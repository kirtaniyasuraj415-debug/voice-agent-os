"""Voice pipeline - record -> ASR -> commander -> TTS -> speak.

The end-to-end voice assistant loop that drives the whole OS.
"""
from __future__ import annotations

import logging

from nvidia.factory import nvidia_stack
from voice.audio import audio_io
from voice.commander import commander

log = logging.getLogger("vaos.voice.pipeline")


class VoicePipeline:
    def __init__(self) -> None:
        self.enabled = True
        self.conversation: list[dict[str, str]] = []

    def one_turn(self, audio_bytes: bytes | None = None, text: str | None = None) -> tuple[str, bytes]:
        """Process one voice round-trip and return (reply_text, reply_wav)."""
        if text is None:
            audio = audio_bytes if audio_bytes is not None else audio_io.input.record(3.0)
            text = nvidia_stack.asr.transcribe(audio, "en-US")
        self.conversation.append({"speaker": "user", "text": text})

        reply = commander.respond(text)
        self.conversation.append({"speaker": "nova", "text": reply})
        wav = commander.speak(reply)
        return reply, wav

    def run_interactive(self) -> None:
        """Continuous voice loop (ctrl+C to stop)."""
        print(f"\n  {commander.name} voice pipeline is live. Mode: {audio_io.mode}.")
        print("  (press Ctrl+C to stop)\n")
        import time

        while self.enabled:
            try:
                reply, wav = self.one_turn()
                print(f"  You: {self.conversation[-2]['text']}")
                print(f"  {commander.name}: {reply}\n")
                audio_io.output.play(wav)
                time.sleep(0.3)
            except KeyboardInterrupt:
                break


pipeline = VoicePipeline()
