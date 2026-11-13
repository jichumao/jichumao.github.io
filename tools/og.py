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
card(os.path.join(img, "home", "sponza-1920.webp"), os.path.join(img, "home", "og.jpg"), 0.58, 0.5); n += 1
og = os.path.join(ROOT, "photography", "og")
card(photo(G.SLIDES[0][0]), os.path.join(og, "index.jpg")); card(photo(G.SLIDES[0][0]), os.path.join(og, "all.jpg")); n += 2
for s in G.SERIES:
    card(photo(s["cover"]), os.path.join(og, s["slug"] + ".jpg"), *focus(s)); n += 1
for g in G.SUBJECTS:
    first = sorted(g["photos"], key=G.ORDER.index)[0]
    card(photo(first), os.path.join(og, g["slug"] + ".jpg"), 0.5, 0.5 if G.ar(first) > 1 else 0.38); n += 1
print("wrote", n, "sharing pictures")
