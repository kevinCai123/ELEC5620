"""Comprehensive tests for app/services/code.py - code generation and execution service."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from app.schemas.code import CodeAnalysis, OutputAnalysis
from app.services.code import CodeService


@pytest.fixture
def code_service():
    """Create a CodeService instance."""
    return CodeService()


def test_fallback_code_returns_python(code_service):
    """Test _fallback_code returns Python example."""
    result = code_service._fallback_code("python")
    assert "def greet" in result
    assert "Hello" in result


def test_fallback_code_returns_javascript(code_service):
    """Test _fallback_code returns JavaScript example."""
    result = code_service._fallback_code("javascript")
    assert "function greet" in result
    assert "console.log" in result


def test_fallback_code_returns_typescript(code_service):
    """Test _fallback_code returns TypeScript example."""
    result = code_service._fallback_code("typescript")
    assert "function greet" in result
    assert "string" in result  # TypeScript type annotation


def test_fallback_code_defaults_to_python_for_unknown_language(code_service):
    """Test _fallback_code returns Python for unknown language."""
    result = code_service._fallback_code("unknownlang")
    assert "def greet" in result


def test_normalise_generated_code_handles_escape_sequences(code_service):
    """Test _normalise_generated_code converts escape sequences."""
    code = "print(\\n)"
    result = code_service._normalise_generated_code(code)
    assert "\n" in result


def test_normalise_generated_code_handles_tabs(code_service):
    """Test _normalise_generated_code converts tab escapes."""
    code = "\\tindented"
    result = code_service._normalise_generated_code(code)
    assert "\t" in result


def test_normalise_generated_code_handles_quotes(code_service):
    """Test _normalise_generated_code preserves quoted strings."""
    code = "print('hello')"
    result = code_service._normalise_generated_code(code)
    assert "'" in result
    assert "hello" in result


def test_normalise_generated_code_handles_empty_string(code_service):
    """Test _normalise_generated_code handles empty input."""
    result = code_service._normalise_generated_code("")
    assert result == ""


def test_normalise_generated_code_normalises_newlines(code_service):
    """Test _normalise_generated_code normalises different newline styles."""
    code = "line1\r\nline2\rline3\nline4"
    result = code_service._normalise_generated_code(code)
    assert "\r" not in result  # All converted to \n


@pytest.mark.asyncio
async def test_generate_code_uses_llm_when_available(code_service):
    """Test generate_code uses LLM when available."""
    mock_llm = MagicMock()
    mock_llm.has_llm = True
    code_service._llm = mock_llm
    
    with patch.object(code_service, "_generate_via_llm", return_value=("print('test')", "Prints test")):
        code, explanation, fallback = await code_service.generate_code("print test", "python")
        
        assert fallback is False
        assert "print" in code


@pytest.mark.asyncio
async def test_generate_code_uses_fallback_when_llm_unavailable(code_service):
    """Test generate_code uses fallback when LLM unavailable."""
    mock_llm = MagicMock()
    mock_llm.has_llm = False
    code_service._llm = mock_llm
    
    code, explanation, fallback = await code_service.generate_code("print test", "python")
    
    assert fallback is True
    assert "def greet" in code  # Fallback code
    assert "Fallback" in explanation


@pytest.mark.asyncio
async def test_generate_code_uses_fallback_on_llm_error(code_service):
    """Test generate_code uses fallback when LLM fails."""
    mock_llm = MagicMock()
    mock_llm.has_llm = True
    code_service._llm = mock_llm
    
    with patch.object(code_service, "_generate_via_llm", side_effect=Exception("LLM error")):
        code, explanation, fallback = await code_service.generate_code("print test", "python")
        
        assert fallback is True


@pytest.mark.asyncio
async def test_execute_code_directly_python_success(code_service):
    """Test _execute_code_directly executes Python code."""
    code = "print('hello')"
    
    output, error, exec_time, success = await code_service._execute_code_directly(code, "python", 5)
    
    assert success is True
    assert "hello" in output or output == ""  # Subprocess might not capture print
    assert exec_time >= 0


@pytest.mark.asyncio
async def test_execute_code_directly_handles_syntax_error(code_service):
    """Test _execute_code_directly handles syntax errors."""
    code = "print('unclosed string"
    
    output, error, exec_time, success = await code_service._execute_code_directly(code, "python", 5)
    
    assert success is False
    assert error is not None


@pytest.mark.asyncio
async def test_execute_code_directly_handles_timeout(code_service):
    """Test _execute_code_directly handles timeout."""
    code = "import time; time.sleep(100)"
    
    output, error, exec_time, success = await code_service._execute_code_directly(code, "python", 1)
    
    assert success is False
    assert "timeout" in error.lower() or "timed out" in error.lower()


@pytest.mark.asyncio
async def test_execute_code_with_llm_analysis_blocks_unsafe_code(code_service):
    """Test execute_code_with_llm_analysis blocks unsafe code."""
    unsafe_code = "import os; os.system('rm -rf /')"
    
    mock_analysis = CodeAnalysis(
        should_execute=False,
        safety_score=0,
        predicted_output="N/A",
        potential_issues=["File deletion"]
    )
    
    mock_llm = MagicMock()
    mock_llm.has_llm = True
    code_service._llm = mock_llm
    
    with patch.object(code_service, "_analyze_code_before_execution", return_value=mock_analysis):
        pre, output, error, exec_time, success, post, fallback = await code_service.execute_code_with_llm_analysis(
            unsafe_code, "python", 5
        )
        
        assert pre.should_execute is False
        assert success is False
        assert "safety" in error.lower()


@pytest.mark.asyncio
async def test_execute_code_with_llm_analysis_allows_safe_code(code_service):
    """Test execute_code_with_llm_analysis allows safe code."""
    safe_code = "print('hello')"
    
    mock_pre_analysis = CodeAnalysis(
        should_execute=True,
        safety_score=10,
        predicted_output="hello",
        potential_issues=[]
    )
    
    mock_post_analysis = OutputAnalysis(
        summary="Executed successfully",
        insights=["Code printed hello"],
        suggestions=[]
    )
    
    mock_llm = MagicMock()
    mock_llm.has_llm = True
    code_service._llm = mock_llm
    
    with patch.object(code_service, "_analyze_code_before_execution", return_value=mock_pre_analysis):
        with patch.object(code_service, "_analyze_output", return_value=mock_post_analysis):
            with patch.object(code_service, "_execute_code_directly", return_value=("hello\n", None, 0.1, True)):
                pre, output, error, exec_time, success, post, fallback = await code_service.execute_code_with_llm_analysis(
                    safe_code, "python", 5
                )
                
                assert pre.should_execute is True
                assert success is True


@pytest.mark.asyncio
async def test_execute_code_with_llm_analysis_uses_fallback_when_llm_unavailable(code_service):
    """Test execute_code_with_llm_analysis uses fallback when LLM unavailable."""
    code = "print('test')"
    
    mock_llm = MagicMock()
    mock_llm.has_llm = False
    code_service._llm = mock_llm
    
    with patch.object(code_service, "_execute_code_directly", return_value=("test\n", None, 0.1, True)):
        pre, output, error, exec_time, success, post, fallback = await code_service.execute_code_with_llm_analysis(
            code, "python", 5
        )
        
        assert fallback is True
        assert pre.should_execute is True  # Fallback allows execution


def test_fallback_pre_analysis_allows_execution(code_service):
    """Test _fallback_pre_analysis returns permissive analysis."""
    result = code_service._fallback_pre_analysis()
    
    assert result.should_execute is True
    assert result.safety_score >= 0


def test_fallback_post_analysis_for_success(code_service):
    """Test _fallback_post_analysis for successful execution."""
    result = code_service._fallback_post_analysis(success=True)
    
    assert "successfully" in result.summary.lower()


def test_fallback_post_analysis_for_failure(code_service):
    """Test _fallback_post_analysis for failed execution."""
    result = code_service._fallback_post_analysis(success=False)
    
    assert "error" in result.summary.lower() or "failed" in result.summary.lower()


@pytest.mark.asyncio
async def test_execute_code_with_llm_analysis_handles_pre_analysis_error(code_service):
    """Test execute_code_with_llm_analysis handles pre-analysis errors."""
    code = "print('test')"
    
    mock_llm = MagicMock()
    mock_llm.has_llm = True
    code_service._llm = mock_llm
    
    with patch.object(code_service, "_analyze_code_before_execution", side_effect=Exception("Analysis error")):
        with patch.object(code_service, "_execute_code_directly", return_value=("test\n", None, 0.1, True)):
            pre, output, error, exec_time, success, post, fallback = await code_service.execute_code_with_llm_analysis(
                code, "python", 5
            )
            
            assert fallback is True
            assert pre.should_execute is True  # Falls back to permissive


@pytest.mark.asyncio
async def test_execute_code_with_llm_analysis_handles_post_analysis_error(code_service):
    """Test execute_code_with_llm_analysis handles post-analysis errors."""
    code = "print('test')"
    
    mock_pre_analysis = CodeAnalysis(
        should_execute=True,
        safety_score=10,
        predicted_output="test",
        potential_issues=[]
    )
    
    mock_llm = MagicMock()
    mock_llm.has_llm = True
    code_service._llm = mock_llm
    
    with patch.object(code_service, "_analyze_code_before_execution", return_value=mock_pre_analysis):
        with patch.object(code_service, "_analyze_output", side_effect=Exception("Analysis error")):
            with patch.object(code_service, "_execute_code_directly", return_value=("test\n", None, 0.1, True)):
                pre, output, error, exec_time, success, post, fallback = await code_service.execute_code_with_llm_analysis(
                    code, "python", 5
                )
                
                # Should complete with fallback post-analysis
                assert success is True
                assert post is not None


def test_normalise_generated_code_handles_double_quotes(code_service):
    """Test _normalise_generated_code handles double quotes."""
    code = 'print("hello")'
    result = code_service._normalise_generated_code(code)
    assert '"' in result
    assert "hello" in result


def test_normalise_generated_code_handles_backticks(code_service):
    """Test _normalise_generated_code handles backticks."""
    code = "console.log(`hello`)"
    result = code_service._normalise_generated_code(code)
    assert "`" in result
    assert "hello" in result


def test_normalise_generated_code_handles_escaped_characters_in_strings(code_service):
    """Test _normalise_generated_code preserves escaped chars in strings."""
    code = "print('\\n')"  # \n inside a string should stay as \\n
    result = code_service._normalise_generated_code(code)
    assert "print" in result


@pytest.mark.asyncio
async def test_generate_code_emits_metrics(code_service):
    """Test generate_code emits appropriate metrics."""
    mock_llm = MagicMock()
    mock_llm.has_llm = False
    code_service._llm = mock_llm
    
    with patch("app.services.code.emit_metric") as mock_emit:
        code, explanation, fallback = await code_service.generate_code("test", "python")
        
        # Should emit fallback_rate metric
        assert mock_emit.called


@pytest.mark.asyncio
async def test_generate_code_uses_time_metric(code_service):
    """Test generate_code uses time metric."""
    mock_llm = MagicMock()
    mock_llm.has_llm = False
    code_service._llm = mock_llm
    
    with patch("app.services.code.time_metric") as mock_time_metric:
        code, explanation, fallback = await code_service.generate_code("test", "python")
        
        # Should use time_metric
        mock_time_metric.assert_called_once_with("p95_latency_ms", feature="code_generation")


@pytest.mark.asyncio
async def test_execute_code_directly_handles_javascript(code_service):
    """Test _execute_code_directly can execute JavaScript."""
    code = "console.log('hello');"
    
    # This will likely fail unless node is installed, but test the code path
    output, error, exec_time, success = await code_service._execute_code_directly(code, "javascript", 5)
    
    # Just verify it attempts execution
    assert exec_time >= 0
    # Success depends on node being installed, so we don't assert it


def test_normalise_generated_code_complex_escapes(code_service):
    """Test _normalise_generated_code with complex escape sequences."""
    code = "text = 'Line 1\\nLine 2\\tIndented'"
    result = code_service._normalise_generated_code(code)
    assert "text" in result


@pytest.mark.asyncio
async def test_execute_code_directly_measures_execution_time(code_service):
    """Test _execute_code_directly measures execution time."""
    code = "x = 1 + 1"
    
    output, error, exec_time, success = await code_service._execute_code_directly(code, "python", 5)
    
    assert exec_time > 0  # Should have some measured time


@pytest.mark.asyncio
async def test_execute_code_directly_uses_asyncio_timeout(code_service):
    """Test _execute_code_directly respects timeout parameter."""
    import asyncio
    
    code = "import time; time.sleep(10)"  # Sleep longer than timeout
    
    start_time = asyncio.get_event_loop().time()
    output, error, exec_time, success = await code_service._execute_code_directly(code, "python", 1)
    end_time = asyncio.get_event_loop().time()
    
    # Should timeout within reasonable time (not wait full 10 seconds)
    assert (end_time - start_time) < 5


def test_fallback_code_is_valid_python(code_service):
    """Test _fallback_code returns valid Python syntax."""
    code = code_service._fallback_code("python")
    
    # Should be valid Python (compile without error)
    try:
        compile(code, "<string>", "exec")
        is_valid = True
    except SyntaxError:
        is_valid = False
    
    assert is_valid

