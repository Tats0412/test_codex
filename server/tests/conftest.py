import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Tests must never hit the Anthropic API
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used")
