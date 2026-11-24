"""Fetch the pinned source data for a developer-initiated rebake."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def fetch():
    for entry in json.loads((ROOT / "godot/data/assets_manifest.json").read_text())["sources"]:
        dest = ROOT / entry["path"]
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == entry["sha256"]:
            continue
        with urlopen(entry["url"], timeout=90) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Checksum mismatch for {dest.name}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)


if __name__ == "__main__":
    fetch()
