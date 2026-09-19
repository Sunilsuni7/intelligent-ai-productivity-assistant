import pyttsx3
import threading

_engine = None
_thread = None

def init_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty('rate', 150)

def speak(text):
    """
    Convert text to speech using a local TTS engine (pyttsx3).
    Runs in a separate thread to avoid blocking the main application.
    """
    if not text:
        return

    def _speak_thread(text_to_speak):
        global _engine
        try:
            init_engine()
            _engine.say(text_to_speak)
            _engine.runAndWait()
        except Exception as e:
            print(f"TTS Engine failed: {e}")

    global _thread
    _thread = threading.Thread(target=_speak_thread, args=(text,), daemon=True)
    _thread.start()

def stop_speaking():
    global _engine
    try:
        if _engine:
            _engine.stop()
    except Exception as e:
        print(f"Failed to stop TTS: {e}")
