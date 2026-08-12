"""NVIDIA integration layer.

Every section of the OS talks to NVIDIA through these small interfaces:
    - LLM   : NVIDIA NIM / AI Endpoints (OpenAI compatible)
    - ASR   : NVIDIA Riva cloud speech recognition
    - TTS   : NVIDIA Riva cloud speech synthesis

Each provider has a *mock* counterpart so the OS runs fully offline.
"""
