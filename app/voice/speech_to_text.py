import speech_recognition as sr

def listen_and_recognize():
    """
    Listen to the microphone and convert speech to text.
    Returns:
        tuple: (success (bool), transcript/error_message (str))
    """
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            # Listen with a timeout to avoid hanging forever
            audio = r.listen(source, timeout=5, phrase_time_limit=10)

        transcript = r.recognize_google(audio)
        if not transcript:
            return False, "Empty speech detected."
        return True, transcript
    except sr.WaitTimeoutError:
        return False, "Speech timeout: No speech detected."
    except sr.UnknownValueError:
        return False, "Speech recognition failure: Could not understand audio."
    except sr.RequestError as e:
        return False, f"Speech recognition service unavailable: {e}"
    except Exception as e:
        return False, f"Microphone unavailable or error: {str(e)}"
