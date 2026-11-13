"""Build the project covers: one layout for every project.

Each cover is 1500x1000 (3:2), with 10px black gutters between its pictures. Four layouts:

    [main, tile, tile]                 a square main panel on the left, two square-ish tiles on the right
    ("full", image, crop)              one strong wide image across the whole frame
    ("grid", columns, [pictures])      equal cells, filled row by row (a set of variants, or sources too small for a big panel)
    ("rows", [(share, [pictures]), …]) rows of different heights, each split into equal cells

A picture is (file, crop box or None). No picture should be enlarged much beyond its own pixels:
run the script and read the "largest enlargement" it prints for each cover. Also written: cover-thumb (900x600),
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
    # two scenes, each as the renderer draws it and as the hash-grid cells it shades from; the robot pair is cut from a 1080p capture
    "world-space-restir": ("grid", 2, [
        (S("world-space-restir", "subway-ours"), (55, 110, 745, 570)),
        (S("world-space-restir", "subway-hash-grid"), (55, 108, 742, 566)),
        (C("restir-robot.jpg"), (120, 200, 1160, 893)),         # the mouse pointer is outside this crop
        (C("restir-robot-grid.jpg"), (420, 200, 1190, 713)),    # pointer painted out with the flat cell colours beside it
    ]),
    "cuda-path-tracer": [
        (C("pt-duck-room.png"), None),              # 1200x1200 render, 14,496 samples
        (S("cuda-path-tracer", "duck-doggy-duck"), None),
        (S("cuda-path-tracer", "dragon"), None),
    ],
    # three parts of one 3840x1959 screenshot (5,000 lights)
    "webgpu-clustered-shading": [
        (C("webgpu-4k.jpg"), (1180, 240, 2760, 1820)),
        (C("webgpu-4k.jpg"), (0, 760, 1000, 1760)),
        (C("webgpu-4k.jpg"), (2700, 700, 3700, 1700)),
    ],
    # the captures are small (400 to 800px), so six cells instead of one big panel
    "vulkan-grass-rendering": ("grid", 3, [
        (C("grass-field.png"), (170, 250, 610, 690)),
        (C("grass-close.png"), (150, 124, 490, 464)),
        (C("grass-dense.png"), (100, 110, 440, 450)),
        (C("grass-sparse.png"), (130, 80, 514, 464)),
        (C("grass-wire.png"), (40, 110, 330, 400)),
        (C("grass-distance.png"), (160, 130, 470, 440)),
    ]),
    "cuda-flocking": [
        (C("flock-cloud.png"), None),
        (C("flock-cube.png"), None),
        (C("flock-swarm.png"), None),
    ],
    "procedural-fireball": [
        (C("fireball-spiky.png"), None),
        (C("fireball-molten.png"), None),
        (C("fireball-smooth.png"), None),
    ],
    # the team's own title art, shown whole: the terrain only reads as a landscape when it is wide
    "mini-minecraft": ("full", C("minecraft-title.png"), (0, 40, 1611, 1114)),
    "monte-carlo-path-tracer": ("grid", 3, [
        (S("monte-carlo-path-tracer", "direct-lighting-cornell-two-lights"), (4, 4, 975, 975)),
        (S("monte-carlo-path-tracer", "specular-btdfs"), (4, 4, 972, 972)),
        (S("monte-carlo-path-tracer", "veach-mis"), (4, 4, 972, 972)),
        (S("monte-carlo-path-tracer", "dielectric-materials"), (4, 4, 975, 975)),
        (S("monte-carlo-path-tracer", "microfacet-brdfs"), (4, 4, 972, 972)),
        (S("monte-carlo-path-tracer", "direct-sample-spot-light"), (4, 4, 974, 974)),
    ]),
    # a drawing of the algorithm itself: kept elements joined to their compacted positions (cover-src/stream-compaction/diagram.py)
    "stream-compaction": ("full", C("stream-compaction-diagram.png"), None),
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
    # three scenes on top; under them one sphere going from mirror-smooth to fully rough
    "physically-based-shaders": ("rows", [
        (2, [(S("physically-based-shaders", "scene-skull"), (20, 97, 858, 935)),
             (S("physically-based-shaders", "scene-gun"), (20, 97, 858, 935))]),
        (1, [(S("physically-based-shaders", n), (230, 220, 620, 660)) for n in
             ("red-metal1-rough0", "red-metal1-rough025", "red-metal1-rough050", "red-metal1-rough075", "red-metal1-rough100")]),
    ]),
    # plants grown by the plugin's own L-system core from its bundled grammars (see cover-src/tree-plate/README.md)
    "tree-creator": ("full", C("tree-plate.png"), (0, 0, 3000, 2000)),
    # every shader on the same model, sixteen at once
    "glsl-shaders": ("grid", 4, [(S("glsl-shaders", n), (0, 78, 1456, 1048)) for n in (
        "matcap-blue-purple", "matcap-chrome", "matcap-orange-green", "matcap-outline",
        "matcap-pearl", "matcap-red-clay", "matcap-red-plastic", "surface-normals",
        "vertex-deformation", "bloom", "color-gradient", "blinn-phong",
        "greyscale", "custom-shader", "sobel", "worley-noise")]),
    # six close crops from the 1080p demo recordings, one or two per editor
    "animation-toolkit": ("grid", 3, [
        (C("anim-spline.jpg"), (650, 118, 1270, 738)),
        (C("anim-rotation.jpg"), (560, 130, 1400, 970)),
        (C("anim-ik.jpg"), (680, 290, 1180, 790)),
        (C("anim-cones.jpg"), (700, 340, 1300, 940)),
        (C("anim-fireworks.jpg"), (640, 118, 1140, 618)),
        (C("anim-burst.jpg"), (640, 118, 1200, 678)),
    ]),
    "maya-3d-scene-modeling": [
        (S("maya-3d-scene-modeling", "render-2"), (360, 0, 1440, 1080)),
        (S("maya-3d-scene-modeling", "render-3"), (380, 0, 1018, 638)),
        (S("maya-3d-scene-modeling", "render-1"), (0, 0, 1080, 1080)),
    ],
    # one photograph across the whole frame, like the series it comes from
    "virtual-subway": ("full", S("virtual-subway", "interior"), None),
    # five poses cut out of the finished animation's own frames (cover-src/mocap-poses/poses.py)
    "motion-capture": ("full", C("mocap-poses.png"), None),
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

def cells(n, total):
    """Edges of `n` equal cells across `total` pixels with G between them."""
    w = (total - (n - 1) * G) / n
    return [(round(i * (w + G)), round(i * (w + G) + w)) for i in range(n)]


def enlargement(spec, size):
    """How much a picture is blown up to fill `size` (1.0 = shown at its own pixels or smaller)."""
    if spec[0] in ("lineart", "split"):
        im, box = load(spec[1]), spec[2]
    else:
        im, box = load(spec[0]), spec[1]
    w, h = (box[2] - box[0], box[3] - box[1]) if box else im.size
    return max(size[0] / w, size[1] / h)


def main():
    man = json.load(open(MANP, encoding="utf-8"))
    only = sys.argv[3:]
    for proj, spec in COVERS.items():
        if only and proj not in only:
            continue
        placed = []                                # (picture, rectangle)
        if spec[0] == "full":                      # one image across the whole frame
            layout = "full"
            placed = [((spec[1], spec[2]), (0, 0, W, H))]
        elif spec[0] == "grid":                    # equal cells, row by row
            layout = "full"                        # the preview covers the whole frame
            cols, pics = spec[1], spec[2]
            rows = -(-len(pics) // cols)
            xs, ys = cells(cols, W), cells(rows, H)
            placed = [(p, (xs[i % cols][0], ys[i // cols][0], xs[i % cols][1], ys[i // cols][1])) for i, p in enumerate(pics)]
        elif spec[0] == "rows":                    # rows of different heights
            layout = "full"
            total = sum(share for share, _ in spec[1])
            y = 0.0
            for k, (share, pics) in enumerate(spec[1]):
                h = (H - (len(spec[1]) - 1) * G) * share / total
                xs = cells(len(pics), W)
                placed += [(p, (xs[i][0], round(y), xs[i][1], round(y + h))) for i, p in enumerate(pics)]
                y += h + G
        else:                                      # main panel and two tiles
            layout = "panels"
            placed = list(zip(spec, (MAIN, T1, T2)))
        canvas = Image.new("RGB", (W, H), (0, 0, 0))
        worst = 0
        for s, (x0, y0, x1, y1) in placed:
            canvas.paste(panel(s, (x1 - x0, y1 - y0)), (x0, y0))
            worst = max(worst, enlargement(s, (x1 - x0, y1 - y0)))
        d = os.path.join(IMG, proj)
        canvas.save(os.path.join(d, "cover.webp"), "WEBP", quality=92, method=6)
        th = canvas.resize((900, 600), Image.LANCZOS)
        th.save(os.path.join(d, "cover-thumb.webp"), "WEBP", quality=90, method=6)
        canvas.resize((360, 240), Image.LANCZOS).save(os.path.join(d, "cover-mini.webp"), "WEBP", quality=80, method=6)
        # a tiny, heavily blurred copy: the project page stretches it behind its header as ambient colour
        glow = canvas.resize((96, 64), Image.LANCZOS).filter(ImageFilter.GaussianBlur(9))
        glow.save(os.path.join(d, "glow.webp"), "WEBP", quality=70, method=6)
        man[f"{proj}/cover"] = {"w": W, "h": H, "tw": 900, "th": 600, "alpha": False, "layout": layout}
        print(f"{proj:26s} {round(os.path.getsize(os.path.join(d, 'cover.webp')) / 1024):4d} KB / "
              f"{round(os.path.getsize(os.path.join(d, 'cover-thumb.webp')) / 1024):3d} KB   largest enlargement x{worst:.2f}")
    json.dump(man, open(MANP, "w", encoding="utf-8"), indent=1, sort_keys=True)

main()
