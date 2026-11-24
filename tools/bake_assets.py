"""Bake longitude-wrapped land, country lookup, and illustrated Earth maps."""
from collections import Counter
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, map_coordinates, distance_transform_edt
from shapely.geometry import Polygon, Point, box
from shapely.affinity import translate

from fetch_assets import ROOT, fetch

DATA = ROOT / "godot/data"
TEX = ROOT / "godot/assets/textures"
W, H = 4096, 2048
rng = np.random.default_rng(71023)


def unwrap(ring):
    coords = [ring[0]]
    for lon, lat in ring[1:]:
        prev, prev_lat = coords[-1]
        if abs(lat) < 89.9999 or abs(prev_lat) < 89.9999:
            lon += 360 * round((prev - lon) / 360)
        coords.append((lon, lat))
    return coords


def parts(geometry):
    polygons = geometry["coordinates"]
    if geometry["type"] == "Polygon":
        polygons = [polygons]
    for shell, *holes in polygons:
        shell = unwrap(shell)
        inside = []
        for hole in holes:
            ring = unwrap(hole)
            shift = 360 * round((shell[0][0] - ring[0][0]) / 360)
            inside.append([(x + shift, y) for x, y in ring])
        poly = Polygon(shell, inside)
        if not poly.is_valid:
            poly = poly.buffer(0)
        for shift in (-360, 0, 360):
            piece = translate(poly, xoff=shift)
            if piece.bounds[0] > 180 or piece.bounds[2] < -180:
                continue
            piece = piece.intersection(box(-180, -90, 180, 90))
            for p in getattr(piece, "geoms", [piece]):
                if p.geom_type == "Polygon" and p.area > 0:
                    yield p


def pixels(ring, width, height):
    return [((lon / 360 + 0.5) * width, (0.5 - lat / 180) * height)
            for lon, lat in ring.coords]


def paint(image, polygons, value):
    # Draw each polygon on its own tile so enclave holes retain previous IDs.
    w, h = image.size
    for poly in polygons:
        xy = pixels(poly.exterior, w, h)
        left = max(0, int(min(x for x, y in xy)))
        top = max(0, int(min(y for x, y in xy)))
        right = min(w, int(max(x for x, y in xy)) + 1)
        bottom = min(h, int(max(y for x, y in xy)) + 1)
        if right <= left or bottom <= top:
            continue
        tile = Image.new("1", (right-left, bottom-top))
        draw = ImageDraw.Draw(tile)
        for coords, fill in [(xy, 1)] + [(pixels(hole, w, h), 0) for hole in poly.interiors]:
            draw.polygon([(x-left, y-top) for x, y in coords], fill=fill)
        image.paste(value, (left, top, right, bottom), tile)


def features(dataset):
    return json.loads((ROOT / ".tools/assets" / (dataset + ".geojson")).read_bytes())["features"]


