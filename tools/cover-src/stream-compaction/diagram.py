"""Cover for the CUDA Stream Compaction project: a drawing of what the code does.

The top row is an array in which some elements are to be dropped (outlined cells); the bottom row is
the compacted array, every kept element moved to the front in its original order. Each curve joins a
kept element to its new index, which is exactly what the scan computes: the number of kept elements
before it.

    python3 tools/cover-src/stream-compaction/diagram.py tools/cover-src

writes stream-compaction-diagram.png (the cover) and stream-compaction-stage-1.png / -2.png (the same
drawing with only the input, then with half of the curves, for the hover preview). Needs Pillow.
"""
import os, random, sys
from PIL import Image, ImageDraw

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
W, H = 3000, 2000
N, CELL, GAP = 32, 60, 28
PITCH = CELL + GAP
X0 = (W - (N * PITCH - GAP)) // 2
TOP, BOT = 360, 1580
ACCENT, GROUND = (219, 79, 61), (10, 10, 10)

random.seed(565)
keep = [random.random() < 0.44 for _ in range(N)]
keep[0], keep[1], keep[N - 1] = False, True, True          # so the first curve leans left and the last spans the picture
index, k = [], 0
for flag in keep:                                           # exclusive scan of the keep flags = each kept element's new index
    index.append(k); k += flag


def bezier(p0, p1, p2, p3, steps=90):
    pts = []
    for i in range(steps + 1):
        t = i / steps; u = 1 - t
        pts.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return pts


def draw(curves=1.0, output=True):
    """`curves`: the fraction of the curves drawn, left to right."""
    im = Image.new("RGB", (W, H), GROUND)
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lines)
    shown = round(k * curves)
    for i in range(N):
        if keep[i] and index[i] < shown:
            a = (X0 + i * PITCH + CELL / 2, TOP + CELL + 16)
            b = (X0 + index[i] * PITCH + CELL / 2, BOT - 16)
            mid = (b[1] - a[1]) * 0.52
            ld.line(bezier(a, (a[0], a[1] + mid), (b[0], b[1] - mid), b), fill=ACCENT + (205,), width=9, joint="curve")
    im.paste(lines, (0, 0), lines)
    d = ImageDraw.Draw(im)
    for i in range(N):
        x = X0 + i * PITCH
        if keep[i]:
            d.rounded_rectangle((x, TOP, x + CELL, TOP + CELL), 12, fill=(244, 244, 244))
        else:
            d.rounded_rectangle((x, TOP, x + CELL, TOP + CELL), 12, outline=(74, 74, 74), width=4)
        if output and i < shown:
            d.rounded_rectangle((x, BOT, x + CELL, BOT + CELL), 12, fill=ACCENT)
        else:
            d.rounded_rectangle((x, BOT, x + CELL, BOT + CELL), 12, outline=(40, 40, 40), width=4)
    return im


draw().save(os.path.join(OUT, "stream-compaction-diagram.png"))
draw(curves=0, output=False).save(os.path.join(OUT, "stream-compaction-stage-1.png"))
draw(curves=0.5).save(os.path.join(OUT, "stream-compaction-stage-2.png"))
print("kept", k, "of", N)
