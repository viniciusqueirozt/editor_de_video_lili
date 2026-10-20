"""Entrada absoluta para iniciar o MCP a partir de qualquer pasta."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lili.mcp import main

if __name__ == "__main__":
    main()