def country_maps():
    mask = Image.new("I", (W, H))
    countries = []
    records = features("ne_50m_admin_0_countries")
    iso_counts = Counter(f["properties"]["ISO_A2_EH"] for f in records)
    for feature in records:
        prop = feature["properties"]
        src = prop["ADM0_A3"]
        iso = prop["ISO_A2_EH"]
        code = iso if len(iso) == 2 and (iso_counts[iso] == 1 or src == "AUS") else src
        a, b, c = (ord(ch) - ord("A") for ch in src)
        ident = 1 + 676*a + 26*b + c
        polys = list(parts(feature["geometry"]))
        paint(mask, polys, ident)
        label = Point(prop["LABEL_X"], prop["LABEL_Y"])
        if not any(poly.contains(label) for poly in polys):
            label = max(polys, key=lambda p: p.area).representative_point()
        countries.append((dict(id=ident, code=code, source_code=src, en=prop["NAME_EN"],
                               ru=prop["NAME_RU"] or prop["NAME_EN"]), label, polys))
    array = np.asarray(mask).copy()
    result = []
    reserved = set()
    for row, point, polys in sorted(countries, key=lambda entry: sum(p.area for p in entry[2])):
        x = int((point.x/360+0.5)*W) % W
        y = min(H-1, int((0.5-point.y/180)*H))
        if array[y, x] != row["id"] or (x, y) in reserved:
            # Prefer an inland pixel; for a subpixel island reserve the cell
            # containing its actual internal representative point.
            yy, xx = np.where(array == row["id"])
            for index in np.argsort((xx-x)**2 + (yy-y)**2):
                candidate = Point(((xx[index]+0.5)/W-0.5)*360, (0.5-(yy[index]+0.5)/H)*180)
                if (xx[index], yy[index]) not in reserved and any(poly.contains(candidate) for poly in polys):
                    point = candidate
                    break
            else:
                candidates = []
                for dy in range(-2,3):
                    for dx in range(-2,3):
                        ix, iy = (x+dx)%W, y+dy
                        if (ix,iy) in reserved or not 0 <= iy < H:
                            continue
                        cell = box((ix/W-.5)*360,(.5-(iy+1)/H)*180,
                                   ((ix+1)/W-.5)*360,(.5-iy/H)*180)
                        for poly in polys:
                            patch = poly.intersection(cell)
                            if patch.area:
                                candidates.append((patch.area,ix,iy,patch.representative_point()))
                _, ix, iy, point = max(candidates, key=lambda candidate:candidate[0])
                array[iy,ix] = row["id"]
        reserved.add((int((point.x/360+.5)*W)%W,int((.5-point.y/180)*H)))
        row["lon"], row["lat"] = round(point.x, 7), round(point.y, 7)
        result.append(row)
    for row in result:
        assert array[int((0.5-row["lat"]/180)*H), int((row["lon"]/360+0.5)*W)%W] == row["id"], row
    rgb = np.stack((array % 256, array // 256, np.zeros_like(array)), -1).astype("uint8")
    Image.fromarray(rgb).save(DATA / "country_mask.png")
    (DATA / "countries.json").write_text(json.dumps(sorted(result,key=lambda x:x["id"]),
        ensure_ascii=False, separators=(",",":")) + "\n", encoding="utf-8")


def field(h, w, scale):
    noise = rng.random((scale, scale*2), dtype=np.float32)
    y, x = np.mgrid[:h, :w].astype("float32")
    return map_coordinates(noise, [y*scale/h, x*2*scale/w], order=3, mode="grid-wrap")


def earth_textures():
    h, w = 1024, 2048
    land = Image.new("L", (w,h))
    for feature in features("ne_50m_land"):
        paint(land, parts(feature["geometry"]), 255)
    land = np.asarray(land) > 0
    Image.fromarray(np.uint8(~land)*255).save(TEX/"ocean.png")
    latitude = np.abs(np.linspace(1,-1,h)[:,None])
    terrain = sum(amp*field(h,w,n) for n,amp in [(8,.45),(25,.31),(68,.15),(184,.09)])
    dry = np.clip(1.5 - 5*np.abs(latitude-.29) + 2*(terrain-.58),0,1)
    wet = np.array([42,82,66])
    sand = np.array([195,154,101])
    land_rgb = wet+(sand-wet)*dry[:,:,None]
    land_rgb += ((terrain-.5)*78)[:,:,None]
    ice = np.clip((latitude-.77)*6+(terrain-.5),0,1)[:,:,None]
    land_rgb = land_rgb*(1-ice)+np.array([213,223,220])*ice
    coast = np.exp(-distance_transform_edt(~land)/4)
    sea = np.array([17,46,80])+coast[:,:,None]*np.array([11,58,52])+terrain[:,:,None]*12
    pack_ice = np.clip((latitude-.84)*7+(terrain-.49)*.65,0,1)[:,:,None]
    sea = sea*(1-pack_ice) + np.array([205,219,225])*pack_ice
    day = np.uint8(np.clip(np.where(land[:,:,None],land_rgb,sea),0,255))
    Image.fromarray(day).resize((W,H),Image.Resampling.BICUBIC).save(TEX/"earth_day.jpg",quality=92)
    density = (field(h,w,49)**5)*np.clip(1.15-latitude,0,1)
    points = (rng.random((h,w)) < density*.17)*land
    glow = np.clip(points*.8 + gaussian_filter(points.astype(float),1.2)*2.1,0,1)
    Image.fromarray(np.uint8(glow[:,:,None]*np.array([255,194,108]))).save(TEX/"earth_night.jpg",quality=95)
    swirl = field(h,w,8)
    y,x=np.mgrid[:h,:w].astype("float32")
    cloud = .50*field(h,w,17)+.3*field(h,w,52)+.2*field(h,w,128)
    cloud = map_coordinates(cloud,[y+24*np.sin(swirl*7),x+45*swirl],order=1,mode="grid-wrap")
    polar_weight = np.clip((1-latitude)*9,0,1)
    alpha = np.uint8(np.clip((cloud-.42)*2.25,0,1)*polar_weight*255)
    clouds = Image.new("RGBA",(w,h),"white")
    clouds.putalpha(Image.fromarray(alpha))
    clouds.save(TEX/"clouds.png")


if __name__ == "__main__":
    fetch()
    TEX.mkdir(parents=True, exist_ok=True)
    country_maps()
    earth_textures()
