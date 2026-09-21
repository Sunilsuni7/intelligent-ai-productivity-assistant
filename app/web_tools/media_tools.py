import ctypes
import webbrowser
import urllib.parse
from app.web_tools.browser_tools import search_youtube

# Virtual Key Codes for Media and Volume Controls
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

def _press_key(vk_code):
    try:
        # press down
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        # release
        ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
        return True
    except Exception:
        return False

def play_media(query: str = None) -> str:
    """Plays media. If query is provided, opens YouTube search for it. Otherwise toggles play."""
    if query and query.strip():
        # Play specific media via YouTube
        return search_youtube(query)
    else:
        # Just hit play
        res = _press_key(VK_MEDIA_PLAY_PAUSE)
        return "Played media." if res else "Failed to send play media key."

def pause_media() -> str:
    res = _press_key(VK_MEDIA_PLAY_PAUSE)
    return "Paused media." if res else "Failed to send pause media key."

def resume_media() -> str:
    res = _press_key(VK_MEDIA_PLAY_PAUSE)
    return "Resumed media." if res else "Failed to send resume media key."

def stop_media() -> str:
    res = _press_key(VK_MEDIA_STOP)
    return "Stopped media." if res else "Failed to send stop media key."

def volume_up() -> str:
    # hit volume up a few times to make a noticeable difference
    for _ in range(5):
        _press_key(VK_VOLUME_UP)
    return "Increased volume."

def volume_down() -> str:
    for _ in range(5):
        _press_key(VK_VOLUME_DOWN)
    return "Decreased volume."

def mute() -> str:
    res = _press_key(VK_VOLUME_MUTE)
    return "Muted volume." if res else "Failed to send mute key."
