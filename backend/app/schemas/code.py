from __future__ import annotations

from pydantic import Field

from app.schemas.common import BaseSchema


class CodeGenerationRequest(BaseSchema):
    prompt: str = Field(min_length=1, max_length=2000, description="User's description of what code to generate")
    language: str = Field(default="python", description="Programming language (python, javascript, etc.)")


class CodeGenerationResponse(BaseSchema):
    code: str = Field(description="Generated code")
    language: str = Field(description="Programming language")
    explanation: str = Field(description="Brief explanation of what the code does")
    fallback_used: bool = Field(default=False, description="Whether LLM fallback was used")


class CodeExecutionRequest(BaseSchema):
    code: str = Field(min_length=1, max_length=10000, description="Code to execute")
    language: str = Field(default="python", description="Programming language")
    timeout: int = Field(default=5, ge=1, le=30, description="Execution timeout in seconds")


class CodeAnalysis(BaseSchema):
    safety_score: int = Field(ge=0, le=10, description="Safety score (0=dangerous, 10=safe)")
    potential_issues: list[str] = Field(description="List of potential issues")
    predicted_output: str = Field(description="What the LLM predicts the code will output")
    should_execute: bool = Field(description="Whether it's safe to execute")


class OutputAnalysis(BaseSchema):
    summary: str = Field(description="Brief summary of what happened")
    insights: list[str] = Field(description="Key insights about the execution")
    suggestions: list[str] = Field(description="Suggestions for improvement")


class CodeExecutionResponse(BaseSchema):
    # Pre-execution analysis
    pre_analysis: CodeAnalysis = Field(description="LLM analysis before execution")
    
    # Execution results
    output: str = Field(description="Execution output (stdout)")
    error: str | None = Field(default=None, description="Error message if execution failed")
    execution_time: float = Field(description="Execution time in seconds")
    success: bool = Field(description="Whether execution completed successfully")
    
    # Post-execution analysis
    post_analysis: OutputAnalysis = Field(description="LLM analysis after execution")
    
    fallback_used: bool = Field(default=False, description="Whether LLM fallback was used")


__all__ = [
    "CodeGenerationRequest",
    "CodeGenerationResponse",
    "CodeExecutionRequest",
    "CodeExecutionResponse",
]

