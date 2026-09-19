import pytest
from app.web_tools.url_validator import validate_url, get_official_url
from app.web_tools.media_tools import construct_youtube_search_url
from app.web_tools.web_search import perform_web_search, WebSearchRequest
from app.web_tools.browser_tools import open_website_in_browser
from unittest.mock import patch

def test_url_validation():
    # Valid
    assert validate_url("http://google.com") is True
    assert validate_url("https://github.com/path?q=1") is True

    # Invalid schemes
    assert validate_url("file:///etc/passwd") is False
    assert validate_url("javascript:alert(1)") is False
    assert validate_url("data:text/html,<html>") is False
    assert validate_url("vbscript:msgbox(1)") is False

    # Malformed
    assert validate_url("") is False

    # Credentials
    assert validate_url("https://user:pass@github.com") is False

def test_official_allowlist():
    assert get_official_url("python") == "https://www.python.org/"
    assert get_official_url("youtube") == "https://www.youtube.com/"
    assert get_official_url("unknown") == ""

def test_media_search_url():
    assert "search_query=python" in construct_youtube_search_url("python")
    assert "search_query=python%2Btutorial" in construct_youtube_search_url("python+tutorial")
    assert construct_youtube_search_url("") == "https://www.youtube.com/"

def test_web_search_fallback():
    req = WebSearchRequest(query="FastAPI")
    resp = perform_web_search(req)
    assert resp.success is False
    assert "duckduckgo.com/?q=FastAPI" in resp.message

def test_web_search_credential_filter():
    req = WebSearchRequest(query="my password is password123")
    resp = perform_web_search(req)
    assert resp.success is False
    assert "credential" in resp.message.lower()

def test_web_search_empty():
    req = WebSearchRequest(query="   ")
    resp = perform_web_search(req)
    assert resp.success is False
    assert "empty query" in resp.message.lower()

@patch("webbrowser.open")
def test_open_website(mock_open):
    mock_open.return_value = True

    # Safe URL
    res = open_website_in_browser("https://github.com")
    assert "opened" in res.lower()
    mock_open.assert_called_with("https://github.com")

    # Unsafe URL
    res = open_website_in_browser("file:///C:/secrets.txt")
    assert "invalid" in res.lower()
    # Ensure it wasn't called on unsafe URL
    assert mock_open.call_count == 1
