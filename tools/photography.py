"""Builds the photography section (photography/).

Run through tools/build.py, or on its own from the repo root:
    python3 tools/photography.py .

Everything editable is in this file: SERIES (order, titles, rows) and ALT
(one description per photograph). tools/photos.json holds what was measured
from the files (pixel sizes, placeholder colour, camera settings).
The stylesheet and the viewer are hand-written: photography/assets/.
"""
import html, json, os, sys

SITE = "https://jichu.art"
EMAIL = "maojichu@gmail.com"
E = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "photos.json")))

# One entry per series, in the order they appear on the index page.
#   rows   the sequence. Each inner list is one row on a wide screen; on a
#          phone held upright the same order runs top to bottom.
#   cover  the photograph used for the tile on the index page.
#   focus  optional. Where to hold the cover when a tile has to crop it
#          ("More series" at the foot of a series page), as a CSS position.
SERIES = [
    dict(slug="above-the-fog", title="Above the Fog", where="California", when="July 2025",
         note="An evening on a ridge trail while the marine layer filled the valleys below.",
         rows=[[4], [3, 1], [5], [2, 0, 13], [12], [16, 17]], cover=4),
    dict(slug="macau", title="Macau", where="", when="January 2026",
         note="An afternoon in the old town, then the casinos after dark.",
         rows=[[242, 241], [246, 244, 247], [249, 255, 251], [252]], cover=247, focus="50% 62%"),
    dict(slug="salt", title="Salt", where="Alviso, California", when="June 2025",
         note="Salt ponds at the southern end of San Francisco Bay.",
         rows=[[58], [57, 54], [61], [62, 52, 64], [63, 53]], cover=58),
    dict(slug="subway", title="Subway", where="", when="April 2025",
         note="One subway car in black and white, on a 50 mm lens.",
         rows=[[398], [399, 397], [391], [394, 396], [392, 395], [400]], cover=391),
    dict(slug="rose", title="Rose", where="", when="",
         note="A portrait session in a café.",
         rows=[[127, 136], [129, 132, 137], [145, 146]], cover=132, focus="50% 30%"),
    dict(slug="guangzhou", title="Guangzhou", where="", when="January 2026",
         note="Museum halls by day, the Pearl River after dark.",
         rows=[[214, 216], [213, 215], [219, 308, 220], [221]], cover=214, focus="50% 62%"),
    dict(slug="pacific", title="Pacific", where="San Francisco", when="July 2025",
         note="The western edge of the city on a clear afternoon.",
         rows=[[90], [95, 96], [101, 97], [91], [98, 104], [87, 88]], cover=90),
    dict(slug="dry-hills", title="Dry Hills", where="California", when="July 2025",
         note="Sunset from the grazing land above the valley.",
         rows=[[71], [77, 79], [76], [80]], cover=80),
    dict(slug="rooftop", title="Rooftop", where="Chongqing", when="June 2026",
         note="LED glasses and two light sticks, high above the city at night.",
         rows=[[18, 20, 22], [25, 21]], cover=21, focus="50% 55%"),
    dict(slug="fourth-of-july", title="Fourth of July", where="San Francisco Bay", when="July 2025",
         note="From dusk to the fireworks, seen from across the bay.",
         rows=[[114, 115], [116], [118], [120, 122], [126, 124]], cover=120),
    dict(slug="tea-hills", title="Tea Hills", where="Zhejiang", when="December 2025",
         note="A tea estate built around a château-style hotel.",
         rows=[[200, 201], [202, 198], [206, 205]], cover=206),
    dict(slug="evening-walk", title="Evening Walk", where="", when="May 2025",
         note="Portraits in a park, from the last daylight until the lamps came on.",
         rows=[[43, 38, 40], [46, 49, 51]], cover=38, focus="50% 30%"),
    dict(slug="zhuhai", title="Zhuhai", where="", when="January 2026",
         note="The opera house on the water, from late afternoon into the night.",
         rows=[[228, 222], [230], [232], [240], [256, 238]], cover=232),
    dict(slug="off-season", title="Off-season", where="Atlantic City and Cape May, New Jersey", when="March 2025",
         note="The Jersey Shore before the summer crowds.",
         rows=[[261], [373, 372, 368], [289], [285], [288]], cover=261),
    dict(slug="pennsylvania", title="Pennsylvania", where="", when="October 2025",
         note="A gorge overlook, an orchard and a small town in autumn.",
         rows=[[187], [181, 182, 174], [188, 194, 189], [190, 193]], cover=194, focus="50% 28%"),
]

