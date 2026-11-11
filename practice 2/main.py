"""Запуск: python main.py [config.toml] [--order]."""

import sys
from pathlib import Path


def main():
    """Запускает визуализатор из каталога исходников."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.apk_graph import main as run

    run()


if __name__ == "__main__":
    main()
