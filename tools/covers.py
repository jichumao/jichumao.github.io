"""Build the project covers: one layout for every project.

Each cover is 1500x1000 (3:2). Most use a square main panel on the left and two square-ish
tiles on the right, separated by 10px black gutters; a project with one strong wide image
uses it across the whole frame instead ("full"). Also written: cover-thumb (900x600),
cover-mini (360x240, for the Previous / Next links) and glow (blurred, behind the page header). Sources are the project's own
renders, screenshots and video frames; crops are chosen by hand so the subject is
never cut by the card frame.

Panels that are not page images already (video frames, screenshots from the project
READMEs) live in tools/cover-src/.

usage, from the repository root:  python3 tools/covers.py . tools/manifest.json [project ...]
Then rebuild the pages with tools/build.py.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFilter

SITE, MANP = sys.argv[1], sys.argv[2]
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cover-src")
IMG = os.path.join(SITE, "assets", "img")
W, H, G = 1500, 1000, 10
MAIN = (0, 0, 1000, 1000)
T1 = (1010, 0, 1500, 495)
T2 = (1010, 505, 1500, 1000)

def C(name):
    return os.path.join(SRC, name)

def S(proj, name):
    return os.path.join(IMG, proj, name + ".webp")

def load(path):
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
        im = Image.alpha_composite(bg, im)
    return im.convert("RGB")

def fit(im, box, size):
    """Crop `box` (or the whole image), then centre-crop to the target ratio and resize."""
    if box:
        im = im.crop(box)
    tw, th = size
    w, h = im.size
    if w / h > tw / th:
        nw = round(h * tw / th); x = (w - nw) // 2; im = im.crop((x, 0, x + nw, h))
    else:
        nh = round(w * th / tw); y = (h - nh) // 2; im = im.crop((0, y, w, y + nh))
    up = tw / im.size[0]
    im = im.resize((tw, th), Image.LANCZOS)
    if up > 1.15:
        im = im.filter(ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=2))
    return im

def split(a, abox, b, bbox, size):
    """Diagonal split: `a` above the diagonal, `b` below it."""
    A, B = fit(a, abox, size), fit(b, bbox, size)
    w, h = size
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon([(w, 0), (w, h), (0, h)], fill=255)
    out = Image.composite(B, A, mask)
    ImageDraw.Draw(out).line([(w, 0), (0, h)], fill=(255, 255, 255), width=4)
    return out

PALETTE = [(89, 89, 89), (150, 150, 150), (75, 240, 160)]   # background, branches, leaf nodes

def lineart(im, box, size):
    """Enlarge a flat-colour diagram with clean edges: classify every pixel to the
    nearest palette colour, enlarge each colour mask smoothly, then take the winner."""
    import numpy as np
    a = np.asarray(im.crop(box)).astype(np.float32)
    pal = np.array(PALETTE, np.float32)
    lab = ((a[:, :, None, :] - pal[None, None, :, :]) ** 2).sum(-1).argmin(-1)
    lab[a.max(-1) < 60] = 1                      # dark outline ticks belong to the branches
    big = (size[0] * 2, size[1] * 2)
    masks = [np.asarray(Image.fromarray(((lab == k) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
                        .resize(big, Image.BICUBIC)).astype(np.float32) for k in range(len(PALETTE))]
    out = pal[np.stack(masks, -1).argmax(-1)].astype(np.uint8)
    return Image.fromarray(out).resize(size, Image.LANCZOS)

def panel(spec, size):
    if spec[0] == "lineart":
        return lineart(load(spec[1]), spec[2], size)
    if spec[0] == "split":
        _, a, abox, b, bbox = spec
        return split(load(a), abox, load(b), bbox, size)
    path, box = spec
    return fit(load(path), box, size)

COVERS = {
    "world-space-restir": [
        ("split", S("world-space-restir", "subway-ours"), (55, 0, 745, 690), S("world-space-restir", "subway-hash-grid"), (55, 0, 742, 687)),
        (C("restir-di.jpg"), (18, 0, 428, 410)),
        (S("world-space-restir", "sponza-hash-grid-split"), (67, 0, 946, 879)),
    ],
    "cuda-path-tracer": [
        (S("cuda-path-tracer", "duck-doggy-duck"), None),
        (S("cuda-path-tracer", "dragon"), None),
        (S("cuda-path-tracer", "shanghai-nights"), None),
    ],
    "webgpu-clustered-shading": [
        (S("webgpu-clustered-shading", "sponza-4k-5000-lights"), (490, 0, 1510, 1020)),
        (S("webgpu-clustered-shading", "gbuffer-normal"), (23, 0, 320, 297)),
        (S("webgpu-clustered-shading", "gbuffer-color"), (23, 0, 321, 298)),
    ],
    "vulkan-grass-rendering": [
        (C("grass-showcase.jpg"), (176, 263, 620, 707)),
        (C("grass-closeup.jpg"), (86, 0, 550, 464)),
        (C("grass-lod.jpg"), None),
    ],
    "cuda-flocking": [
        (C("flocking-swarm.png"), (40, 40, 600, 600)),
        (C("flocking-dense.png"), None),
        (C("flocking-red.png"), (60, 40, 580, 560)),
    ],
    "procedural-fireball": [
        (C("fireball-spiky.png"), None),
        (C("fireball-molten.png"), None),
        (C("fireball-smooth.png"), None),
    ],
    # the team's own title art, shown whole: the terrain only reads as a landscape when it is wide
    "mini-minecraft": ("full", C("minecraft-title.png"), (0, 40, 1611, 1114)),
    "monte-carlo-path-tracer": [
        (S("monte-carlo-path-tracer", "dielectric-materials"), (4, 4, 975, 975)),
        (S("monte-carlo-path-tracer", "veach-mis"), (4, 4, 972, 972)),
        (S("monte-carlo-path-tracer", "microfacet-brdfs"), (4, 4, 972, 972)),
    ],
    "stream-compaction": [
        (C("stream-compaction-bars.png"), None),
        (C("stream-compaction-chart-size.png"), None),
        (C("stream-compaction-chart-block.png"), None),
    ],
    "unity-stylization": [
        (C("stylization-scene.png"), (215, 0, 685, 470)),
        (S("unity-stylization", "mode-2"), None),
        (S("unity-stylization", "mode-3"), None),
    ],
    "houdini-procedural": [
        (S("houdini-procedural", "jellyfish"), None),
        (S("houdini-procedural", "veins"), None),
        (S("houdini-procedural", "building-1"), None),
    ],
    "physically-based-shaders": [
        (S("physically-based-shaders", "scene-skull"), (71, 97, 909, 935)),
        (S("physically-based-shaders", "scene-gun"), (20, 97, 858, 935)),
        (S("physically-based-shaders", "displacement-100"), (61, 97, 899, 935)),
    ],
    "tree-creator": [
        ("lineart", C("tree-diagram.jpg"), (310, 45, 675, 410)),
        (C("tree-maya.jpg"), (670, 300, 1090, 720)),
        (C("tree-houdini.jpg"), (368, 509, 688, 829)),
    ],
    "glsl-shaders": [
        (S("glsl-shaders", "matcap-chrome"), (166, 0, 1292, 1126)),
        (S("glsl-shaders", "sobel"), (166, 0, 1292, 1126)),
        (S("glsl-shaders", "surface-normals"), (166, 0, 1289, 1123)),
    ],
    "animation-toolkit": [
        (C("animation-behavior.jpg"), (392, 78, 964, 650)),
        (C("animation-curve.jpg"), (560, 150, 1010, 600)),
        (C("animation-particle.jpg"), (430, 78, 860, 508)),
    ],
    "maya-3d-scene-modeling": [
        (S("maya-3d-scene-modeling", "render-2"), (360, 0, 1440, 1080)),
        (S("maya-3d-scene-modeling", "render-3"), (380, 0, 1018, 638)),
        (S("maya-3d-scene-modeling", "render-1"), (0, 0, 1080, 1080)),
    ],
    "motion-capture": [
        (C("mocap-kick.jpg"), (285, 285, 925, 925)),
        (C("mocap-session.jpg"), (654, 150, 1274, 770)),
        (C("mocap-point.jpg"), (560, 285, 1200, 925)),
    ],
    "houdini-fireworks": [
        (C("fireworks-normal.jpg"), (500, 220, 1360, 1080)),
        (C("fireworks-repulsive.jpg"), (520, 330, 1270, 1080)),
        (C("fireworks-interparticle.jpg"), (735, 300, 1335, 900)),
    ],
    "gem-match-game": [
        (C("gem-start-screen.png"), (419, 27, 987, 595)),
        (C("gem-start-screen.png"), (12, 45, 382, 415)),
        (C("gem-midgame.jpg"), (790, 100, 1090, 400)),
    ],
}

def main():
    man = json.load(open(MANP, encoding="utf-8"))
    only = sys.argv[3:]
    for proj, spec in COVERS.items():
        if only and proj not in only:
            continue
        if spec[0] == "full":                      # one image across the whole frame
            layout = "full"
            canvas = fit(load(spec[1]), spec[2], (W, H))
        else:                                      # main panel and two tiles
            layout = "panels"
            m, t1, t2 = spec
            canvas = Image.new("RGB", (W, H), (0, 0, 0))
            for s, rect in ((m, MAIN), (t1, T1), (t2, T2)):
                x0, y0, x1, y1 = rect
                canvas.paste(panel(s, (x1 - x0, y1 - y0)), (x0, y0))
        d = os.path.join(IMG, proj)
        canvas.save(os.path.join(d, "cover.webp"), "WEBP", quality=88, method=6)
        th = canvas.resize((900, 600), Image.LANCZOS)
        th.save(os.path.join(d, "cover-thumb.webp"), "WEBP", quality=84, method=6)
        canvas.resize((360, 240), Image.LANCZOS).save(os.path.join(d, "cover-mini.webp"), "WEBP", quality=80, method=6)
        # a tiny, heavily blurred copy: the project page stretches it behind its header as ambient colour
        glow = canvas.resize((96, 64), Image.LANCZOS).filter(ImageFilter.GaussianBlur(9))
        glow.save(os.path.join(d, "glow.webp"), "WEBP", quality=70, method=6)
        man[f"{proj}/cover"] = {"w": W, "h": H, "tw": 900, "th": 600, "alpha": False, "layout": layout}
        print(proj, round(os.path.getsize(os.path.join(d, "cover.webp")) / 1024), "KB /",
              round(os.path.getsize(os.path.join(d, "cover-thumb.webp")) / 1024), "KB")
    json.dump(man, open(MANP, "w", encoding="utf-8"), indent=1, sort_keys=True)

main()