# Rows of series tiles on the index page, by slug.
# The first series has no tile: the opening picture is its link.
HOME_ROWS = [
    ["macau", "salt"],
    ["subway", "rose"],
    ["guangzhou", "pacific"],
    ["dry-hills", "rooftop"],
    ["fourth-of-july", "tea-hills"],
    ["evening-walk", "zhuhai"],
    ["off-season", "pennsylvania"],
]
# Opening picture of the index page: one photograph for wide screens, one for upright phones.
HERO = dict(wide=16, tall=1, series="above-the-fog")

# One plain description per photograph (used as alt text).
ALT = {
    # Above the Fog
    4: "Golden grass on a ridge above forested hills, with a sea of fog reaching the horizon.",
    3: "A dirt trail curving up a grassy ridge toward the low sun.",
    1: "Dry grass stalks in front of a bank of fog.",
    5: "Fog pouring through forested valleys under a pale evening sky.",
    2: "The sun above a dark ridge and backlit golden grass.",
    0: "Tall grass in silhouette against the setting sun.",
    13: "The sun setting over fog-filled valleys, seen across a field of red grass.",
    12: "An orange sunset over the fog, a dark tree line on the left.",
    16: "Fog rolling over dark ridges under a pink and blue sky after sunset.",
    17: "A half moon in a blue sky above treetops.",
    # Macau
    242: "The Grand Lisboa tower rising between old apartment blocks.",
    241: "A yellow colonial building with green shutters and palm trees, towers behind it.",
    246: "Pedestrians crossing in front of the Casino Lisboa's neon entrance.",
    244: "Looking up at the patterned facade of a tower against a pink sky.",
    247: "A crowded street at dusk under Chinese pharmacy and shop signs.",
    249: "A gondola on an indoor canal lined with Venetian-style facades under a painted sky.",
    255: "A lit carousel under a dome.",
    251: "A glowing white cube building beside a replica clock tower at night.",
    252: "A hotel outlined in gold light at night, a crowd in the plaza below.",
    # Salt
    58: "A dark red salt pond edged with white salt crust; a few people walk along the far shore.",
    57: "A person standing at the edge of a shallow pond, mirrored in the water beside a lump of salt.",
    54: "Close view of red brine with salt crystals forming under the surface.",
    61: "Upside-down reflections of two people in still red water.",
    62: "A man standing on a spit of salt under a high sun, reflected in the pond.",
    52: "Tan hills beyond a blurred white field of salt.",
    64: "A boardwalk with steel railings leading to a small house-shaped frame.",
    63: "A house-shaped wooden frame on a grassy bank, mirrored in a pond.",
    53: "An adult and two children at the water's edge in silhouette, with their reflections.",
    # Rose
    127: "A woman in a black slip dress sits on a cream sofa holding a red rose, lit from the side.",
    136: "She reclines on the sofa in a dark room, the rose held up to one eye.",
    129: "She leans on the arm of the sofa, looking down at the rose in her hand.",
    132: "She holds the rose to her lips and looks at the camera.",
    137: "She leans back with the rose raised beside her face, eyes lowered.",
    145: "Close portrait, her eyes turned to the side, shelves behind her.",
    146: "Close portrait from above; she looks down with a slight smile.",
    # Subway
    398: "The side of a subway car: the number 8805 and a flag decal beside a window.",
    399: "The car's double doors, with stickers reading 'Do not hold doors'.",
    397: "The end of the car, with its headlights and end door.",
    391: "The empty interior of the car, benches along both sides.",
    394: "A bench and a framed poster seen across the aisle.",
    396: "The door at the end of the car, graffiti on the wall beside it.",
    392: "The aisle seen from floor level.",
    395: "Ceiling lights and advertisements blurred and mirrored in a window.",
    400: "Looking into the car through a window; the sign above the seats reads 'Emergency'.",
    # Guangzhou
    214: "A visitor in silhouette reading a lit exhibition wall in a museum.",
    216: "A dark atrium opening onto a tall window glowing with warm light.",
    213: "Looking straight up at a circular glass dome with a spiral lattice.",
    215: "A white grand piano on a round black stage, seen from directly above.",
    219: "A white sculpture of a seated figure beneath a glass lattice roof.",
    308: "The Canton Tower at dusk behind a bed of pink flowers.",
    220: "A lit pagoda at night beyond an empty plaza.",
    221: "The Guangzhou skyline and an arched bridge at night, boat lights streaking across the river.",
    # Pacific
    90: "A person in a dark coat stands at the water's edge facing rows of breaking waves.",
    95: "A gull standing in the shallows as a wave breaks behind it.",
    96: "A dog running along the wet sand with a ball in its mouth, sea stacks behind.",
    101: "A cormorant perched on a ruined wall while a person walks along it, the sea glittering behind.",
    97: "A lone figure far off on an empty beach.",
    91: "The ruins of a seaside bath below green bluffs, with the open ocean beyond.",
    98: "An empty road curving down toward the ocean past a cypress tree.",
    104: "The Golden Gate Bridge seen from a sandy beach.",
    87: "A man carrying two large blue bags crosses a sunny street lined with palm trees.",
    88: "A tiled dome on a white building, framed by tree branches.",
    # Fourth of July
    114: "A causeway and an island at sunset, the sky fading from orange to blue.",
    115: "The San Francisco skyline at dusk across the bay, trees in silhouette below.",
    116: "The white tower of the Bay Bridge at night, light trails along the road.",
    118: "The downtown skyline lit up at night, seen across the water.",
    120: "Gold fireworks bursting over the bay above red smoke.",
    122: "Two blue fireworks over dark water.",
    126: "A large gold firework with smaller bursts beneath it.",
    124: "Red fireworks trailing long sparks.",
    # Dry Hills
    71: "Rolling golden hills in low evening light, long shadows in the folds.",
    77: "A person in silhouette watching the sun set behind a hill.",
    79: "The sun touching a dark ridge above a fenced hillside road.",
    76: "People in silhouette on a hilltop watching the sunset.",
    80: "A black cow seen from behind, looking out over a valley of city lights at dusk.",
    # Rooftop
    18: "A man in LED glasses stands on a rooftop stairway at night, small against neon-lit towers.",
    20: "He leans on the stair rail holding two light sticks, his glasses glowing.",
    22: "Seen from above in profile, he crouches by the railing with a red light stick, the city spread out below.",
    25: "He stands with the light sticks crossed over his chest, lit red by them.",
    21: "With his back to the camera he raises a red light stick toward the skyline.",
    # Evening Walk
    43: "A woman in a grey cap and sleeveless top stands on a lawn and looks at the camera, a pagoda behind the trees.",
    38: "Close profile: the peak of her cap hides her eyes.",
    40: "Seen from behind, she tilts her head back with her eyes closed.",
    46: "She sits on a wooden bench in profile, one arm resting on her knee.",
    49: "She stands on a path at dusk holding the strap of her bag, looking at the camera.",
    51: "She looks back from a winding path as the park lamps come on.",
    # Zhuhai
    228: "Two people standing on an empty beach under a wide turquoise sky.",
    222: "A white lighthouse at the end of a pier, seen from the beach.",
    230: "A shell-shaped opera house and a red pavilion across the water, framed by an opening in a stone wall.",
    232: "The two shells of the opera house at dusk above a paved plaza.",
    240: "The opera house shells lit amber at night.",
    256: "Two people walking toward a lit lighthouse at night.",
    238: "The moon and its reflection on dark water.",
    # Off-season
    261: "An empty boardwalk and beach; a kite is caught on a line of string lights.",
    373: "A narrow lane between pastel-painted shopfronts.",
    372: "Two shop windows full of soft toys in a red brick wall, under black awnings.",
    368: "Mannequins in pastel tracksuits outside a shop window lettered 'Homemade fudge' and 'Hot roasted nuts'.",
    289: "A row of benches on the sand in low sun; two people sit on one, facing the sea.",
    285: "A lighthouse seen through tall reeds under a clouded sky.",
    288: "The sun setting over the sea beside a half-sunken wreck; a person stands on the jetty.",
    # Pennsylvania
    187: "Two people sit on a rock ledge above a river gorge in autumn colour.",
    181: "Red apples on a branch against a blue sky.",
    182: "Fallen apples lying in rows beneath the orchard trees.",
    174: "An old blue pickup truck loaded with pumpkins, beside a giant pumpkin and chrysanthemums.",
    188: "A crowded main street leading up to a stone church, autumn hills behind.",
    194: "A street musician in a red jacket and sunglasses plays guitar on a bench.",
    189: "A street musician in a bandana plays guitar by a wooden fence, his case open beside him.",
    190: "Framed ink portraits above a shelf of potted cacti and succulents in a shop.",
    193: "Two white ornamental pumpkins with black metal leaves among warm fairy lights.",
    # Tea Hills
    200: "Terraced tea bushes and bare white-trunked trees below a glass dome, mountains behind.",
    201: "The glass dome above rounded rows of tea bushes.",
    202: "A château-style hotel reflected in a pond, framed by a branch of red leaves.",
    198: "A road with a painted arrow curving past a pond and a pruned pine.",
    206: "The hotel lit at night, mirrored in still water.",
    205: "An outdoor Christmas tree wrapped in lights against a dark sky.",
}

