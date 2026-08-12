"""Audio I/O - microphone capture and speaker playback with mock fallback."""
from __future__ import annotations

import io
import logging
import wave
from abc import ABC, abstractmethod

from core.config import settings

log = logging.getLogger("vaos.voice.audio")

SAMPLE_RATE = 16000
CHUNK = 1600  # 0.1 s


class AudioInput(ABC):
    @abstractmethod
    def record(self, seconds: float = 3.0) -> bytes:
        """Return 16 kHz mono PCM audio bytes."""


class AudioOutput(ABC):
    @abstractmethod
    def play(self, wav_bytes: bytes) -> None:
        """Play a WAV buffer (16-bit PCM)."""


class MockInput(AudioInput):
    name = "mock"

    def record(self, seconds: float = 3.0) -> bytes:
        import numpy as np

        n = int(SAMPLE_RATE * seconds)
        t = np.linspace(0, seconds, n, endpoint=False)
        tone = 0.3 * np.sin(2 * np.pi * 220 * t)
        return (tone * 32767).astype(np.int16).tobytes()


class MockOutput(AudioOutput):
    name = "mock"

    def play(self, wav_bytes: bytes) -> None:
        with wave.open(io.BytesIO(wav_bytes)) as w:
            frames = w.readframes(w.getnframes())
        log.info("mock-output: played %d ms of audio", int(len(frames) / w.getframerate() * 1000) if frames else 0)


class MicInput(AudioInput):
    name = "mic"

    def record(self, seconds: float = 3.0) -> bytes:
        import numpy as np
        import sounddevice as sd

        frames = sd.rec(int(SAMPLE_RATE * seconds), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
        sd.wait()
        return np.asarray(frames).tobytes()


class SpeakerOutput(AudioOutput):
    name = "speaker"

    def play(self, wav_bytes: bytes) -> None:
        import sounddevice as sd

        with wave.open(io.BytesIO(wav_bytes)) as w:
            frames = w.readframes(w.getnframes())
            sd.play(frames, w.getframerate(), blocking=True)


class AudioIO:
    def __init__(self) -> None:
        if settings.provider_audio == "mic":
            try:
                import sounddevice  # noqa: F401

                self.input: AudioInput = MicInput()
                self.output: AudioOutput = SpeakerOutput()
            except ImportError:
                log.warning("sounddevice unavailable; audio falls back to mock")
                self.input, self.output = MockInput(), MockOutput()
        else:
            self.input, self.output = MockInput(), MockOutput()

    @property
    def mode(self) -> str:
        return self.input.name


audio_io = AudioIO()
