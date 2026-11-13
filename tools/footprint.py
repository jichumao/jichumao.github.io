"""Makes the land data for the globe on the photography timeline page and saves it as tools/footprint.json.

Only needed again to change the density of the globe's dots; the site build reads footprint.json and does not
need the map data. The land outline is Natural Earth (public domain), 1:50m, as packaged in the npm module
world-atlas:

    npm pack world-atlas@2 && tar xzf world-atlas-*.tgz
    python3 tools/footprint.py package/land-50m.json

The globe's dots are N points spread evenly over a sphere (a Fibonacci lattice). footprint.json says which of
them are on land, one bit per point, so the page only needs a few kilobytes. photography/assets/timeline.js and
tools/og.py rebuild the same lattice, point i at:

    y = 1 - (i + 0.5) * 2 / N,  r = sqrt(1 - y*y),  a = i * pi * (3 - sqrt(5))
    latitude = asin(y),  longitude = atan2(sin(a) * r, cos(a) * r)

Needs Pillow.
"""
import base64, json, math, os, sys
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
N = 40000


def lattice(n=N):
    g = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        y = 1 - (i + 0.5) * 2 / n
        r = math.sqrt(1 - y * y)
        a = i * g
        yield math.degrees(math.asin(y)), math.degrees(math.atan2(math.sin(a) * r, math.cos(a) * r))


def land_mask(topo, W=2880, H=1440):
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

    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    px = lambda p: ((p[0] + 180) / 360 * W, (90 - p[1]) / 180 * H)
    for g in topo["objects"]["land"]["geometries"]:
        for poly in (g["arcs"] if g["type"] == "MultiPolygon" else [g["arcs"]]):
            d.polygon([px(p) for p in ring(poly[0])], fill=255)
            for hole in poly[1:]:
                d.polygon([px(p) for p in ring(hole)], fill=0)
    return mask


if __name__ == "__main__":
    topo = json.load(open(sys.argv[1]))
    mask = land_mask(topo)
    W, H = mask.size
    bits = bytearray((N + 7) // 8)
    count = 0
    for i, (lat, lon) in enumerate(lattice()):
        x = min(W - 1, int((lon + 180) / 360 * W)); y = min(H - 1, int((90 - lat) / 180 * H))
        if mask.getpixel((x, y)) >= 128:
            bits[i >> 3] |= 0x80 >> (i & 7); count += 1
    out = {"n": N, "land": base64.b64encode(bytes(bits)).decode()}
    with open(os.path.join(HERE, "footprint.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, separators=(",", ":"))
    print(count, "land points of", N, ";", len(out["land"]), "characters")
