"""Cover for the Motion Capture project: five poses from the finished animation, side by side in time order.

The character is cut out of frames of assets/video/motion-capture.mp4 (the final animation rendered in
MotionBuilder) by its colour: teal body parts, joined across the black joints between them. Nothing is
redrawn; each figure is the video's own pixels, placed on a dark ground with a soft shadow.

    python3 tools/cover-src/mocap-poses/poses.py . tools/cover-src/mocap-poses.png

Needs ffmpeg, Pillow, numpy and scipy.
"""
import os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

SITE, OUT = sys.argv[1], sys.argv[2]
VIDEO = os.path.join(SITE, "assets", "video", "motion-capture.mp4")
FPS = 5
# (frame number at 5 frames a second, left edge, height) on a 3000x2000 canvas: stride, kick, looking out, pointing, walking off
POSES = [(11, 80, 900), (27, 640, 900), (79, 1370, 920), (50, 1830, 900), (91, 2500, 920)]
W, H, BASE = 3000, 2000, 1500          # BASE: the line the feet stand on


def cut(path):
    """The character in one frame, as an RGBA image cropped to its outline."""
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(axis=2), a.min(axis=2)
    rows = np.zeros((h, w), bool); rows[90:990] = True            # the picture between the letterbox bars
    teal = ((mx - mn) / np.maximum(mx, 1) > 0.2) & (b > r + 12) & (g > r + 5) & rows
    teal = ndi.binary_opening(teal, iterations=1)
    lab, n = ndi.label(teal)
    body = lab == (int(np.argmax(ndi.sum(teal, lab, range(1, n + 1)))) + 1)
    dark = (mx < 31) & rows
    dlab, _ = ndi.label(dark)
    for _ in range(12):                                             # grow across the black joints to the other teal parts
        ids = np.unique(dlab[ndi.binary_dilation(body, iterations=5) & dark]); ids = ids[ids > 0]
        joints = np.isin(dlab, ids) & ndi.binary_dilation(body, iterations=60)
        ids = np.unique(lab[ndi.binary_dilation(body | joints, iterations=5) & teal]); ids = ids[ids > 0]
        new = body | joints | np.isin(lab, ids)
        if new.sum() == body.sum():
            break
        body = new
    m = ndi.binary_closing(body, iterations=2)
    holes = ndi.binary_fill_holes(m) & ~m                           # close pinholes only: larger holes are background seen between limbs
    hl, hn = ndi.label(holes)
    if hn:
        m = m | np.isin(hl, np.flatnonzero(ndi.sum(holes, hl, range(1, hn + 1)) < 220) + 1)
    m = ndi.binary_erosion(m, iterations=1)
    lab, n = ndi.label(m)
    m = lab == (int(np.argmax(ndi.sum(m, lab, range(1, n + 1)))) + 1)
    ys, xs = np.where(m)
    box = (max(0, xs.min() - 4), max(0, ys.min() - 4), min(w, xs.max() + 5), min(h, ys.max() + 5))
    alpha = np.clip(ndi.gaussian_filter(m.astype(np.float32), 0.9), 0, 1)
    out = im.copy(); out.putalpha(Image.fromarray((alpha * 255).astype(np.uint8)))
    return out.crop(box)


with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO, "-vf", f"fps={FPS}", "-q:v", "2", os.path.join(tmp, "f%03d.jpg")], check=True)
    figures = []
    for i, x, height in POSES:
        c = cut(os.path.join(tmp, f"f{i + 1:03d}.jpg"))
        figures.append((c.resize((round(c.width * height / c.height), height), Image.LANCZOS), x))

px = np.zeros((H, W, 3), np.float32)                                # dark ground, slightly lighter at the top, a pool of light at the feet
yy = np.linspace(0, 1, H)[:, None]
for ch, (top, bot) in enumerate(((20, 9), (22, 10), (25, 12))):
    px[..., ch] = top + (bot - top) * yy
xx = np.linspace(-1, 1, W)[None, :]; fy = (np.arange(H)[:, None] - BASE) / 300.0
px += (np.exp(-(xx ** 2) * 1.2 - (fy ** 2) * 2.2) * 16)[..., None] * np.array([0.8, 1.0, 1.15])
im = Image.fromarray(np.clip(px, 0, 255).astype(np.uint8))
shadow = Image.new("L", (W, H), 0); sd = ImageDraw.Draw(shadow)
for f, x in figures:
    sd.ellipse((x + f.width * .12, BASE - 26, x + f.width * .88, BASE + 30), fill=150)
im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, shadow.filter(ImageFilter.GaussianBlur(26)))
for f, x in figures:
    im.paste(f, (x, BASE - f.height), f)
im.save(OUT)
print("wrote", OUT)
