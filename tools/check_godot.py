"""Run the pinned editor import and smoke test with bounded, inspected output."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ERROR = re.compile(r"(?m)^\s*(?:ERROR|SCRIPT ERROR|SHADER ERROR|FATAL|PANIC):|thread '[^']+' panicked")
ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", default=os.environ.get("GODOT", "godot"))
    parser.add_argument("--project", type=Path, default=ROOT / "godot")
    args = parser.parse_args()
    version = subprocess.check_output([args.godot, "--version"], text=True).strip()
    if not version.startswith("4.7.2.stable.official."):
        sys.exit(f"Expected Godot 4.7.2 stable standard, found {version}")
    for flags, marker in [
        (["--editor", "--import"], None),
        (["--script", "res://tests/smoke.gd"], "SPACE DIE SMOKE PASS"),
        (["--script","res://tests/test_demo_clock.gd","--","--railgun-demo"], "RAIL LIVE CLOCK PASS"),
    ]:
        proc = subprocess.run(
            [args.godot, "--headless", "--path", str(args.project), *flags],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=150,
        )
        output = re.sub(r"\x1b\[[0-9;]*m", "", proc.stdout + proc.stderr)
        print(output, flush=True)
        if proc.returncode or ERROR.search(output) or (marker and marker not in output):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
