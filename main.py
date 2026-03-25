#!/usr/bin/env python3
"""
YouTube Downloader Pro - Ponto de entrada principal.
"""

import os
import sys

# Adiciona o diretório src ao path antes dos imports
src_path = os.path.join(os.path.dirname(__file__), "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# ruff: noqa: E402
from gui.main_window import main  # ty: ignore[unresolved-import]

if __name__ == "__main__":
    main()
