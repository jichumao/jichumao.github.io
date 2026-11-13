"""Build the short looping previews that play on the project cards.

Each preview is a silent 600x600 MP4 that covers the main (left) panel of the cover
(900x600 over the whole frame for a full-frame cover).
Projects with a video use a few seconds of it; the others get a cross-fading slideshow
of their own renders, starting from the cover's main panel so the hover does not jump.

usage, from the repository root:  python3 tools/previews.py . [project ...]
Needs ffmpeg and Pillow.
"""
import os, shutil, subprocess, sys, tempfile
from PIL import Image

SITE = sys.argv[1]
ONLY = sys.argv[2:]
IMG = os.path.join(SITE, "assets", "img")
VID = os.path.join(SITE, "assets", "video")
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cover-src")
SIZE, FPS = 600, 24
ENC = ["-an", "-c:v", "libx264", "-crf", "30", "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]

S = lambda proj, name: os.path.join(IMG, proj, name + ".webp")
V = lambda name: os.path.join(VID, name + ".mp4")
C = lambda name: os.path.join(SRC, name)

def from_video(out, src, crop, start, dur, crf=None, full=False):
    """`crf` overrides the quality for footage that compresses badly (dense particles).
    `full`: a 3:2 crop for a full-frame cover (900x600) instead of a square one."""
    x, y, w, h = crop
    vf = f"crop={w}:{h}:{x}:{y},scale={900 if full else SIZE}:{600 if full else SIZE}:flags=lanczos,fps={FPS}"
    enc = [str(crf) if a == "30" and crf else a for a in ENC]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-t", str(dur), "-i", src, "-vf", vf, *enc, out], check=True)

def frame(path, box, size):
    """Crop `box`, centre-crop to the frame's shape, resize."""
    im = Image.open(path).convert("RGB")
    if box:
        im = im.crop(box)
    w, h = im.size
    tw, th = size
    if w / h > tw / th:
        nw = round(h * tw / th); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = round(w * th / tw); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im.resize(size, Image.LANCZOS)

def from_stills(out, proj, stills, hold=1.1, fade=0.45, full=False):
    """Slideshow: the cover first (its main panel, or all of it for a full-frame cover),
    then the stills, cross-fading back to the start."""
    size = (900, 600) if full else (SIZE, SIZE)
    cover = Image.open(os.path.join(IMG, proj, "cover.webp")).convert("RGB")
    cover = (cover if full else cover.crop((0, 0, 1000, 1000))).resize(size, Image.LANCZOS)
    frames = [cover] + [frame(p, b, size) for p, b in stills]
    tmp = tempfile.mkdtemp()
    n = 0
    for i, im in enumerate(frames):
        nxt = frames[(i + 1) % len(frames)]
        for _ in range(round(hold * FPS)):
            im.save(os.path.join(tmp, f"{n:05d}.jpg"), quality=92); n += 1
        k = round(fade * FPS)
        for j in range(1, k + 1):
            Image.blend(im, nxt, j / (k + 1)).save(os.path.join(tmp, f"{n:05d}.jpg"), quality=92); n += 1
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", os.path.join(tmp, "%05d.jpg"), *ENC, out], check=True)
    shutil.rmtree(tmp)

VP = (53, 81, 751, 779)       # viewport of the 1130x804 PBR screenshots
VPL = (71, 97, 909, 935)      # viewport of the 1356x964 PBR screenshots
GL = (166, 0, 1292, 1126)     # square crop of the GLSL shader screenshots

PREVIEWS = {
    "world-space-restir": ("video-full", V("restir-hash-grid"), (0, 94, 960, 640), 3, 7.0),      # the robot as rendered, then its hash-grid cells
    "cuda-path-tracer": ("stills", [(S("cuda-path-tracer", n), None) for n in ("duck-doggy-duck", "dragon", "shanghai-nights", "stone-cat")]),
    "webgpu-clustered-shading": ("video", V("webgpu-moving-lights"), (67, 0, 488, 488), 12.5, 5.5),
    "vulkan-grass-rendering": ("video-full", V("grass-showcase"), (0, 236, 796, 530), 0, 5.4),
    "cuda-flocking": ("video", V("flocking-dense"), (0, 0, 640, 640), 0.3, 4.5, 36),
    "stream-compaction": ("stills-full", [(C("stream-compaction-stage-1.png"), None), (C("stream-compaction-stage-2.png"), None)]),   # the diagram drawing itself
    "unity-stylization": ("video", V("stylization-2"), (215, 0, 470, 470), 0, 6.0),
    "houdini-procedural": ("video", V("jellyfish"), (0, 0, 800, 800), 0, 2.3),
    "physically-based-shaders": ("stills-full", [(S("physically-based-shaders", "scene-skull"), (20, 137, 858, 696)), (S("physically-based-shaders", "scene-gun"), (20, 137, 858, 696)),
                                                 (S("physically-based-shaders", "displacement-100"), (61, 137, 899, 696))]
                                 + [(S("physically-based-shaders", n), (53, 148, 751, 613)) for n in ("red-metal1-rough0", "red-metal1-rough050", "red-metal1-rough100")]),
    "mini-minecraft": ("stills-full", [(S("mini-minecraft", n), None) for n in ("biome-grassland", "biome-desert", "biome-snow", "biome-mountain")]),
    "monte-carlo-path-tracer": ("stills-full", [(S("monte-carlo-path-tracer", n), (4, 164, 972, 810)) for n in
                                                ("direct-lighting-cornell-two-lights", "specular-btdfs", "dielectric-materials", "microfacet-brdfs", "veach-mis")]),
    "glsl-shaders": ("stills-full", [(S("glsl-shaders", n), (0, 78, 1456, 1048)) for n in ("matcap-chrome", "matcap-orange-green", "surface-normals", "color-gradient", "bloom", "sobel", "worley-noise")]),
    "procedural-fireball": ("video", V("fireball"), (0, 0, 800, 800), 0, 5.9),
    "tree-creator": ("stills-full", [(C(f"tree-grow-{n}.png"), None) for n in range(1, 7)]),   # one plant, iterations 1 to 6
    "animation-toolkit": ("video-full", V("animation-behavior"), (100, 0, 1080, 720), 1, 7.0),
    "gem-match-game": ("video", V("gem-match-game"), (788, 98, 582, 582), 12, 6.0),
    "maya-3d-scene-modeling": ("stills", [(S("maya-3d-scene-modeling", "render-1"), (0, 0, 1080, 1080)), (S("maya-3d-scene-modeling", "render-3"), (380, 0, 1018, 638)),
                                          (S("maya-3d-scene-modeling", "render-4"), None), (S("maya-3d-scene-modeling", "render-5"), None)]),
    "virtual-subway": ("stills-full", [(S("virtual-subway", n), None) for n in ("side", "doors", "front", "bench", "end-door", "window")]),
    "motion-capture": ("video-full", V("motion-capture"), (276, 84, 1368, 912), 2, 6.0),
    "houdini-fireworks": ("video", V("houdini-fireworks"), (500, 220, 860, 860), 0.6, 4.4),
}

for proj, spec in PREVIEWS.items():
    if ONLY and proj not in ONLY:
        continue
    out = os.path.join(VID, f"preview-{proj}.mp4")
    if spec[0] in ("video", "video-full"):
        from_video(out, *spec[1:], full=(spec[0] == "video-full"))
    else:
        from_stills(out, proj, spec[1], full=(spec[0] == "stills-full"))
    print(proj, round(os.path.getsize(out) / 1024), "KB")
