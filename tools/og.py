"""Writes the pictures that chat apps and social sites show when a page is shared:
1200x630 JPEG, because several of them do not accept WebP.

    python3 tools/og.py .

Run it after covers or photographs change. It writes assets/img/<project>/og.jpg,
assets/img/home/og.jpg and photography/og/<page>.jpg; the page generators only link to them.
"""
import os, sys
from PIL import Image

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photography as G

W, H = 1200, 630


def card(src, dst, fx=0.5, fy=0.5):
    """Crops `src` to 1200x630 around the point (fx, fy), given as fractions of its width and height."""
    im = Image.open(src).convert("RGB")
    k = max(W / im.width, H / im.height)
    im = im.resize((max(W, round(im.width * k)), max(H, round(im.height * k))), Image.LANCZOS)
    x = min(max(0, round(im.width * fx - W / 2)), im.width - W)
    y = min(max(0, round(im.height * fy - H / 2)), im.height - H)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im.crop((x, y, x + W, y + H)).save(dst, "JPEG", quality=84, optimize=True, progressive=True)


def photo(n):
    files = G.ph(n)["files"]
    size = next((k for k, _ in files if k == 1400), files[-1][0])
    return os.path.join(ROOT, "photography", "img", f"{n:03d}-{size}.webp")


def focus(s):
    if s.get("focus"):
        x, y = (float(v.strip("%")) / 100 for v in s["focus"].split())
        return x, y
    return 0.5, 0.5 if G.ar(s["cover"]) > 1 else 0.38


img = os.path.join(ROOT, "assets", "img")
n = 0
for proj in sorted(os.listdir(img)):
    cover = os.path.join(img, proj, "cover.webp")
    if os.path.exists(cover):
        card(cover, os.path.join(img, proj, "og.jpg")); n += 1
card(os.path.join(img, "home", "cornell-1600.webp"), os.path.join(img, "home", "og.jpg"), 0.66, 0.5); n += 1
og = os.path.join(ROOT, "photography", "og")
card(photo(G.SLIDES[0][0]), os.path.join(og, "index.jpg")); card(photo(G.SLIDES[0][0]), os.path.join(og, "all.jpg")); n += 2
for s in G.SERIES:
    card(photo(s["cover"]), os.path.join(og, s["slug"] + ".jpg"), *focus(s)); n += 1
for g in G.SUBJECTS:
    first = sorted(g["photos"], key=G.ORDER.index)[0]
    card(photo(first), os.path.join(og, g["slug"] + ".jpg"), 0.5, 0.5 if G.ar(first) > 1 else 0.38); n += 1


def footprint(dst):
    """The timeline's picture: the dotted globe seen over the Pacific, a red point where each series was made and
    arcs from one to the next, as on the page (photography/assets/timeline.js)."""
    import base64, math
    from PIL import ImageDraw, ImageFilter
    S = 3                                                     # drawn at three times the size, then reduced
    big = Image.new("RGB", (W * S, H * S), (0, 0, 0))
    R = 270 * S; cx, cy = W * S / 2, H * S / 2 + 12 * S
    lat0, lon0 = math.radians(28), math.radians(-172)

    def proj(lat, lon, alt=1.0):
        la, lo = math.radians(lat), math.radians(lon) - lon0
        x, y, z = math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)
        y2, z2 = y * math.cos(lat0) - z * math.sin(lat0), y * math.sin(lat0) + z * math.cos(lat0)
        return cx + x * R * alt, cy - y2 * R * alt, z2, (x * x + y2 * y2) * alt * alt

    glow = Image.new("RGB", big.size, (0, 0, 0))              # atmosphere
    ImageDraw.Draw(glow).ellipse([cx - R * 1.04, cy - R * 1.04, cx + R * 1.04, cy + R * 1.04], fill=(70, 74, 82))
    big = Image.blend(big, glow.filter(ImageFilter.GaussianBlur(28 * S)), 1.0)
    d = ImageDraw.Draw(big)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(9, 9, 10))
    bits = base64.b64decode(G.LAND["land"]); N = G.LAND["n"]; g = math.pi * (3 - math.sqrt(5))
    for i in range(N):
        if not bits[i >> 3] & (0x80 >> (i & 7)):
            continue
        y = 1 - (i + 0.5) * 2 / N; r = math.sqrt(1 - y * y); a = i * g
        x, yy, z, _ = proj(math.degrees(math.asin(y)), math.degrees(math.atan2(math.sin(a) * r, math.cos(a) * r)))
        if z <= 0:
            continue
        v = int(30 + 190 * z ** 0.8); rr = 1.25 * S
        d.ellipse([x - rr, yy - rr, x + rr, yy + rr], fill=(v, v, v))

    def vec(lat, lon):
        la, lo = math.radians(lat), math.radians(lon)
        return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))
    stops = sorted(G.SERIES, key=lambda s: G.TIMELINE[s["slug"]]["date"])
    places = [G.TIMELINE[s["slug"]]["at"][0] for s in stops if G.TIMELINE[s["slug"]]["at"]]
    for (la1, lo1), (la2, lo2) in zip(places, places[1:]):
        a, b = vec(la1, lo1), vec(la2, lo2)
        w = math.acos(max(-1, min(1, sum(p * q for p, q in zip(a, b)))))
        if w < 0.01:
            continue
        pts = []
        for k in range(65):
            t = k / 64
            f1, f2 = math.sin((1 - t) * w) / math.sin(w), math.sin(t * w) / math.sin(w)
            v = [f1 * p + f2 * q for p, q in zip(a, b)]
            lat = math.degrees(math.asin(max(-1, min(1, v[2])))); lon = math.degrees(math.atan2(v[1], v[0]))
            x, yy, z, rad = proj(lat, lon, 1 + (0.025 + 0.09 * min(w, 1.2) / math.pi) * math.sin(math.pi * t))
            pts.append((x, yy, z > 0))
        for (x1, y1, v1), (x2, y2, v2) in zip(pts, pts[1:]):
            if v1 and v2:
                d.line([x1, y1, x2, y2], fill=(235, 100, 80), width=int(2.2 * S))
    for s in stops:
        for lat, lon in G.TIMELINE[s["slug"]]["at"]:
            x, yy, z, _ = proj(lat, lon)
            if z > 0:
                rr = (3.2 + 0.8 * len(G.ids(s)) ** 0.5) * S
                d.ellipse([x - rr, yy - rr, x + rr, yy + rr], fill=(235, 92, 72))
    big.resize((W, H), Image.LANCZOS).save(dst, "JPEG", quality=86, optimize=True, progressive=True)


footprint(os.path.join(og, "timeline.jpg")); n += 1
print("wrote", n, "sharing pictures")
