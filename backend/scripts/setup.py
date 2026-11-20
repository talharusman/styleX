"""
Backend setup helper.

Usage (from the backend/ directory):
    python scripts/setup.py            # venv + deps + .env
    python scripts/setup.py --no-deps  # only create .env

Creates .venv, installs requirements.txt, and copies .env.example to .env
(generating a random SECRET_KEY). It does not start MongoDB - see the root README.
"""
import argparse
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def create_env() -> None:
    env, example = BACKEND / ".env", BACKEND / ".env.example"
    if env.exists():
        print(".env already exists - leaving it untouched")
        return
    text = example.read_text(encoding="utf-8")
    text = text.replace(
        "SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars",
        f"SECRET_KEY={secrets.token_urlsafe(48)}",
    )
    env.write_text(text, encoding="utf-8")
    print("Created .env with a random SECRET_KEY. Add GROQ/OPENWEATHER/GOOGLE keys if you have them.")


def install_deps() -> None:
    venv = BACKEND / ".venv"
    if not venv.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
    py = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.check_call([str(py), "-m", "pip", "install", "-r", str(BACKEND / "requirements.txt")])
    print(f"Dependencies installed. Activate with: {venv / ('Scripts/activate' if sys.platform == 'win32' else 'bin/activate')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-deps", action="store_true")
    args = ap.parse_args()
    create_env()
    if not args.no_deps:
        install_deps()
    if shutil.which("mongod") is None and shutil.which("docker") is None:
        print("WARNING: neither mongod nor docker found - install one to run MongoDB.")
    print("Next: start MongoDB, then `uvicorn app.main:app --reload` from backend/.")


if __name__ == "__main__":
    main()
