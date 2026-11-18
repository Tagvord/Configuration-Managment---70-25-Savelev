
import sys
from pathlib import Path

def main():
    """Запускает ассемблер из каталога исходников."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.uvm_asm import main as run
    run()


if __name__ == "__main__":
    main()
