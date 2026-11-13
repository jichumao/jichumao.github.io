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
card(os.path.join(img, "home", "subway-interior-1920.webp"), os.path.join(img, "home", "og.jpg"), 0.5, 0.5); n += 1
og = os.path.join(ROOT, "photography", "og")
card(photo(G.SLIDES[0][0]), os.path.join(og, "index.jpg")); card(photo(G.SLIDES[0][0]), os.path.join(og, "all.jpg")); n += 2
for s in G.SERIES:
    card(photo(s["cover"]), os.path.join(og, s["slug"] + ".jpg"), *focus(s)); n += 1
for g in G.SUBJECTS:
    first = sorted(g["photos"], key=G.ORDER.index)[0]
    card(photo(first), os.path.join(og, g["slug"] + ".jpg"), 0.5, 0.5 if G.ar(first) > 1 else 0.38); n += 1


def footprint(dst):
    """The timeline's picture: both dotted maps side by side, a red point wherever a series was made."""
    import re
    from PIL import ImageDraw
    S = 3                                                     # drawn at three times the size, then reduced
    gap, pad = 40, 70
    maps = [("asia", G.MAPS["asia"]), ("america", G.MAPS["america"])]
    k = (W - 2 * pad - gap) / sum(m["w"] for _, m in maps)
    k = min(k, (H - 2 * pad) / max(m["h"] for _, m in maps))
    big = Image.new("RGB", (W * S, H * S), (0, 0, 0))
    d = ImageDraw.Draw(big)
    x0 = (W - (sum(m["w"] for _, m in maps) * k + gap)) / 2
    y0 = (H - max(m["h"] for _, m in maps) * k) / 2
    for key, m in maps:
        x = y = 0.0
        for mm in re.finditer(r"([Mm])(-?[\d.]+) (-?[\d.]+)h0", m["dots"]):
            if mm.group(1) == "M":
                x, y = float(mm.group(2)), float(mm.group(3))
            else:
                x += float(mm.group(2)); y += float(mm.group(3))
            cx, cy, r = (x0 + x * k) * S, (y0 + y * k) * S, 1.15 * k * S
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 70, 70))
        for s in G.SERIES:
            for lat, lon in G.TIMELINE[s["slug"]]["at"]:
                west, east, south, north = m["bounds"]
                if west <= lon <= east and south <= lat <= north:
                    px, py = G.spot(key, lat, lon)
                    cx, cy, r = (x0 + px * k) * S, (y0 + py * k) * S, (2.6 + 0.9 * len(G.ids(s)) ** 0.5) * k * S
                    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(219, 79, 61))
        x0 += m["w"] * k + gap
    big.resize((W, H), Image.LANCZOS).save(dst, "JPEG", quality=86, optimize=True, progressive=True)


footprint(os.path.join(og, "timeline.jpg")); n += 1
print("wrote", n, "sharing pictures")
