"""Check offline source products before importing or packaging the atlas."""
import hashlib
import json
from pathlib import Path
import struct

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def check():
    manifest = json.loads((ROOT / "godot/data/assets_manifest.json").read_text())
    for entry in manifest["generated"]:
        data = (ROOT / entry["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Output hash mismatch for {entry['path']}")
    expected = {"Railgun": (8000,15000), "RailgunMedium": (3000,5000),
                "Vera": (10000,20000), "VeraMedium": (4500,5500)}
    model_dir = ROOT / "godot/assets/models"
    for name,(minimum,maximum) in expected.items():
        data = (model_dir / (name+".glb")).read_bytes()
        if data[:4] != b"glTF":
            raise ValueError(f"Missing binary glTF: {name}")
        length = struct.unpack_from("<I",data,12)[0]
        gltf = json.loads(data[20:20+length])
        triangles = sum(gltf["accessors"][p["indices"]]["count"]//3
                        for m in gltf["meshes"] for p in m["primitives"])
        if not minimum <= triangles <= maximum:
            raise ValueError(f"{name}: {triangles} triangles outside budget")
        print(f"{name}: {triangles} triangles")
    geo = ROOT / "godot/data"
    rows = json.loads((geo/"countries.json").read_bytes())
    with Image.open(geo/"country_mask.png") as mask:
        if mask.mode != "RGB" or mask.size != (4096,2048):
            raise ValueError("Expected raw RG-packed lookup in a lossless RGB PNG")
        for row in rows:
            x = int((row["lon"]/360+.5)*mask.width) % mask.width
            y = min(mask.height-1,int((.5-row["lat"]/180)*mask.height))
            r,g,_ = mask.getpixel((x,y))
            if r+256*g != row["id"]:
                raise ValueError(f"Representative point is outside {row['code']}")
    print(f"Verified {len(rows)} regions and {len(manifest['generated'])} baked outputs")


if __name__ == "__main__":
    check()
