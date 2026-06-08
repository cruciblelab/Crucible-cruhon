"""pytest configuration for Cruhon tests."""
import sys
from pathlib import Path

# Ensure the package root (one level above cruhon/) is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
