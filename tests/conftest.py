"""Test configuration - isolated temp database and mock providers per test run."""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TMP_DB = tempfile.mkdtemp(prefix="vaos_test_") + "/vaos_test.db"
os.environ["VAOS_DB_PATH"] = TMP_DB

# Force offline providers so tests never hit NVIDIA rate limits.
os.environ.setdefault("PROVIDER_LLM", "mock")
os.environ.setdefault("PROVIDER_ASR", "mock")
os.environ.setdefault("PROVIDER_TTS", "mock")
os.environ.setdefault("PROVIDER_TELEPHONY", "mock")
os.environ.setdefault("PROVIDER_AUDIO", "mock")
