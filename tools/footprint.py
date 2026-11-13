"""Draws the two dotted maps on the photography timeline page and saves them as tools/footprint.json.

Only needed again if the maps' edges or the dot spacing change; the site build reads footprint.json and
does not need the map data. The land outline is Natural Earth (public domain), 1:50m, as packaged in the
npm module world-atlas:

    npm pack world-atlas@2 && tar xzf world-atlas-*.tgz
    python3 tools/footprint.py package/land-50m.json

Each map is a plain grid of dots, one wherever the grid point is on land. Positions are in the map's own
units: 10 units to one degree of latitude, and east-west distances shortened by cos(33°) so that shapes at
the latitudes in question look right. tools/photography.py places the markers with the same arithmetic
(see `spot()` there), so PANELS below and in that file must agree.

Needs Pillow.
"""
import json, math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
UNIT = 10                                  # map units per degree of latitude
SQUEEZE = math.cos(math.radians(33))       # east-west shortening
PITCH = 8                                  # distance between dots, in map units
# key: (west, east, south, north) in degrees
PANELS = {
    "asia": (97, 125, 16, 42),
    "america": (-126, -66, 24, 50),
}


def rings(topo):
    """Every ring of the land polygons as a list of (lon, lat)."""
    sx, sy = topo["transform"]["scale"]
    tx, ty = topo["transform"]["translate"]
    arcs = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx; y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(idx):
        out = []
        for i in idx:
            pts = arcs[i] if i >= 0 else arcs[~i][::-1]
            out += pts[1:] if out else pts
        return out

    for g in topo["objects"]["land"]["geometries"]:
        polys = g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]
        for poly in polys:
            yield [ring(r) for r in poly]


def panel(topo, west, east, south, north):
    res = 20                                # mask pixels per degree
    pad = 1
    W, H = int((east - west + 2 * pad) * res), int((north - south + 2 * pad) * res)
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    px = lambda lon, lat: ((lon - west + pad) * res, (north + pad - lat) * res)
    for poly in rings(topo):
        outer = poly[0]
        if max(p[0] for p in outer) < west - pad or min(p[0] for p in outer) > east + pad:
            continue
        d.polygon([px(*p) for p in outer], fill=255)
        for hole in poly[1:]:
            d.polygon([px(*p) for p in hole], fill=0)
    w, h = (east - west) * SQUEEZE * UNIT, (north - south) * UNIT
    cols, rows = int(w // PITCH), int(h // PITCH)
    x0, y0 = (w - cols * PITCH) / 2 + PITCH / 2, (h - rows * PITCH) / 2 + PITCH / 2
    path, n = [], 0
    for r in range(rows):
        y = y0 + r * PITCH
        lat = north - y / UNIT
        last = None
        for c in range(cols):
            x = x0 + c * PITCH
            lon = west + x / (SQUEEZE * UNIT)
            mx, my = px(lon, lat)
            if mask.getpixel((int(mx), int(my))) < 128:
                continue
            if last is None:
                path.append(f"M{x:.1f} {y:.1f}h0")
            else:
                path.append(f"m{PITCH * (c - last)} 0h0")
            last = c; n += 1
    return dict(w=round(w, 1), h=round(h, 1), dots="".join(path).replace(".0", ""), count=n)


if __name__ == "__main__":
    topo = json.load(open(sys.argv[1]))
    out = {k: dict(panel(topo, *b), bounds=list(b)) for k, b in PANELS.items()}
    out["unit"], out["squeeze"], out["pitch"] = UNIT, round(SQUEEZE, 6), PITCH
    with open(os.path.join(HERE, "footprint.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, separators=(",", ":"))
    for k in PANELS:
        print(k, out[k]["w"], "x", out[k]["h"], out[k]["count"], "dots,", len(out[k]["dots"]), "characters")
