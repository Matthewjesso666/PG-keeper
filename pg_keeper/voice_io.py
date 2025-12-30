"""Voice I/O utilities using speech_recognition and pyttsx3."""
from __future__ import annotations

from typing import Optional

try:
    import speech_recognition as sr  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    sr = None  # type: ignore

try:
    import pyttsx3  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    pyttsx3 = None  # type: ignore


class VoiceInterface:
    def __init__(self):
        self.recognizer = sr.Recognizer() if sr else None
        self.tts_engine = pyttsx3.init() if pyttsx3 else None

    def listen(self, timeout: float = 10.0) -> Optional[str]:
        if not self.recognizer or not sr:
            raise RuntimeError("speech_recognition is not installed")
        with sr.Microphone() as source:  # pragma: no cover - requires microphone
            audio = self.recognizer.listen(source, timeout=timeout)
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return None

    def speak(self, text: str) -> None:
        if not self.tts_engine:
            raise RuntimeError("pyttsx3 is not installed")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