ABOUT = [
    "I’m Jichu Mao. I work on real-time rendering and GPU performance, and I photograph on the side: "
    "landscapes, cities after dark, and now and then a portrait.",
    "These pictures were made in 2025 and 2026 in California, on the East Coast of the United States and in "
    "China, on a Sony α7C II and a Canon EOS 5D Mark IV.",
]

BY_SLUG = {s["slug"]: s for s in SERIES}


def ph(n):
    return P[f"{n:03d}"]


def ar(n):
    return ph(n)["w"] / ph(n)["h"]


def ids(s):
    return [n for row in s["rows"] for n in row]


def meta_line(s):
    return ", ".join(x for x in (s["where"], s["when"]) if x)


def count(s):
    return f'{len(ids(s))} photographs'


def srcset(n, img):
    return ", ".join(f"{img}{n:03d}-{k}.webp {w}w" for k, w in ph(n)["files"])


def img_tag(n, img, sizes, *, eager=False, alt=None):
    p = ph(n)
    k = p["files"][0][0]
    load = ' fetchpriority="high"' if eager else ' loading="lazy" decoding="async"'
    return (f'<img src="{img}{n:03d}-{k}.webp" srcset="{srcset(n, img)}" sizes="{sizes}" width="{p["w"]}" height="{p["h"]}" '
            f'alt="{E(ALT.get(n, "") if alt is None else alt)}"{load}>')


