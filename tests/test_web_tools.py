import pytest
from app.web_tools.url_validator import validate_url, get_official_url
from app.web_tools.web_search import perform_web_search, WebSearchRequest
from app.web_tools.browser_tools import open_website, search_google, search_youtube
from unittest.mock import patch

def test_url_validation():
    assert validate_url("http://google.com") is True
    assert validate_url("file:///etc/passwd") is False

def test_official_allowlist():
    assert get_official_url("python") == "https://www.python.org/"

def test_web_search_fallback():
    req = WebSearchRequest(query="FastAPI")
    resp = perform_web_search(req)
    assert resp.success is False

@patch("webbrowser.open")
def test_open_website(mock_open):
    mock_open.return_value = True
    res = open_website("https://github.com")
    assert "Opened" in res
    mock_open.assert_called_with("https://github.com")

@patch("webbrowser.open")
def test_search_google(mock_open):
    mock_open.return_value = True
    res = search_google("Python")
    assert "Searched Google" in res
    mock_open.assert_called_once()
