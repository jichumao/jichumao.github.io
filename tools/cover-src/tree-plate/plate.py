"""Draws the Tree Creator cover: plants produced by the plugin's own L-system core
(LSystem.cpp, built by build.sh) from its bundled grammars, as an SVG plate.
usage: python3 plate.py <plants dir> <out dir>"""
import json, math, os, subprocess, sys
PLANTS, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.abspath(os.path.join(OUT, "..", "..", "assets", "fonts", "jetbrains-mono-latin-400-normal.woff2"))

def grow(name, angle, n):
    out = subprocess.run([os.path.join(HERE, "driver"), os.path.join(PLANTS, name + ".txt"), str(angle), "1", str(n)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)

def rule(name):
    lines = [l.strip() for l in open(os.path.join(PLANTS, name + ".txt")) if l.strip()]
    return [l.replace("->", " → ").replace("\\\\", "\\").replace("-", "−") for l in lines[1:]]

def layout(d, turn=0.0):
    """2D points (u right, v up), stroke weight per branch from the size of the subtree it carries."""
    c, s = math.cos(turn), math.sin(turn)
    P = lambda x, y, z: (y * c - x * s, z)
    segs = [(P(*b[:3]), P(*b[3:]), tuple(round(v, 3) for v in b[:3]), tuple(round(v, 3) for v in b[3:])) for b in d["branches"]]
    end_at = {}; parent = [-1] * len(segs)
    for i, (_, _, a, b) in enumerate(segs):
        parent[i] = end_at.get(a, -1); end_at[b] = i
    size = [1] * len(segs)
    for i in range(len(segs) - 1, -1, -1):
        if parent[i] >= 0: size[parent[i]] += size[i]
    return segs, size, [(P(*f[:3]), f[3]) for f in d["flowers"]]

def plant_svg(d, box, turn=0.0, flower_r=None, base=1.0):
    x0, y0, w, h = box
    segs, size, dots = layout(d, turn)
    us = [p[0] for s in segs for p in s[:2]]; vs = [p[1] for s in segs for p in s[:2]]
    k = min(w / (max(us) - min(us) + 1e-9), h / (max(vs) - min(vs) + 1e-9))
    cx = (max(us) + min(us)) / 2
    if flower_r is None: flower_r = max(1.5, min(3.4, 1.15 * k))
    X = lambda u: x0 + w / 2 + (u - cx) * k
    Y = lambda v: y0 + h - (v - min(vs)) * k
    top = max(size)
    classes = {}
    for (a, b, _, _), n in zip(segs, size):
        t = math.log(n) / math.log(top) if top > 1 else 0
        q = round(t * 14)
        classes.setdefault(q, []).append(f"M{X(a[0]):.1f} {Y(a[1]):.1f}L{X(b[0]):.1f} {Y(b[1]):.1f}")
    out = []
    for q in sorted(classes):
        t = q / 14
        width = base * (0.9 + 9.0 * t ** 1.6)
        r, g, b_ = (round(126 + (236 - 126) * t), round(196 + (229 - 196) * t), round(150 + (214 - 150) * t))   # twig green to trunk cream
        out.append(f'<path d="{"".join(classes[q])}" stroke="rgb({r},{g},{b_})" stroke-width="{width:.2f}" stroke-opacity="{0.55 + 0.45 * t:.2f}"/>')
    buds = "".join(f'<circle cx="{X(p[0]):.1f}" cy="{Y(p[1]):.1f}" r="{flower_r * .5:.1f}"/>' for p, sym in dots if sym != "*")
    flowers = "".join(f'<circle cx="{X(p[0]):.1f}" cy="{Y(p[1]):.1f}" r="{flower_r:.1f}"/>' for p, sym in dots if sym == "*")
    return (f'<g fill="none" stroke-linecap="round">{"".join(out)}</g>'
            + (f'<g fill="#bfe3b4" fill-opacity=".8">{buds}</g>' if buds else "")
            + (f'<g fill="#db4f3d" fill-opacity=".92">{flowers}</g>' if flowers else ""))

def page(body, W, H):
    return f"""<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:"JBM";src:url("file://{FONT}") format("woff2")}}
html,body{{margin:0;background:#000}} svg{{display:block}} text{{font:400 16px "JBM",monospace;fill:#a6a6a6}} .d{{fill:#6b6b6b}}
</style><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><radialGradient id="g" cx="50%" cy="78%" r="75%"><stop offset="0" stop-color="#15201a"/><stop offset="1" stop-color="#000"/></radialGradient></defs>
<rect width="{W}" height="{H}" fill="url(#g)"/>{body}</svg>"""

SPECS = [("simple1", 25.7, 4), ("simple5", 25.7, 6), ("simple6", 22.5, 5), ("flower1", 22.5, 3), ("flower2", 22.5, 5)]

def plate():
    W, H = 1500, 1000
    col = W / len(SPECS); body = [f'<line x1="60" x2="{W - 60}" y1="840" y2="840" stroke="#2c3a31" stroke-width="1.5"/>']
    for i, (name, angle, n) in enumerate(SPECS):
        d = grow(name, angle, n)
        body.append(plant_svg(d, (i * col + 14, 64, col - 28, 774)))
        cx = i * col + col / 2
        for j, line in enumerate(rule(name)):
            body.append(f'<text x="{cx:.0f}" y="{880 + j * 26}" text-anchor="middle">{line}</text>')
        body.append(f'<text class="d" x="{cx:.0f}" y="{880 + len(rule(name)) * 26}" text-anchor="middle">δ {angle}°  n {n}</text>')
    open(os.path.join(OUT, "tree-plate.html"), "w", encoding="utf-8").write(page("".join(body), W, H))

def growth(name="simple6", angle=22.5, steps=(1, 2, 3, 4, 5, 6)):
    W, H = 900, 600
    for n in steps:
        d = grow(name, angle, n)
        body = f'<line x1="40" x2="{W - 40}" y1="548" y2="548" stroke="#2c3a31" stroke-width="1.5"/>' + plant_svg(d, (60, 28, 780, 516), base=max(0.6, 1.7 - 0.18 * n))
        open(os.path.join(OUT, f"tree-grow-{n}.html"), "w", encoding="utf-8").write(page(body, W, H))

plate(); growth()
print("wrote", sorted(f for f in os.listdir(OUT) if f.startswith("tree-") and f.endswith(".html")))
