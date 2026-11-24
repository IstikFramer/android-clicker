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
    # Retain Natural Earth's shaded relief, bathymetry and permanent ice at 4K.
    atlas = np.asarray(Image.open(ROOT/".tools/assets/earth-relief.tif")
                       .convert("RGB").resize((W,H),Image.Resampling.LANCZOS), dtype=np.float32)/255
    shore = np.asarray(Image.fromarray(np.uint8(land)*255).resize((W,H), Image.Resampling.BILINEAR),
                       dtype=np.float32)[:,:,None]/255
    dry = np.clip((atlas-.23)*1.33,0,1)
    foliage = np.clip((atlas[:,:,1]-atlas[:,:,0])*7,0,1)[:,:,None]
    dry *= (1-.40*foliage)*np.array([.94,.94,.92],dtype=np.float32)
    blue = np.clip((atlas[:,:,2]-.46)*2.0,0,1)
    shelf = np.asarray(Image.fromarray(np.float32(np.exp(-distance_transform_edt(~land)/4)))
                       .resize((W,H),Image.Resampling.BILINEAR))
    sea = np.stack((.025+.03*blue, .09+.18*blue+.12*shelf, .17+.26*blue+.09*shelf),-1)
    ice = np.clip((atlas.min(axis=2)-.72)*5,0,1)[:,:,None]
    sea = sea*(1-ice)+atlas*ice
    day = np.uint8(np.clip(dry*shore+sea*(1-shore),0,1)*255)
    Image.fromarray(day).save(TEX/"earth_day.jpg",quality=94,subsampling=0)
    density = (field(h,w,49)**5)*np.clip(1.15-latitude,0,1)
    points = (rng.random((h,w)) < density*.17)*land
    glow = np.clip(points*.8 + gaussian_filter(points.astype(float),1.2)*2.1,0,1)
    Image.fromarray(np.uint8(glow[:,:,None]*np.array([255,194,108]))).save(TEX/"earth_night.jpg",quality=95)
    # Warp several cloud scales together. Rotating a bounded weather system
    # winds its fibres into fronts that taper continuously into surrounding air.
    y,x=np.mgrid[:h,:w].astype("float32")
    dx = 35*np.sin(y*0.012+field(h,w,7)*4)
    dy = 22*np.sin(x*0.006+field(h,w,9)*5)
    for cx,cy,r,direction in [(0.31,.36,105,1),(.74,.68,120,-1),(.87,.39,117,1),
                              (.43,.71,82,-1),(.18,.57,96,-1),(.60,.27,78,1)]:
        px=(x-cx*w+w/2)%w-w/2
        py=y-cy*h
        rr=(px*px+py*py)/(r*r)
        angle=direction*3.8*np.exp(-rr*1.3)
        dx+=px*(np.cos(angle)-1)-py*np.sin(angle)
        dy+=px*np.sin(angle)+py*(np.cos(angle)-1)
    cloud=sum(weight*field(h,w,scale) for scale,weight in [(12,.39),(33,.23),(78,.18),(177,.12),(281,.08)])
    eddies = field(h,w,63)-.5
    cloud=map_coordinates(cloud,[(y+dy+eddies*5)*1.53,x+dx+eddies*9],order=1,mode="grid-wrap")
    fibres = .6*field(h,w,229)+.4*field(h,w,399)-.5
    cloud += fibres*(.13+.19*np.clip(cloud,0,1))
    alpha=np.uint8(np.clip((cloud-.475)*3.75,0,1)*np.clip((1-latitude)*11,0,1)*255)
    clouds = Image.new("RGBA",(w,h),"white")
    clouds.putalpha(Image.fromarray(alpha))
    clouds.save(TEX/"clouds.png")


if __name__ == "__main__":
    fetch()
    TEX.mkdir(parents=True, exist_ok=True)
    country_maps()
    earth_textures()
    from bake_fractures import build
    build()
