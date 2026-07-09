from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "data",
    "dist",
    "build",
}

PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    "bearer_token": re.compile(r"(?i)bearer\s+[a-z0-9._~+/=-]{30,}"),
    "long_hex_secret": re.compile(r"(?i)(secret|token|password)\s*[:=]\s*['\"]?[a-f0-9]{32,}"),
    "client_id_like_value": re.compile(r"\bbdn-[A-Za-z0-9_-]{20,}\b"),
}


def main() -> None:
    findings: list[str] = []

    for path in ROOT.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name.startswith(".env") and path.name != ".env.example":
            findings.append(f"Local env file should not be committed: {path}")
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{label} in {path}")

    if findings:
        print("Potential secret material found:")
        for finding in findings:
            print(f" - {finding}")
        sys.exit(1)

    print("No obvious secret material found.")


if __name__ == "__main__":
    main()
