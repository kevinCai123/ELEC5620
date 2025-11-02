from __future__ import annotations

import asyncio
import logging
import subprocess
import time

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.schemas.code import CodeAnalysis, OutputAnalysis
from app.services.llm import LLMService
from app.utils.metrics import emit_metric, time_metric

logger = logging.getLogger(__name__)


class GeneratedCode(BaseModel):
    code: str = Field(description="The generated code")
    explanation: str = Field(description="Brief explanation of what the code does")


class CodeService:
    def __init__(self) -> None:
        self._llm = LLMService()

    async def generate_code(self, prompt: str, language: str = "python") -> tuple[str, str, bool]:
        """
        Generate code from natural language prompt using LLM.
        Returns: (code, explanation, fallback_used)
        """
        with time_metric("p95_latency_ms", feature="code_generation"):
            if self._llm.has_llm:
                try:
                    code, explanation = await self._generate_via_llm(prompt, language)
                    emit_metric("fallback_rate", 0.0, feature="code_generation")
                    return code, explanation, False
                except Exception as exc:
                    logger.warning("LLM code generation failed: %s", exc)

        # Fallback
        emit_metric("fallback_rate", 1.0, feature="code_generation")
        return self._fallback_code(language), "Fallback example code (LLM unavailable)", True

    async def _generate_via_llm(self, prompt: str, language: str) -> tuple[str, str]:
        """Use LLM to generate code"""
        parser = PydanticOutputParser(pydantic_object=GeneratedCode)
        format_instructions = parser.get_format_instructions()

        system_prompt = f"""You are an expert {language} programmer. Generate clean, working code based on the user's request.
        
Rules:
- Write production-quality code with proper error handling
- Include helpful comments
- Follow best practices for {language}
- Keep code concise but complete
- Provide a brief explanation of what the code does

Return your response in this format:
{{format_instructions}}"""

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{prompt}")
        ])

        llm = self._llm._llm.bind(temperature=0.3)  # type: ignore[attr-defined]
        chain = prompt_template | llm | parser
        
        result = await chain.ainvoke({
            "prompt": prompt,
            "format_instructions": format_instructions
        })
        
        generated: GeneratedCode = result  # type: ignore[assignment]
        normalised_code = self._normalise_generated_code(generated.code)
        return normalised_code, generated.explanation

    def _fallback_code(self, language: str) -> str:
        """Provide fallback example code"""
        fallbacks = {
            "python": """# Hello World Example
def greet(name):
    \"\"\"Greet a person by name\"\"\"
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
""",
            "javascript": """// Hello World Example
function greet(name) {
    return `Hello, ${name}!`;
}

console.log(greet("World"));
""",
            "typescript": """// Hello World Example
function greet(name: string): string {
    return `Hello, ${name}!`;
}

console.log(greet("World"));
""",
        }
        return fallbacks.get(language.lower(), fallbacks["python"])

    def _normalise_generated_code(self, code: str) -> str:
        """Best-effort normalisation so returned code preserves original structure."""
        if not code:
            return code

        # Normalise native newline conventions first.
        code = code.replace("\r\n", "\n").replace("\r", "\n")

        result: list[str] = []
        in_single = False
        in_double = False
        in_backtick = False
        escape_active = False
        i = 0
        length = len(code)

        while i < length:
            char = code[i]

            if char == "\\" and i + 1 < length:
                next_char = code[i + 1]
                if next_char == "n" and not (in_single or in_double or in_backtick):
                    result.append("\n")
                    i += 2
                    escape_active = False
                    continue
                if next_char == "t" and not (in_single or in_double or in_backtick):
                    result.append("\t")
                    i += 2
                    escape_active = False
                    continue

            if char in {"'", '"', "`"} and not escape_active:
                if char == "'" and not (in_double or in_backtick):
                    in_single = not in_single
                elif char == '"' and not (in_single or in_backtick):
                    in_double = not in_double
                elif char == "`" and not (in_single or in_double):
                    in_backtick = not in_backtick

            escape_active = char == "\\" and not escape_active
            if char != "\\":
                escape_active = False

            result.append(char)
            i += 1

        return "".join(result)

    async def execute_code_with_llm_analysis(
        self, code: str, language: str = "python", timeout: int = 5
    ) -> tuple[CodeAnalysis, str, str | None, float, bool, OutputAnalysis, bool]:
        """
        LLM-powered code execution with pre and post analysis.
        Returns: (pre_analysis, output, error, execution_time, success, post_analysis, fallback_used)
        """
        fallback_used = False
        
        # Step 1: Pre-execution analysis by LLM
        if self._llm.has_llm:
            try:
                pre_analysis = await self._analyze_code_before_execution(code, language)
            except Exception as exc:
                logger.warning("LLM pre-analysis failed: %s", exc)
                pre_analysis = self._fallback_pre_analysis()
                fallback_used = True
        else:
            pre_analysis = self._fallback_pre_analysis()
            fallback_used = True
        
        # Step 2: Execute code (only if LLM says it's safe)
        if pre_analysis.should_execute:
            output, error, execution_time, success = await self._execute_code_directly(
                code, language, timeout
            )
        else:
            output = ""
            error = "Execution blocked due to safety concerns"
            execution_time = 0.0
            success = False
        
        # Step 3: Post-execution analysis by LLM
        if self._llm.has_llm and not fallback_used:
            try:
                post_analysis = await self._analyze_output(
                    code, language, output, error, success
                )
            except Exception as exc:
                logger.warning("LLM post-analysis failed: %s", exc)
                post_analysis = self._fallback_post_analysis(success)
        else:
            post_analysis = self._fallback_post_analysis(success)
        
        return pre_analysis, output, error, execution_time, success, post_analysis, fallback_used

    async def _execute_code_directly(
        self, code: str, language: str = "python", timeout: int = 5
    ) -> tuple[str, str | None, float, bool]:
        """
        Execute code directly (internal method used by LLM-powered execution).
        Returns: (output, error, execution_time, success)
        """
        with time_metric("p95_latency_ms", feature="code_execution"):
            if language.lower() == "python":
                return await self._execute_python(code, timeout)
            elif language.lower() in ("javascript", "js"):
                return await self._execute_javascript(code, timeout)
            else:
                return "", f"Unsupported language: {language}", 0.0, False

    async def _execute_python(self, code: str, timeout: int) -> tuple[str, str | None, float, bool]:
        """Execute Python code safely (cross-platform compatible)"""
        start_time = time.time()
        
        try:
            # Use subprocess.run in thread pool for Windows compatibility
            result = await asyncio.to_thread(
                subprocess.run,
                ["python", "-c", code],
                capture_output=True,
                timeout=timeout,
                text=False  # We'll decode manually
            )
            
            execution_time = time.time() - start_time
            output = result.stdout.decode('utf-8', errors='replace')
            error = result.stderr.decode('utf-8', errors='replace') if result.stderr else None
            success = result.returncode == 0
            
            return output, error if error else None, execution_time, success
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return "", f"Execution timed out after {timeout} seconds", execution_time, False
        except Exception as exc:
            execution_time = time.time() - start_time
            logger.error("Python execution error: %s", exc, exc_info=True)
            return "", f"Execution error: {str(exc)}", execution_time, False

    async def _execute_javascript(self, code: str, timeout: int) -> tuple[str, str | None, float, bool]:
        """Execute JavaScript code using Node.js (cross-platform compatible)"""
        start_time = time.time()
        
        try:
            # Use subprocess.run in thread pool for Windows compatibility
            result = await asyncio.to_thread(
                subprocess.run,
                ["node", "-e", code],
                capture_output=True,
                timeout=timeout,
                text=False  # We'll decode manually
            )
            
            execution_time = time.time() - start_time
            output = result.stdout.decode('utf-8', errors='replace')
            error = result.stderr.decode('utf-8', errors='replace') if result.stderr else None
            success = result.returncode == 0
            
            return output, error if error else None, execution_time, success
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return "", f"Execution timed out after {timeout} seconds", execution_time, False
        except FileNotFoundError:
            execution_time = time.time() - start_time
            return "", "Node.js not found. JavaScript execution requires Node.js to be installed.", execution_time, False
        except Exception as exc:
            execution_time = time.time() - start_time
            logger.error("JavaScript execution error: %s", exc, exc_info=True)
            return "", f"Execution error: {str(exc)}", execution_time, False

    async def _analyze_code_before_execution(self, code: str, language: str) -> CodeAnalysis:
        """Use LLM to analyze code before execution"""
        parser = PydanticOutputParser(pydantic_object=CodeAnalysis)
        format_instructions = parser.get_format_instructions()

        system_prompt = """You are an expert code security analyst and execution predictor.
        
Analyze the provided code and:
1. Assess its safety (rate 0-10, where 0=dangerous, 10=completely safe)
2. Identify potential issues (infinite loops, file system access, network calls, etc.)
3. Predict what the code will output when executed
4. Decide if it should be executed (should_execute: true/false)

Be practical - simple educational code should be marked safe to execute.

Return your analysis in this format:
{format_instructions}"""

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Language: {language}\n\nCode:\n```\n{code}\n```")
        ])

        llm = self._llm._llm.bind(temperature=0.2)  # type: ignore[attr-defined]
        chain = prompt_template | llm | parser
        
        result = await chain.ainvoke({
            "code": code,
            "language": language,
            "format_instructions": format_instructions
        })
        
        return result  # type: ignore[return-value]

    async def _analyze_output(
        self, code: str, language: str, output: str, error: str | None, success: bool
    ) -> OutputAnalysis:
        """Use LLM to analyze execution output"""
        parser = PydanticOutputParser(pydantic_object=OutputAnalysis)
        format_instructions = parser.get_format_instructions()

        system_prompt = """You are an expert code execution analyst.

Analyze the code execution results and provide:
1. A brief summary of what happened
2. Key insights about the execution (performance, behavior, patterns)
3. Suggestions for improvement (optimization, best practices, error handling)

Be helpful and educational.

Return your analysis in this format:
{format_instructions}"""

        execution_details = f"""Language: {language}

Code:
```
{code}
```

Execution Result:
- Success: {success}
- Output: {output or '(no output)'}
- Error: {error or '(no error)'}"""

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{execution_details}")
        ])

        llm = self._llm._llm.bind(temperature=0.3)  # type: ignore[attr-defined]
        chain = prompt_template | llm | parser
        
        result = await chain.ainvoke({
            "execution_details": execution_details,
            "format_instructions": format_instructions
        })
        
        return result  # type: ignore[return-value]

    def _fallback_pre_analysis(self) -> CodeAnalysis:
        """Fallback pre-analysis when LLM is unavailable"""
        return CodeAnalysis(
            safety_score=7,
            potential_issues=["Unable to perform detailed analysis - LLM unavailable"],
            predicted_output="(LLM unavailable - cannot predict output)",
            should_execute=True  # Allow execution by default
        )

    def _fallback_post_analysis(self, success: bool) -> OutputAnalysis:
        """Fallback post-analysis when LLM is unavailable"""
        if success:
            return OutputAnalysis(
                summary="Code executed successfully",
                insights=["LLM analysis unavailable"],
                suggestions=["Enable LLM for detailed analysis and suggestions"]
            )
        else:
            return OutputAnalysis(
                summary="Code execution failed",
                insights=["LLM analysis unavailable"],
                suggestions=["Check the error message for details"]
            )


__all__ = ["CodeService"]

