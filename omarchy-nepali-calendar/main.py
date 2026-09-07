#!/usr/bin/env python3
"""
Entry point for nepali-calendar plugin.
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from lib.cli import main

if __name__ == "__main__":
    main()
