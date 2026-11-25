import sys
from pathlib import Path


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.apk_graph import main as run

    run()


if __name__ == "__main__":
    main()