def share(a, total):
    return f"(max-width: 760px) and (orientation: portrait) 100vw, {max(10, round(100 * a / total))}vw"


def row_html(row, img, *, eager=False):
    total = sum(ar(n) for n in row)
    cells = []
    for n in row:
        p = ph(n)
        big = p["files"][-1][0]
        st = f' data-settings="{E(p["settings"])}"' if p["settings"] else ""
        cells.append(f'<a class="ph" href="{img}{n:03d}-{big}.webp" style="--ar:{ar(n):.4f};--c:{p["color"]}" '
                     f'data-w="{p["w"]}" data-h="{p["h"]}" data-srcset="{srcset(n, img)}"{st}>'
                     f'{img_tag(n, img, share(ar(n), total), eager=eager)}</a>')
    return f'<div class="row" style="--sum:{total:.4f};--n:{len(row)}">' + "".join(cells) + "</div>"


def tile(s, home, img, total, *, fixed=False):
    n = s["cover"]
    meta = meta_line(s)
    text = (f'<span class="tile-text"><span class="tile-title">{E(s["title"])}</span>'
            f'<span class="tile-meta">{E(meta) + "<br>" if meta else ""}{count(s)}</span></span>')
    sizes = "(max-width: 760px) and (orientation: portrait) 100vw, 50vw" if fixed else share(ar(n), total)
    pos = f';--pos:{s["focus"]}' if fixed and s.get("focus") else ""
    return (f'<a class="ph tile" href="{home}{s["slug"]}/" style="--ar:{ar(n):.4f};--c:{ph(n)["color"]}{pos}">'
            f'{img_tag(n, img, sizes, alt="")}{text}</a>')


def page(*, title, desc, path, home, body, og, v, series="", viewer=False):
    site = home + "../"
    data = f' data-series="{E(series)}"' if series else ""
    js = f'\n<script src="{home}assets/viewer.js?v={v}" defer></script>' if viewer else ""
    over = "" if series else " over"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}/{path}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Jichu · Art">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{SITE}/{path}">
<meta property="og:image" content="{SITE}/photography/img/{og}">
<link rel="icon" href="{site}assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{site}assets/fonts/playfair-display-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{home}assets/photo.css?v={v}">
</head>
<body{data}>
<a class="skip" href="#main">Skip to content</a>
<header class="top{over}">
  <a class="name" href="{home or "./"}">Jichu Mao</a>
  <nav aria-label="Main">
    <a href="{home}#series">Series</a>
    <a href="{home}#about">About</a>
    <a href="{site}">Graphics work</a>
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <p>© Jichu Mao. All rights reserved. Please ask before using a photograph.</p>
  <p><a href="{site}">jichu.art</a></p>
