"""Bake or verify the four offline partitions against the planet definitions."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "godot/data/fractures"
SEEDS = {"mercury": 31001, "venus": 31002, "earth": 31003, "mars": 31004}


def digest(paths):
    h = hashlib.sha256()
    for path in paths:
        h.update(path.read_bytes())
    return h.hexdigest()


def build(check=False):
    rust = ROOT / "rust"
    def cargo(*args):
        return subprocess.check_output(["cargo", *args], cwd=rust)
    cargo("build", "--release", "--locked", "-p", "bake_cli")
    target = Path(json.loads(cargo("metadata", "--format-version", "1", "--locked", "--no-deps"))["target_directory"])
    import os
    cli = target / "release" / ("bake_cli.exe" if os.name == "nt" else "bake_cli")
    OUT.mkdir(exist_ok=True)
    manifest = {"version": 1, "algorithm_sha256": digest([rust/"fracture_core/src"/name for name in
                ("geometry.rs","voronoi.rs","rng.rs")] + [rust/"Cargo.lock"]), "partitions": {}}
    for planet, seed in SEEDS.items():
        definition = (ROOT/f"godot/data/planets/{planet}.tres").read_text()
        count = int(re.search(r"^fracture_count = (\d+)$", definition, re.M)[1])
        path = OUT / (planet+".json")
        if not check:
            subprocess.run([cli,"--planet",planet,"--count",str(count),"--seed",str(seed),"--output",path],check=True)
        subprocess.run([cli,"--validate","--output",path],check=True)
        data = json.loads(path.read_bytes())
        if (data["planet_id"], data["seed"], len(data["cells"])) != (planet,seed,count):
            raise ValueError(f"Stale metadata for {planet}")
        manifest["partitions"][planet] = {"count":count,"seed":seed,"sha256":digest([path])}
    file = OUT / "manifest.json"
    if check:
        if json.loads(file.read_bytes()) != manifest: raise ValueError("Stale fracture cache")
    else:
        file.write_text(json.dumps(manifest,indent=2)+"\n")


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true")
    build(parser.parse_args().check)
