import subprocess
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "libs" / "python39"
PACKAGE = "psycopg2-binary"

def main() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, "-m", "pip", "install", PACKAGE, "--upgrade", "--target", str(TARGET)]
    print("Running:", " ".join(args))
    subprocess.check_call(args)
    print(f"Installed {PACKAGE} into {TARGET}")

if __name__ == "__main__":
    main()