</footer>{js}
</body>
</html>
"""


def build_home(v):
    img = "img/"
    h = BY_SLUG[HERO["series"]]
    w, t = ph(HERO["wide"]), ph(HERO["tall"])
    hero = f"""<section class="hero">
  <picture>
    <source media="(max-aspect-ratio: 4/5)" srcset="{srcset(HERO["tall"], img)}" sizes="150vw" width="{t["w"]}" height="{t["h"]}">
    <img src="{img}{HERO["wide"]:03d}-1400.webp" srcset="{srcset(HERO["wide"], img)}" sizes="100vw" width="{w["w"]}" height="{w["h"]}" alt="{E(ALT.get(HERO["wide"], ""))}" fetchpriority="high">
  </picture>
  <div class="hero-text">
    <div><h1>Photographs</h1><p>Jichu Mao, 2025 to 2026</p></div>
    <a class="hero-link" href="{h["slug"]}/"><b>{E(h["title"])}</b><span>{E(meta_line(h))}<br>{count(h)}</span></a>
  </div>
</section>
"""
    seen = [x for row in HOME_ROWS for x in row]
    assert sorted(seen + [HERO["series"]]) == sorted(BY_SLUG), "HOME_ROWS must list every series but the opening one, once"
    rows = []
    for row in HOME_ROWS:
        ss = [BY_SLUG[x] for x in row]
        total = sum(ar(s["cover"]) for s in ss)
        rows.append(f'<div class="row" style="--sum:{total:.4f};--n:{len(ss)}">' + "".join(tile(s, "", img, total) for s in ss) + "</div>")
    about = "".join(f"<p>{E(x)}</p>" for x in ABOUT)
    body = hero + f"""<section class="series-index rows" id="series" aria-label="Series">
<h2 class="hide">Series</h2>
{chr(10).join(rows)}
</section>
<section class="about" id="about">
  <h2>About</h2>
  <div>{about}<p><a href="mailto:{EMAIL}">{EMAIL}</a><br><a href="../">Rendering and graphics work</a></p></div>
</section>"""
    total = sum(len(ids(s)) for s in SERIES)
    return page(title="Photographs – Jichu Mao", path="photography/", home="", body=body, og=f'{HERO["wide"]:03d}-1400.webp', v=v,
                desc=f"Photographs by Jichu Mao, 2025 to 2026: {total} pictures in {len(SERIES)} series, from the California coast to Macau at night.")


def build_series(i, v):
    s = SERIES[i]
    img, home = "../img/", "../"
    meta = meta_line(s)
    panel = (f'<div class="panel"><h1>{E(s["title"])}</h1>'
             + (f'<p class="where">{E(meta)}</p>' if meta else "")
             + (f'<p>{E(s["note"])}</p>' if s["note"] else "")
             + f'<p class="count">{count(s)}</p></div>')
    lead = f'<div class="lead">{panel}{row_html(s["rows"][0], img, eager=True)}</div>'
    rest = "\n".join(row_html(r, img) for r in s["rows"][1:])
    nxt = [SERIES[(i + 1) % len(SERIES)], SERIES[(i + 2) % len(SERIES)]]
    more = "".join(tile(x, home, img, 1, fixed=True) for x in nxt)
    body = f"""{lead}
<div class="rows">
{rest}
</div>
<section class="more">
  <h2>More series</h2>
  <div class="row">{more}</div>
</section>"""
    desc = (s["note"] + " " if s["note"] else "") + f'{count(s).capitalize()} by Jichu Mao' + (f", {meta}." if meta else ".")
    return page(title=f'{s["title"]} – Photographs by Jichu Mao', path=f'photography/{s["slug"]}/', home=home, body=body,
                og=f'{s["cover"]:03d}-1400.webp' if any(k == 1400 for k, _ in ph(s["cover"])["files"]) else f'{s["cover"]:03d}-{ph(s["cover"])["files"][-1][0]}.webp',
                v=v, series=s["title"], viewer=True, desc=desc)


def build(root, v="1", strict=True):
    """Writes the pages and returns their site-relative paths (for the sitemap)."""
    used = [n for s in SERIES for n in ids(s)]
    assert len(used) == len(set(used)), "a photograph is used twice"
    if strict:
        missing = [n for n in used if not ALT.get(n)]
        assert not missing, f"no ALT text for {missing}"
    out = {"photography/index.html": build_home(v)}
    for i, s in enumerate(SERIES):
        out[f'photography/{s["slug"]}/index.html'] = build_series(i, v)
    for path, text in out.items():
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    return ["photography/"] + [f'photography/{s["slug"]}/' for s in SERIES]


if __name__ == "__main__":
    pages = build(sys.argv[1] if len(sys.argv) > 1 else ".", strict="--draft" not in sys.argv)
    print("built", len(pages), "photography pages,", sum(len(ids(s)) for s in SERIES), "photographs")
