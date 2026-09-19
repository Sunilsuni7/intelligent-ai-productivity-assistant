import pytest
from unittest.mock import patch, MagicMock
from app.voice.speech_to_text import listen_and_recognize
from app.voice.text_to_speech import speak, stop_speaking, init_engine
import speech_recognition as sr

def test_speech_to_text_success():
    with patch("speech_recognition.Recognizer.listen") as mock_listen, \
         patch("speech_recognition.Recognizer.recognize_google") as mock_recognize, \
         patch("speech_recognition.Microphone") as mock_mic:
        mock_mic.return_value.__enter__.return_value = MagicMock()
        mock_listen.return_value = MagicMock()
        mock_recognize.return_value = "Hello assistant"

        success, text = listen_and_recognize()
        assert success is True
        assert text == "Hello assistant"

def test_speech_to_text_empty():
    with patch("speech_recognition.Recognizer.listen") as mock_listen, \
         patch("speech_recognition.Recognizer.recognize_google") as mock_recognize, \
         patch("speech_recognition.Microphone") as mock_mic:
        mock_mic.return_value.__enter__.return_value = MagicMock()
        mock_listen.return_value = MagicMock()
        mock_recognize.return_value = ""

        success, text = listen_and_recognize()
        assert success is False
        assert "Empty speech" in text

def test_speech_to_text_timeout():
    with patch("speech_recognition.Recognizer.listen") as mock_listen, \
         patch("speech_recognition.Microphone") as mock_mic:
        mock_mic.return_value.__enter__.return_value = MagicMock()
        mock_listen.side_effect = sr.WaitTimeoutError()

        success, text = listen_and_recognize()
        assert success is False
        assert "timeout" in text.lower()

def test_speech_to_text_failure():
    with patch("speech_recognition.Recognizer.listen") as mock_listen, \
         patch("speech_recognition.Microphone") as mock_mic:
        mock_mic.return_value.__enter__.return_value = MagicMock()
        mock_listen.side_effect = sr.UnknownValueError()

        success, text = listen_and_recognize()
        assert success is False
        assert "failure" in text.lower()


@patch("pyttsx3.init")
def test_text_to_speech_init(mock_init):
    # Just verify that speak doesn't crash
    mock_engine = MagicMock()
    mock_init.return_value = mock_engine

    # We call speak, it spawns a thread. We don't really wait for the thread here,
    # but we can call init_engine directly to test pyttsx3 init handling.
    init_engine()
    assert mock_init.called

def test_text_to_speech_empty():
    # Should return early
    speak("")

@patch("app.voice.text_to_speech._engine")
def test_stop_speaking(mock_engine):
    stop_speaking()
    mock_engine.stop.assert_called_once()
