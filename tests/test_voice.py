import speech_recognition as sr
from unittest.mock import MagicMock, patch

from app.voice.speech_to_text import listen_and_recognize


def create_mock_audio_source():
    source = MagicMock(spec=sr.AudioSource)
    source.stream = MagicMock()
    source.CHUNK = 1024
    source.SAMPLE_RATE = 16000
    source.SAMPLE_WIDTH = 2
    return source


def test_speech_to_text_success():
    with patch("speech_recognition.Recognizer.adjust_for_ambient_noise"), \
         patch("speech_recognition.Recognizer.listen") as mock_listen, \
         patch("speech_recognition.Recognizer.recognize_google") as mock_recognize, \
         patch("speech_recognition.Microphone") as mock_mic:

        source = create_mock_audio_source()
        mock_mic.return_value.__enter__.return_value = source

        mock_listen.return_value = MagicMock()
        mock_recognize.return_value = "hello world"

        success, text = listen_and_recognize()

        assert success is True
        assert text == "hello world"


def test_speech_to_text_empty():
    with patch("speech_recognition.Recognizer.adjust_for_ambient_noise"), \
         patch("speech_recognition.Recognizer.listen") as mock_listen, \
         patch("speech_recognition.Recognizer.recognize_google") as mock_recognize, \
         patch("speech_recognition.Microphone") as mock_mic:

        source = create_mock_audio_source()
        mock_mic.return_value.__enter__.return_value = source

        mock_listen.return_value = MagicMock()
        mock_recognize.return_value = ""

        success, text = listen_and_recognize()

        assert success is False
        assert "Empty speech" in text


def test_speech_to_text_timeout():
    with patch("speech_recognition.Recognizer.adjust_for_ambient_noise"), \
         patch("speech_recognition.Recognizer.listen") as mock_listen, \
         patch("speech_recognition.Microphone") as mock_mic:

        source = create_mock_audio_source()
        mock_mic.return_value.__enter__.return_value = source

        mock_listen.side_effect = sr.WaitTimeoutError()

        success, text = listen_and_recognize()

        assert success is False
        assert "timeout" in text.lower()


def test_speech_to_text_failure():
    with patch("speech_recognition.Recognizer.adjust_for_ambient_noise"), \
         patch("speech_recognition.Recognizer.listen") as mock_listen, \
         patch("speech_recognition.Microphone") as mock_mic:

        source = create_mock_audio_source()
        mock_mic.return_value.__enter__.return_value = source

        mock_listen.side_effect = sr.UnknownValueError()

        success, text = listen_and_recognize()

        assert success is False
        assert "failure" in text.lower()