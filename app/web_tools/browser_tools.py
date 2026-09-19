import webbrowser
from app.web_tools.url_validator import validate_url

def open_website_in_browser(url: str) -> str:
    """
    Validates and opens the website in the local browser.
    Should be called after user confirmation.
    """
    if not validate_url(url):
        return f"Error: Invalid or unsafe URL: {url}"

    try:
        success = webbrowser.open(url)
        if success:
            return f"Browser action prepared and website opened: {url}"
        else:
            return f"Unable to open the browser action for: {url}"
    except Exception as e:
        return f"Unable to open the browser action. Error: {e}"
