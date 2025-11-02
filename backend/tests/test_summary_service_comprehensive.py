"""Comprehensive tests for app/services/summary.py - content summarization service."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import HttpUrl

from app.services.summary import MAX_CHARS, SummaryService


@pytest.fixture
def summary_service():
    """Create a SummaryService instance."""
    return SummaryService()


@pytest.mark.asyncio
async def test_summarize_requires_text_or_url():
    """Test that summarize raises ValueError when neither text nor URL provided."""
    service = SummaryService()
    
    with pytest.raises(ValueError, match="Either text or url must be provided"):
        await service.summarize(text=None, url=None)


@pytest.mark.asyncio
async def test_summarize_with_text():
    """Test summarizing with direct text input."""
    service = SummaryService()
    
    mock_summary = MagicMock()
    mock_result = MagicMock()
    mock_result.data = mock_summary
    mock_result.fallback_used = False
    
    with patch.object(service, "_summarize_cached", return_value=(mock_summary, False)):
        summary, fallback, truncated = await service.summarize(text="Test content")
        
        assert summary == mock_summary
        assert fallback is False
        assert truncated is False


@pytest.mark.asyncio
async def test_summarize_with_url():
    """Test summarizing with URL input."""
    service = SummaryService()
    
    mock_summary = MagicMock()
    
    with patch.object(service, "_fetch_url", return_value="Fetched content"):
        with patch.object(service, "_summarize_cached", return_value=(mock_summary, False)):
            summary, fallback, truncated = await service.summarize(url="https://example.com")
            
            assert summary == mock_summary


@pytest.mark.asyncio
async def test_summarize_truncates_long_text():
    """Test that long text is truncated to MAX_CHARS."""
    service = SummaryService()
    
    long_text = "x" * (MAX_CHARS + 1000)
    mock_summary = MagicMock()
    
    with patch.object(service, "_summarize_cached", return_value=(mock_summary, False)):
        summary, fallback, truncated = await service.summarize(text=long_text)
        
        assert truncated is True


@pytest.mark.asyncio
async def test_summarize_handles_llm_failure():
    """Test that summarize falls back when LLM fails."""
    service = SummaryService()
    
    fallback_summary = MagicMock()
    
    with patch.object(service, "_summarize_cached", side_effect=Exception("LLM error")):
        with patch.object(service._llm, "_fallback_summary", return_value=fallback_summary):
            summary, fallback, truncated = await service.summarize(text="Test")
            
            assert summary == fallback_summary
            assert fallback is True


@pytest.mark.asyncio
async def test_fetch_url_success():
    """Test fetching content from URL."""
    service = SummaryService()
    
    mock_response = MagicMock()
    mock_response.text = "Page content"
    mock_response.raise_for_status = MagicMock()
    
    with patch("app.services.summary.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client
        
        content = await service._fetch_url("https://example.com")
        
        assert content == "Page content"


@pytest.mark.asyncio
async def test_fetch_url_with_httpurl():
    """Test fetching content with HttpUrl type."""
    service = SummaryService()
    
    mock_response = MagicMock()
    mock_response.text = "Page content"
    mock_response.raise_for_status = MagicMock()
    
    with patch("app.services.summary.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        MockClient.return_value.__aenter__.return_value = mock_client
        
        http_url = HttpUrl("https://example.com")
        content = await service._fetch_url(http_url)
        
        assert content == "Page content"


def test_normalise_source_plain_text():
    """Test normalizing plain text (no HTML)."""
    service = SummaryService()
    
    result = service._normalise_source("Plain text content")
    
    assert result == "Plain text content"


def test_normalise_source_removes_html_tags():
    """Test that HTML tags are removed."""
    service = SummaryService()
    
    html = "<p>This is <strong>bold</strong> text</p>"
    result = service._normalise_source(html)
    
    assert "strong" not in result
    assert "This is bold text" in result


def test_normalise_source_extracts_main_content():
    """Test that content from <main> tag is extracted."""
    service = SummaryService()
    
    html = "<header>Header</header><main>Main content here</main><footer>Footer</footer>"
    result = service._normalise_source(html)
    
    assert "Main content here" in result
    # Header and footer should ideally not be in result (extracted from main)


def test_normalise_source_removes_scripts():
    """Test that script tags are removed."""
    service = SummaryService()
    
    html = "<p>Content</p><script>alert('test')</script>"
    result = service._normalise_source(html)
    
    assert "alert" not in result
    assert "script" not in result


def test_normalise_source_removes_styles():
    """Test that style tags are removed."""
    service = SummaryService()
    
    html = "<style>body { color: red; }</style><p>Content</p>"
    result = service._normalise_source(html)
    
    assert "color" not in result
    assert "style" not in result


def test_normalise_source_removes_comments():
    """Test that HTML comments are removed."""
    service = SummaryService()
    
    html = "<!-- This is a comment --><p>Content</p>"
    result = service._normalise_source(html)
    
    assert "comment" not in result.lower()


def test_normalise_source_unescapes_html_entities():
    """Test that HTML entities are unescaped."""
    service = SummaryService()
    
    html = "&lt;div&gt;Content&lt;/div&gt;"
    result = service._normalise_source(html)
    
    # After unescaping and removing tags, should just have "Content"
    assert "Content" in result


def test_normalise_source_normalizes_whitespace():
    """Test that whitespace is normalized."""
    service = SummaryService()
    
    html = "<p>Content   with\n\n\nmultiple\t\tspaces</p>"
    result = service._normalise_source(html)
    
    # After normalization, excessive whitespace should be reduced
    assert "Content" in result
    assert "with" in result
    assert "multiple" in result
    assert "spaces" in result


def test_normalise_source_strips_result():
    """Test that result is stripped of leading/trailing whitespace."""
    service = SummaryService()
    
    html = "  <p>Content</p>  "
    result = service._normalise_source(html)
    
    assert not result.startswith(" ")
    assert not result.endswith(" ")


def test_normalise_source_returns_original_if_empty():
    """Test that original source is returned if normalization results in empty string."""
    service = SummaryService()
    
    html = "<script></script><style></style>"
    result = service._normalise_source(html)
    
    # Should return original (stripped) if normalized is empty
    assert result == html.strip()


@pytest.mark.asyncio
async def test_summarize_uses_user_request():
    """Test that summarize passes user_request to LLM."""
    service = SummaryService()
    
    mock_summary = MagicMock()
    
    with patch.object(service._llm, "summarize", return_value=MagicMock(data=mock_summary, fallback_used=False)) as mock_llm:
        await service.summarize(text="Test", user_request="Focus on main points")
        
        # Verify user_request was passed
        call_args = mock_llm.call_args
        assert call_args is not None


@pytest.mark.asyncio
async def test_summarize_defaults_user_request_to_auto():
    """Test that user_request defaults to 'auto' when not provided."""
    service = SummaryService()
    
    mock_summary = MagicMock()
    
    with patch.object(service._llm, "summarize", return_value=MagicMock(data=mock_summary, fallback_used=False)):
        await service.summarize(text="Test")
        
        # Should use "auto" as default


@pytest.mark.asyncio
async def test_summarize_emits_metrics():
    """Test that summarize emits appropriate metrics."""
    service = SummaryService()
    
    mock_summary = MagicMock()
    
    with patch.object(service, "_summarize_cached", return_value=(mock_summary, False)):
        with patch("app.services.summary.emit_metric") as mock_emit:
            await service.summarize(text="Test")
            
            # Should emit fallback_rate and schema_valid_rate
            assert mock_emit.call_count >= 2


@pytest.mark.asyncio
async def test_summarize_emits_fallback_metric_on_error():
    """Test that summarize emits fallback metric when LLM fails."""
    service = SummaryService()
    
    fallback_summary = MagicMock()
    
    with patch.object(service, "_summarize_cached", side_effect=Exception("Error")):
        with patch.object(service._llm, "_fallback_summary", return_value=fallback_summary):
            with patch("app.services.summary.emit_metric") as mock_emit:
                await service.summarize(text="Test")
                
                # Should emit fallback_rate = 1.0
                calls = [call for call in mock_emit.call_args_list if call[0][0] == "fallback_rate"]
                assert any(call[0][1] == 1.0 for call in calls)


@pytest.mark.asyncio
async def test_summarize_cached_uses_time_metric():
    """Test that _summarize_cached uses time metric."""
    service = SummaryService()
    
    mock_summary = MagicMock()
    
    with patch.object(service._llm, "summarize", return_value=MagicMock(data=mock_summary, fallback_used=False)):
        with patch("app.services.summary.time_metric") as mock_time_metric:
            await service._summarize_cached("Test", "auto")
            
            # Should use time_metric context manager
            mock_time_metric.assert_called_once_with("p95_latency_ms", feature="summary")


@pytest.mark.asyncio
async def test_summarize_handles_none_url_fetch():
    """Test that summarize raises error when URL fetch returns None."""
    service = SummaryService()
    
    with patch.object(service, "_fetch_url", return_value=None):
        with pytest.raises(ValueError, match="Unable to obtain source material"):
            await service.summarize(url="https://example.com")

