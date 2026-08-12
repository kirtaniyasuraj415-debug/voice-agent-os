"""Test configuration - isolated temp database per test run."""
from __future__ import annotations

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TMP_DB = tempfile.mkdtemp(prefix="vaos_test_") + "/vaos_test.db"
os.environ["VAOS_DB_PATH"] = TMP_DB
