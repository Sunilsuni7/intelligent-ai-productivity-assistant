import webbrowser
import urllib.parse
import subprocess
from app.web_tools.url_validator import validate_url

def open_website(url: str) -> str:
    """Opens a website in the default browser."""
    if not url.startswith('http://') and not url.startswith('https://'):
        # If they provided a raw domain like google.com
        if '://' not in url:
            url = 'https://' + url
    
    if not validate_url(url):
        return f"Error: Invalid or unsafe URL: {url}"
    try:
        success = webbrowser.open(url)
        if success:
            return f"Opened website: {url}"
        return f"Unable to open website: {url}"
    except Exception as e:
        return f"Failed to open website: {e}"

def search_google(query: str) -> str:
    """Searches Google for the given query."""
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    try:
        webbrowser.open(url)
        return f"Searched Google for: {query}"
    except Exception as e:
        return f"Failed to search Google: {e}"

def search_youtube(query: str) -> str:
    """Searches YouTube for the given query."""
    encoded = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    try:
        webbrowser.open(url)
        return f"Searched YouTube for: {query}"
    except Exception as e:
        return f"Failed to search YouTube: {e}"

def close_browser() -> str:
    """Closes all known browser instances forcefully but safely."""
    browsers = ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe"]
    closed = []
    for browser in browsers:
        try:
            # check if process exists and kill it
            # /F is forceful termination, /IM is image name
            res = subprocess.run(["taskkill", "/IM", browser, "/F"], capture_output=True)
            if res.returncode == 0:
                closed.append(browser)
        except:
            pass
    
    if closed:
        return f"Closed browser(s)."
    return "No browsers were found open or failed to close them."

