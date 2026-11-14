"""Builds the photography section (photography/).

Run through tools/build.py, or on its own from the repo root:
    python3 tools/photography.py .

Everything editable is in this file: SERIES (titles, rows), CHAPTERS (the index page and the order of everything),
SLIDES, SUBJECTS, TIMELINE and MAP_LABELS (the timeline page and its globe), PLACE and ALT (one description per photograph). tools/photos.json holds what was measured
from the files (pixel sizes, placeholder colour, camera settings).
The stylesheet and the viewer are hand-written: photography/assets/.

The section is written twice: in English at photography/ and in Chinese at photography/zh/.
Both editions share the photographs, the stylesheet and the scripts. The Chinese text is in
tools/photography_zh.py; anything missing there appears in English and is listed when the build runs.
"""
import html, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from photography_zh import ZH, ALT_ZH

SITE = "https://jichu.art"
EMAIL = "maojichu@gmail.com"
E = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "photos.json")))

LANG = "en"          # the edition being written; build() switches it
ANALYTICS = ""       # the analytics tag for <head>, or nothing; build() sets it
MISSING = set()      # English strings that had no Chinese when the Chinese edition was built
MONTHS = "January February March April May June July August September October November December".split()


def T(s):
    """A piece of text in the edition being written: as it is for English, looked up in photography_zh.py for Chinese."""
    if LANG == "en" or not s:
        return s
    if s not in ZH:
        MISSING.add(s)
    return ZH.get(s, s)


def alt_text(n):
    if LANG == "zh":
        if n not in ALT_ZH:
            MISSING.add(f"ALT_ZH[{n}]")
        return ALT_ZH.get(n) or ALT.get(n, "")
    return ALT.get(n, "")


def when(s):
    """'July 2025' as it is, or as '2025 年 7 月' in the Chinese edition."""
    w = s["when"]
    if LANG == "en" or not w:
        return w
    parts = w.split()
    return f"{parts[1]} 年 {MONTHS.index(parts[0]) + 1} 月" if len(parts) == 2 else f"{w} 年"


def comma():
    return ", " if LANG == "en" else "，"

# One entry per series. Their order on the site is set by CHAPTERS, further down.
#   rows   the sequence. Each inner list is one row on a wide screen; on a
#          phone held upright the same order runs top to bottom.
#   cover  the photograph used for the tile on the index page.
#   focus  optional. Where to hold the cover when a tile has to crop it
#          ("More series" at the foot of a series page), as a CSS position.
#   link   optional. (text, page on the main site) shown under the note.
#   title_zh  optional. The series' own title in the Chinese edition, when it is not a translation of `title`
#          (Jichu's titles for his city sets); otherwise the Chinese edition translates `title` through ZH.
SERIES = [
    dict(slug="above-the-fog", title="Above the Fog", where="Ridge Trailhead, California", when="July 2025",
         note="An evening on a ridge trail while the marine layer filled the valleys below.",
         rows=[[4], [7, 3], [1, 12], [13, 16]], cover=12),
    dict(slug="rooftop", title="CYBER CHONGQING 2026", where="Chongqing", when="June 2026",
         note="LED glasses and two light sticks, high above the city at night.",
         rows=[[18, 20, 25]], cover=20, focus="50% 52%"),
    dict(slug="macau", title="Macau", title_zh="镜海流金，浮世绘梦", where="Macau Peninsula and Cotai", when="January 2026",
         note="An afternoon in the old town, then the casinos after dark.",
         rows=[[242, 241], [246, 247, 249, 255], [251, 252]], cover=246, focus="50% 40%"),
    dict(slug="salt", title="Salt", where="Alviso Marina County Park, San Jose", when="June 2025",
         note="Salt ponds at the southern end of San Francisco Bay.",
         rows=[[58], [57, 54], [52, 64, 63], [61, 62]], cover=58),
    dict(slug="rose", title="Rose", where="Quzhou, Zhejiang", when="May 2025",
         note="A portrait session in a café.",
         rows=[[127, 136], [129, 132, 138], [142, 146]], cover=132, focus="50% 30%"),
    dict(slug="fourth-of-july", title="Fourth of July", title_zh="独立日", where="Yerba Buena Island, San Francisco", when="July 2025",
         note="From dusk to the fireworks, seen from the middle of the bay.",
         rows=[[114, 118], [117], [116], [120, 122]], cover=120, focus="50% 38%"),
    dict(slug="guangzhou", title="Guangzhou", title_zh="花城光影，霓虹成河", where="", when="January 2026",
         note="Museum halls by day, the Pearl River after dark.",
         rows=[[214, 216], [213, 215], [308, 220, 221]], cover=221, focus="50% 45%"),
    dict(slug="evening-walk", title="Evening Walk", where="Fushan Park, Quzhou, Zhejiang", when="May 2025",
         note="Portraits in a park at dusk.",
         rows=[[43, 38], [46, 49]], cover=38, focus="50% 30%"),
    dict(slug="pacific", title="Pacific", where="Ocean Beach and Sutro Baths, San Francisco", when="July 2025",
         note="The western edge of the city on a clear afternoon.",
         rows=[[94, 97], [95, 96], [101, 103], [102, 100], [98, 104]], cover=101, focus="45% 62%"),
    dict(slug="dry-hills", title="Dry Hills", where="Hills east of San Jose, California", when="July 2025",
         note="Sunset from the grazing land above the valley.",
         rows=[[71], [73, 74], [77, 79], [68, 80]], cover=79),
    dict(slug="subway", title="Subway", where="", when="April 2025",
         note="A subway car I built in Unreal Engine, photographed off a 4K monitor with a Canon 5D Mark IV, a 50 mm lens and a polarising filter, then finished to take the digital edge off.",
         rows=[[398], [399, 397], [391], [393, 396], [394, 392], [395, 400]], cover=398, link=("How it was made", "works/virtual-subway/")),
    dict(slug="zhuhai", title="Zhuhai", title_zh="珠落夜色，海照贝影", where="", when="January 2026",
         note="The lighthouse and the Fisher Girl by day, the opera house from dusk into the night, and the moon over the sea.",
         rows=[[222, 225], [230], [232, 240], [238]], cover=240),
    dict(slug="tea-hills", title="Tea Hills", where="Wuyi, Jinhua, Zhejiang", when="December 2025",
         note="A tea estate built around a château-style hotel.",
         rows=[[200, 197, 202], [206, 205]], cover=206),
    dict(slug="off-season", title="Off-season", where="Atlantic City and Cape May, New Jersey", when="March 2025",
         note="The Jersey Shore before the summer crowds.",
         rows=[[261], [390, 363], [267, 368], [373, 374], [284, 289], [288]], cover=374),
    dict(slug="pennsylvania", title="Pennsylvania", where="Near Allentown", when="October 2025",
         note="A gorge overlook, an orchard and a small town in autumn.",
         rows=[[187], [181, 174], [182, 193], [188, 194, 189]], cover=174),
]

# The index page, in chapters. Every series appears once. The order here is also the order of the whole section:
# the "All" page, the subject pages and the "More series" links at the foot of a series follow it.
#   note     one sentence under the chapter's title
#   per_row  covers in a row on a wide screen. Covers are shown whole, in their own proportions: the covers of a row
#            share one height and divide the width between them, as the photographs on a series page do.
CHAPTERS = [
    dict(title="Landscape", note="California at the end of the day: fog over the ridges, salt ponds, dry hills and the Pacific.",
         series=["above-the-fog", "salt", "dry-hills", "pacific"], per_row=2),
    dict(title="Cities after dark", note="Macau, Zhuhai and Guangzhou in January, and San Francisco on the Fourth of July.",
         series=["macau", "zhuhai", "guangzhou", "fourth-of-july"], per_row=2),
    dict(title="Portraits", note="Three sessions: a café, a park at dusk, a rooftop at night.",
         series=["rose", "evening-walk", "rooftop"], per_row=3),
    dict(title="Other work", note="Shorter sets and experiments.",
         series=["off-season", "pennsylvania", "tea-hills", "subway"], per_row=4),
]

# Opening slideshow of the index page: (photograph for wide screens, photograph for upright phones, series it links to).
# The strongest pictures of the whole section, chosen at the slideshow's own full-screen crop; one per series,
# alternating warm and cool, day and night. The upright partner comes from the same series.
SLIDES = [
    (12, 1, "above-the-fog"),
    (240, 238, "zhuhai"),
    (58, 57, "salt"),
    (221, 308, "guangzhou"),
    (79, 77, "dry-hills"),
    (120, 120, "fourth-of-july"),
]

# Subject pages. A photograph can be listed under more than one subject; every photograph needs at least one.
SUBJECTS = [
    dict(slug="landscape", title="Landscape",
         photos=[4, 3, 7, 13, 12, 16, 58, 57, 62, 52, 71, 73, 74, 77, 79, 68, 80, 200, 187]),
    dict(slug="coast", title="Coast",
         photos=[94, 97, 95, 96, 101, 103, 102, 100, 98, 104, 222, 225, 261, 390, 284, 289, 288]),
    dict(slug="night", title="Night",
         photos=[251, 252, 255, 308, 220, 221, 114, 117, 116, 118, 120, 122, 206, 205, 240, 238, 18, 20, 25, 80]),
    dict(slug="architecture", title="Architecture",
         photos=[242, 241, 249, 251, 252, 64, 63, 214, 216, 213, 215, 197, 202, 206, 230, 232, 240, 363, 267, 373, 374]),
    dict(slug="street", title="Street",
         photos=[246, 247, 74, 368, 188, 194, 189, 214, 7]),
    dict(slug="portrait", title="Portrait",
         photos=[127, 136, 129, 132, 138, 142, 146, 43, 38, 46, 49, 18, 20, 25, 194, 189]),
    dict(slug="black-and-white", title="Black and White",
         photos=[398, 399, 397, 391, 393, 396, 394, 392, 395, 400, 267]),
    dict(slug="details", title="Details",
         photos=[1, 54, 61, 215, 255, 395, 181, 182, 174, 193]),
]

# The timeline page (timeline/): when and where each series was made.
#   date   the day it was made (ISO). Orders the timeline; the page itself shows only the month.
#   at     where it goes on the map: one or more (latitude, longitude). Empty for a series made inside a computer.
#   place  what the timeline shows under the title when the series has no "where" of its own.
TIMELINE = {
    "off-season":     dict(date="2025-03-09", at=[(39.36, -74.42), (38.93, -74.91)]),
    "subway":         dict(date="2025-04-15", at=[], place="Inside Unreal Engine"),
    "evening-walk":   dict(date="2025-05-20", at=[(28.96, 118.86)]),
    "rose":           dict(date="2025-05-22", at=[(28.97, 118.87)]),
    "salt":           dict(date="2025-06-29", at=[(37.43, -121.97)]),
    "above-the-fog":  dict(date="2025-07-02", at=[(37.33, -122.19)]),
    "fourth-of-july": dict(date="2025-07-04", at=[(37.81, -122.37)]),
    "pacific":        dict(date="2025-07-05", at=[(37.76, -122.51)]),
    "dry-hills":      dict(date="2025-07-20", at=[(37.37, -121.76)]),
    "pennsylvania":   dict(date="2025-10-18", at=[(40.75, -75.60)]),
    "tea-hills":      dict(date="2025-12-20", at=[(28.89, 119.81)]),
    "guangzhou":      dict(date="2026-01-02", at=[(23.13, 113.26)], place="Guangdong"),
    "zhuhai":         dict(date="2026-01-04", at=[(22.27, 113.58)], place="Guangdong"),
    "macau":          dict(date="2026-01-05", at=[(22.19, 113.54)]),
    "rooftop":        dict(date="2026-06-06", at=[(29.56, 106.55)]),
}
# Names written on the globe, one per group of nearby places: (name, latitude, longitude, side).
# side: "right" or "left" of the point.
MAP_LABELS = [
    ("Bay Area", 37.55, -122.1, "left"),
    ("Pennsylvania and New Jersey", 40.0, -75.1, "right"),   # one spot on the globe: Allentown and the Jersey Shore
    ("Chongqing", 29.56, 106.55, "left"),
    ("Zhejiang", 28.93, 119.3, "right"),
    ("Guangzhou, Zhuhai, Macau", 22.6, 113.45, "left"),
]
# Which dots of the globe are land; made by tools/footprint.py.
LAND = json.load(open(os.path.join(HERE, "footprint.json")))

# Where a single photograph was taken, when that is more exact than its series' "where".
PLACE = {
    242: "Grand Lisboa", 246: "Casino Lisboa", 252: "Wynn Palace, Cotai", 249: "The Venetian Macao, Cotai",
    251: "The Londoner Macao, Cotai", 308: "Canton Tower", 220: "Chigang Pagoda",
    221: "Haixin Bridge and Zhujiang New Town", 232: "Zhuhai Opera House", 240: "Zhuhai Opera House",
    225: "Fisher Girl statue", 230: "Zhuhai Opera House", 95: "Ocean Beach, San Francisco", 96: "Ocean Beach, San Francisco",
    97: "Ocean Beach, San Francisco", 94: "Ocean Beach, San Francisco", 101: "Sutro Baths, San Francisco",
    102: "Sutro Baths, San Francisco", 103: "Sutro Baths, San Francisco",
    100: "Seal Rocks, San Francisco", 104: "Golden Gate Bridge", 116: "Bay Bridge, east span",
    117: "Bay Bridge and San Francisco", 261: "Atlantic City", 390: "Steel Pier, Atlantic City",
    363: "Atlantic City", 267: "Atlantic City", 368: "Atlantic City", 374: "Cape May", 289: "Cape May",
    284: "Cape May Lighthouse", 288: "Sunset Beach, Cape May", 181: "Orchard near Allentown",
    182: "Orchard near Allentown", 174: "Orchard near Allentown",
}

# One plain description per photograph (used as alt text).
ALT = {
    # Above the Fog
    4: "Golden grass on a ridge above forested hills, with a sea of fog reaching the horizon.",
    3: "A dirt trail curving up a grassy ridge toward the low sun.",
    1: "Dry grass stalks in front of a bank of fog.",
    13: "The sun setting over fog-filled valleys, seen across a field of red grass.",
    12: "An orange sunset over the fog, a dark tree line on the left.",
    16: "Fog rolling over dark ridges under a pink and blue sky after sunset.",
    # Macau
    242: "The Grand Lisboa tower rising between old apartment blocks.",
    241: "A yellow colonial building with green shutters and palm trees, towers behind it.",
    246: "Pedestrians crossing in front of the Casino Lisboa's neon entrance.",
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
    # Rose
    127: "A woman in a black slip dress sits on a cream sofa holding a red rose, lit from the side.",
    136: "She reclines on the sofa in a dark room, the rose held up to one eye.",
    129: "She leans on the arm of the sofa, looking down at the rose in her hand.",
    132: "She holds the rose to her lips and looks at the camera.",
    146: "Close portrait from above; she looks down with a slight smile.",
    # Subway
    398: "The side of a subway car in a virtual scene, photographed off a monitor: the number 8805 and a flag decal beside a window.",
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
    308: "The Canton Tower at dusk behind a bed of pink flowers.",
    220: "A lit pagoda at night beyond an empty plaza.",
    221: "The Guangzhou skyline and an arched bridge at night, boat lights streaking across the river.",
    # Pacific
    95: "A gull standing in the shallows as a wave breaks behind it.",
    96: "A dog running along the wet sand with a ball in its mouth, sea stacks behind.",
    101: "A cormorant perched on a ruined wall while a person walks along it, the sea glittering behind.",
    97: "A lone figure far off on an empty beach.",
    94: "A figure in black standing in the shallows, facing the breaking waves.",
    103: "The broken concrete edge of an old seawater pool, a strip of green, and rocks in a glittering sea.",
    102: "Three bands: green grass, a still blue pool, the white surf of the open sea.",
    98: "A road curving down past a crosswalk and a cypress toward the ocean.",
    104: "The Golden Gate Bridge seen from a sandy beach.",
    # Fourth of July
    114: "A causeway and an island at sunset, the sky fading from orange to blue.",
    116: "The white tower of the Bay Bridge at night, light trails along the road.",
    118: "The downtown skyline lit up at night, seen across the water.",
    120: "Gold fireworks bursting over the bay above red smoke.",
    122: "Two blue fireworks over dark water.",
    # Dry Hills
    71: "Rolling golden hills in low evening light, long shadows in the folds.",
    77: "A person in silhouette watching the sun set behind a hill.",
    79: "The sun touching a dark ridge above a fenced hillside road.",
    80: "A black cow seen from behind, looking out over a valley of city lights at dusk.",
    # Rooftop
    18: "A man in LED glasses stands on a rooftop stairway at night, small against neon-lit towers.",
    20: "He leans on the stair rail holding two light sticks, his glasses glowing.",
    25: "He stands with the light sticks crossed over his chest, lit red by them.",
    # Evening Walk
    43: "A woman in a grey cap and sleeveless top stands on a lawn and looks at the camera, a pagoda behind the trees.",
    38: "Close profile: the peak of her cap hides her eyes.",
    46: "She sits on a wooden bench in profile, one arm resting on her knee.",
    49: "She stands on a path at dusk holding the strap of her bag, looking at the camera.",
    # Zhuhai
    222: "A small white lighthouse at the end of a jetty, seen from a sunlit beach.",
    225: "A statue of a woman holding a pearl aloft, on a rock in the sea under a deep blue sky.",
    230: "The opera house and a red pavilion across the water, framed by a carved stone window at sunset.",
    232: "The two shells of the opera house at dusk above a paved plaza.",
    240: "The opera house shells lit amber at night.",
    238: "The moon high over the dark sea, its path of light reaching a lit railing.",
    # Off-season
    261: "An empty boardwalk and beach; a kite is caught on a line of string lights.",
    373: "A narrow lane between pastel-painted shopfronts.",
    368: "Mannequins in pastel tracksuits outside a shop window lettered 'Homemade fudge' and 'Hot roasted nuts'.",
    289: "A row of benches on the sand in low sun; two people sit on one, facing the sea.",
    288: "The sun setting over the sea beside a half-sunken wreck; a person stands on the jetty.",
    # Pennsylvania
    187: "Two people sit on a rock ledge above a river gorge in autumn colour.",
    181: "Red apples on a branch against a blue sky.",
    182: "Fallen apples lying in rows beneath the orchard trees.",
    174: "An old blue pickup truck loaded with pumpkins, beside a giant pumpkin and chrysanthemums.",
    188: "A crowded main street leading up to a stone church, autumn hills behind.",
    194: "A street musician in a red jacket and sunglasses plays guitar on a bench.",
    189: "A street musician in a bandana plays guitar by a wooden fence, his case open beside him.",
    193: "Two white ornamental pumpkins with black metal leaves among warm fairy lights.",
    # Tea Hills
    200: "Terraced tea bushes and bare white-trunked trees below a glass dome, mountains behind.",
    202: "A château-style hotel reflected in a pond, framed by a branch of red leaves.",
    206: "The hotel lit at night, mirrored in still water.",
    205: "An outdoor Christmas tree wrapped in lights against a dark sky.",
    # added later
    7: "Two long shadows fall across a dirt trail through golden grass.",
    68: "Layered ridges fading into haze under an orange sky.",
    73: "The valley and its city at golden hour, seen past a slope scattered with rocks.",
    74: "Three people on a grassy hill looking out over the city below.",
    100: "Sea stacks beyond a bank of yellow flowers.",
    117: "The Bay Bridge strung with lights, leading to the San Francisco skyline at night.",
    138: "She crouches beside the sofa, looking down.",
    142: "Close portrait: she smiles, shelves and warm light behind her.",
    197: "A stone clock tower behind beds of red and yellow flowers.",
    267: "Cloud shadows on a blank white wall behind a row of lamp posts, in black and white.",
    284: "A boardwalk ramp zigzagging toward a distant lighthouse.",
    363: "A pale tower rising behind a curved wall of blue glass.",
    374: "A Victorian porch hung with pink bows and mirror balls.",
    390: "An amusement pier with a Ferris wheel, seen from above the shoreline.",
    393: "A door window beside a 'No exit' sign and graffiti.",
}

ABOUT = [
    "I’m Jichu Mao. I work on real-time rendering and GPU performance, and I photograph on the side: "
    "landscapes, cities after dark, and now and then a portrait.",
    "These pictures were made in 2025 and 2026 in California, on the East Coast of the United States and in "
    "China, on a Sony α7C II and a Canon EOS 5D Mark IV.",
]

BY_SLUG = {s["slug"]: s for s in SERIES}
_order = [x for c in CHAPTERS for x in c["series"]]
assert sorted(_order) == sorted(BY_SLUG), "CHAPTERS must list every series once"
SERIES.sort(key=lambda s: _order.index(s["slug"]))


def ph(n):
    return P[f"{n:03d}"]


def ar(n):
    return ph(n)["w"] / ph(n)["h"]


def ids(s):
    return [n for row in s["rows"] for n in row]


ORDER = [n for s in SERIES for n in ids(s)]            # every photograph, in site order
SERIES_OF = {n: s for s in SERIES for n in ids(s)}


def meta_line(s):
    return comma().join(x for x in (T(s["where"]), when(s)) if x)


def count(n):
    return f"{n} photographs" if LANG == "en" else f"{n} 张照片"


def place(n):
    """Caption for one photograph: the exact place if known, else where its series was made."""
    return T(PLACE.get(n) or SERIES_OF[n]["where"])


def srcset(n, img):
    return ", ".join(f"{img}{n:03d}-{k}.webp {w}w" for k, w in ph(n)["files"])


def img_tag(n, img, sizes, *, eager=False, alt=None):
    p = ph(n)
    k = p["files"][0][0]
    load = ' fetchpriority="high"' if eager else ' loading="lazy" decoding="async"'
    return (f'<img src="{img}{n:03d}-{k}.webp" srcset="{srcset(n, img)}" sizes="{sizes}" width="{p["w"]}" height="{p["h"]}" '
            f'alt="{E(alt_text(n) if alt is None else alt)}"{load}>')


def share(a, total, phone=None):
    """The sizes attribute: the photograph's share of the row's width. On an upright phone it is the full width,
    unless the page says otherwise (phone: a width in vw, e.g. a column of a three-column grid)."""
    w = max(10, round(100 * a / total))
    return f"(max-width: 760px) and (orientation: portrait) {phone if phone is not None else 100}vw, {w}vw"


def row_html(row, img, *, eager=False, with_series=False, phone=None):
    """phone: the width in vw each photograph takes on an upright phone, when it is not the full width:
    "grid" for the three-column grid of square crops, "row" for a row kept side by side (the timeline)."""
    total = sum(ar(n) for n in row)
    cells = []
    for n in row:
        p = ph(n)
        big = p["files"][-1][0]
        st = f' data-settings="{E(p["settings"])}"' if p["settings"] else ""
        cap = place(n)
        if with_series:
            title = ST(SERIES_OF[n])
            cap = title if not cap or cap == title else f"{title}{comma()}{cap}"
        cp = f' data-cap="{E(cap)}"' if cap else ""
        cells.append(f'<a class="ph" href="{img}{n:03d}-{big}.webp" style="--ar:{ar(n):.4f};--c:{p["color"]}" '
                     f'data-w="{p["w"]}" data-h="{p["h"]}" data-srcset="{srcset(n, img)}"{st}{cp}>'
                     f'{img_tag(n, img, share(ar(n), total, 34 if phone == "grid" else max(10, round(100 * ar(n) / total)) if phone == "row" else None), eager=eager)}</a>')
    return f'<div class="row" style="--sum:{total:.4f};--n:{len(row)}">' + "".join(cells) + "</div>"


def auto_rows(photos, target=2.7, most=4.3):
    """Packs photographs into rows for the subject pages: a row closes once its aspect ratios add up to `target`."""
    rows, cur, total = [], [], 0.0
    for n in photos:
        if cur and total + ar(n) > most:
            rows.append(cur); cur, total = [], 0.0
        cur.append(n); total += ar(n)
        if total >= target:
            rows.append(cur); cur, total = [], 0.0
    if cur:
        if rows and total < 1.3 and sum(ar(n) for n in rows[-1]) + total <= most + 0.4:
            rows[-1] += cur
        else:
            rows.append(cur)
    return rows


def tile(s, home, img, total, *, fixed=False):
    n = s["cover"]
    meta = meta_line(s)
    text = (f'<span class="tile-text"><span class="tile-title">{E(ST(s))}</span>'
            f'<span class="tile-meta">{E(meta) + "<br>" if meta else ""}{count(len(ids(s)))}</span></span>')
    sizes = "(max-width: 760px) and (orientation: portrait) 100vw, 50vw" if fixed else share(ar(n), total)
    pos = f';--pos:{s["focus"]}' if fixed and s.get("focus") else ""
    return (f'<a class="ph tile" href="{home}{s["slug"]}/" style="--ar:{ar(n):.4f};--c:{ph(n)["color"]}{pos}">'
            f'{img_tag(n, img, sizes, alt="")}{text}</a>')


def ST(s):
    """A series' title in the edition being built."""
    return s["title_zh"] if LANG == "zh" and s.get("title_zh") else T(s["title"])


def card(s, home, img, total, pair=None):
    """A series on the index page: its cover, whole and in its own proportions, with the title and facts under it.
    `total` is the sum of the proportions of the covers in its row, which share one height; `pair`, for a row of
    four, the sum for the two it is paired with on a narrower screen."""
    n = s["cover"]
    meta = meta_line(s)
    share = lambda t: max(12, round(100 * ar(n) / t))
    narrow = f"(max-width: 1000px) {share(pair)}vw" if pair else "(max-width: 760px) and (orientation: portrait) 100vw"
    sizes = f"{narrow}, {share(total)}vw"
    return (f'<a class="card" href="{home}{s["slug"]}/" style="--ar:{ar(n):.4f}">'
            f'<span class="card-img" style="--c:{ph(n)["color"]}">{img_tag(n, img, sizes, alt="")}</span>'
            f'<span class="card-title">{E(ST(s))}</span>'
            f'<span class="card-meta">{E(meta)}</span><span class="card-count">{count(len(ids(s)))}</span></a>')


def subjects_nav(home, current="", quiet=False):
    cur = ' aria-current="page"'
    links = [f'<a href="{home}all/"{cur if current == "all" else ""}>{T("All")}<sup>{len(ORDER)}</sup></a>']
    links += [f'<a href="{home}{g["slug"]}/"{cur if current == g["slug"] else ""}>{E(T(g["title"]))}<sup>{len(g["photos"])}</sup></a>' for g in SUBJECTS]
    return f'<nav class="subjects{" quiet" if quiet else ""}" id="subjects" aria-label="{T("Subjects")}"><span class="subjects-label">{T("By subject")}</span>{"".join(links)}</nav>'


def base(rel):
    """From a page to photography/ itself, where img/ and assets/ are. `rel` is the page's place in its edition: "" or "macau/"."""
    return ("../" if rel else "") + ("../" if LANG == "zh" else "")


def page(*, title, desc, rel, body, og, v, series="", scripts=(), current=""):
    home = "../" if rel else ""            # the index page of this edition
    root = base(rel)                       # photography/
    site = root + "../"                    # the main site
    zh = LANG == "zh"
    path = f"photography/{'zh/' if zh else ''}{rel}"
    other = f'{root}{rel}' if zh else f'{root}zh/{rel}'
    switch = (f'<a class="lang" href="{other or "./"}" lang="en" hreflang="en" aria-label="English edition">EN</a>' if zh
              else f'<a class="lang" href="{other}" lang="zh-Hans" hreflang="zh-Hans" aria-label="中文版">中文</a>')
    data = f' data-series="{E(series)}"' if series else ""
    js = "".join(f'\n<script src="{root}assets/{s}?v={v}" defer></script>' for s in scripts)
    over = "" if rel else " over"
    return f"""<!doctype html>
<html lang="{"zh-Hans" if zh else "en"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{SITE}/{path}">
<link rel="alternate" hreflang="en" href="{SITE}/photography/{rel}">
<link rel="alternate" hreflang="zh-Hans" href="{SITE}/photography/zh/{rel}">
<link rel="alternate" hreflang="x-default" href="{SITE}/photography/{rel}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Jichu · Art">
<meta property="og:locale" content="{"zh_CN" if zh else "en_US"}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{SITE}/{path}">
<meta property="og:image" content="{SITE}/photography/og/{og}.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#000000">
<link rel="icon" href="{site}assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{site}assets/fonts/playfair-display-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/photo.css?v={v}">{ANALYTICS}
</head>
<body{data}>
<a class="skip" href="#main">{T("Skip to content")}</a>
<header class="top{over}">
  <a class="name" href="{home or "./"}">Jichu Mao</a>
  <nav aria-label="Main">
    <a href="{home}#series">{T("Series")}</a>
    <a href="{home}timeline/"{' aria-current="page"' if current == "timeline" else ""}>{T("Timeline")}</a>
    <a class="opt2" href="{home}#subjects">{T("Subjects")}</a>
    <a class="opt" href="{home}#about">{T("About")}</a>
    <a href="{site}">{T("Graphics")}<span class="wide">{T(" work")}</span></a>
    {switch}
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <p>{T("© Jichu Mao. All rights reserved. Please ask before using a photograph.")}</p>
  <p><a href="{site}">jichu.art</a> · <a href="https://beian.miit.gov.cn/" rel="noopener">京ICP备2024041560号-1</a></p>
</footer>{js}
</body>
</html>
"""


def build_home(v):
    img = base("") + "img/"
    site = base("") + "../"
    slides, dots = [], []
    for i, (wide, tall, slug) in enumerate(SLIDES):
        s = BY_SLUG[slug]
        w, t = ph(wide), ph(tall)
        first = i == 0
        a = "srcset" if first else "data-srcset"
        src = f'src="{img}{wide:03d}-1400.webp" ' if first else ""
        hidden = "" if first else ' aria-hidden="true" tabindex="-1"'
        slides.append(f"""    <a class="slide{" on" if first else ""}" href="{slug}/"{hidden}>
      <picture>
        <source media="(max-aspect-ratio: 4/5)" {a}="{srcset(tall, img)}" sizes="118vw" width="{t["w"]}" height="{t["h"]}">
        <img {src}{a}="{srcset(wide, img)}" sizes="100vw" width="{w["w"]}" height="{w["h"]}" alt="{E(alt_text(wide))}"{' fetchpriority="high"' if first else ""}>
      </picture>
      <span class="slide-cap"><b>{E(ST(s))}</b><span>{E(meta_line(s))}<br>{count(len(ids(s)))}</span></span>
    </a>""")
        dots.append(f'<button class="dot" type="button" aria-label="{E(("Show " + s["title"]) if LANG == "en" else ("显示" + ST(s)))}"{" aria-current=" + chr(34) + "true" + chr(34) if first else ""}></button>')
    hero = f"""<section class="hero" aria-roledescription="carousel" aria-label="{T("Selected photographs")}">
  <div class="slides">
{chr(10).join(slides)}
  </div>
  <div class="hero-text"><h1>{T("Photographs")}</h1><p>{T("Jichu Mao, 2025 to 2026")}</p></div>
  <div class="hero-ctl">
    <button class="hero-pause" type="button" aria-label="{T("Pause slideshow")}" aria-pressed="false"><svg viewBox="0 0 24 24" aria-hidden="true"><path class="i-pause" d="M8 5v14M16 5v14"/><path class="i-play" d="M8 5l11 7-11 7z"/></svg></button>
    {"".join(dots)}
  </div>
</section>
"""
    chapters = []
    for k, c in enumerate(CHAPTERS):
        rows = []
        for i in range(0, len(c["series"]), c["per_row"]):
            row = [BY_SLUG[x] for x in c["series"][i:i + c["per_row"]]]
            total = sum(ar(x["cover"]) for x in row)
            if c["per_row"] == 4:     # two pairs: one row of four on a wide screen, two rows of two on a narrower one
                pairs = [row[:2], row[2:]]
                inner = "".join(f'<div class="card-pair" style="--sum:{sum(ar(x["cover"]) for x in pr):.4f}">'
                                + "".join(card(x, "", img, total, sum(ar(y["cover"]) for y in pr)) for x in pr) + "</div>"
                                for pr in pairs if pr)
            else:
                inner = "".join(card(x, "", img, total) for x in row)
            rows.append(f'<div class="card-row r{c["per_row"]}" style="--sum:{total:.4f};--n:{len(row)}">{inner}</div>')
        chapters.append(f"""<section class="chapter"{' id="series"' if k == 0 else ""}>
  <header class="chapter-head"><h2>{E(T(c["title"]))}</h2><p>{E(T(c["note"]))}</p></header>
  <div class="cards">{"".join(rows)}</div>
</section>""")
    about = "".join(f"<p>{E(T(x))}</p>" for x in ABOUT)
    body = hero + chr(10).join(chapters) + f"""
{subjects_nav("", quiet=True)}
<section class="about" id="about">
  <h2>{T("About")}</h2>
  <div>{about}<p><a href="mailto:{EMAIL}">{EMAIL}</a><br><a href="{site}">{T("Rendering and graphics work")}</a></p></div>
</section>"""
    if LANG == "zh":
        title = "摄影 – Jichu Mao"
        desc = f"Jichu Mao 的摄影作品，2025–2026：{len(ORDER)} 张照片，{len(SERIES)} 个系列，从加州海岸到夜色中的澳门。"
    else:
        title = "Photographs – Jichu Mao"
        desc = f"Photographs by Jichu Mao, 2025 to 2026: {len(ORDER)} pictures in {len(SERIES)} series, from the California coast to Macau at night."
    return page(title=title, rel="", body=body, og="index", v=v, scripts=("hero.js",), desc=desc)


def build_series(i, v):
    s = SERIES[i]
    rel = s["slug"] + "/"
    img, home, site = base(rel) + "img/", "../", base(rel) + "../"
    meta = meta_line(s)
    title, note = ST(s), T(s["note"])
    link = f'<p class="how"><a href="{site}{s["link"][1]}">{E(T(s["link"][0]))}</a></p>' if s.get("link") else ""
    panel = (f'<div class="panel"><h1>{E(title)}</h1>'
             + (f'<p class="where">{E(meta)}</p>' if meta else "")
             + (f'<p>{E(note)}</p>' if note else "")
             + link
             + f'<p class="count">{count(len(ids(s)))}</p></div>')
    lead = f'<div class="lead">{panel}{row_html(s["rows"][0], img, eager=True)}</div>'
    rest = "\n".join(row_html(r, img) for r in s["rows"][1:])
    nxt = [SERIES[(i + 1) % len(SERIES)], SERIES[(i + 2) % len(SERIES)]]
    more = "".join(tile(x, home, img, 1, fixed=True) for x in nxt)
    body = f"""{lead}
<div class="rows">
{rest}
</div>
<section class="more">
  <h2>{T("More series")}</h2>
  <div class="row" style="--sum:{sum(ar(x["cover"]) for x in nxt):.4f};--n:2">{more}</div>
</section>"""
    if LANG == "zh":
        desc = note + f"{count(len(ids(s)))}，Jichu Mao 摄" + (f"，{meta}。" if meta else "。")
        full = f"{title} – Jichu Mao 摄影"
    else:
        desc = (note + " " if note else "") + f"{count(len(ids(s))).capitalize()} by Jichu Mao" + (f", {meta}." if meta else ".")
        full = f"{title} – Photographs by Jichu Mao"
    return page(title=full, rel=rel, body=body, og=s["slug"], v=v, series=title, scripts=("viewer.js",), desc=desc)


def build_subject(slug, title, photos, v):
    """A subject page: every photograph of one kind, across all series, packed into rows automatically."""
    rel = slug + "/"
    img, home = base(rel) + "img/", "../"
    title = T(title)
    photos = sorted(photos, key=ORDER.index)
    rows = auto_rows(photos)
    names = []
    for n in photos:
        t = ST(SERIES_OF[n])
        if t not in names:
            names.append(t)
    if LANG == "zh":
        sub = f"{count(len(photos))}，来自 {len(names)} 个系列"
        desc = f"{title}：{count(len(photos))}，Jichu Mao 摄，来自{'、'.join(names[:6])}{'等系列' if len(names) > 6 else ''}。"
        full = f"{title} – Jichu Mao 摄影"
    else:
        sub = f"{count(len(photos))} from {len(names)} series"
        desc = f"{title}: {count(len(photos))} by Jichu Mao, from {', '.join(names[:6])}{' and more' if len(names) > 6 else ''}."
        full = f"{title} – Photographs by Jichu Mao"
    head = f'<div class="head"><h1>{E(title)}</h1><p class="count">{sub}</p></div>' + subjects_nav(home, slug)
    body = head + '\n<div class="rows grid">\n' + "\n".join(row_html(r, img, eager=i == 0, with_series=True, phone="grid") for i, r in enumerate(rows)) + "\n</div>"
    return page(title=full, rel=rel, body=body, og=slug, v=v, series=title, scripts=("viewer.js",), desc=desc)


def month_name(m):
    return MONTHS[m - 1] if LANG == "en" else f"{m} 月"


def build_timeline(v):
    """Every series, newest first, beside a globe that turns to each place as the reader moves down the years."""
    rel = "timeline/"
    img, home = base(rel) + "img/", "../"
    series = sorted(SERIES, key=lambda s: TIMELINE[s["slug"]]["date"], reverse=True)
    newest, oldest = series[0], series[-1]
    no = {x["slug"]: len(series) - k for k, x in enumerate(series)}   # 1 is the oldest; pins on the globe carry the same number
    span = f"{when(oldest)} to {when(newest)}" if LANG == "en" else f"{when(oldest)}到 {when(newest)}"

    # what the globe draws (photography/assets/timeline.js)
    data = {
        "stops": [{"s": s["slug"], "no": no[s["slug"]], "n": len(ids(s)), "at": TIMELINE[s["slug"]]["at"]} for s in series],
        "labels": [[T(name), lat, lon, side] for name, lat, lon, side in MAP_LABELS],
        "n": LAND["n"], "land": LAND["land"],
    }
    globe = (f'<div class="globe" aria-hidden="true"><canvas></canvas></div>\n'
             f'    <script type="application/json" id="tl-data">{json.dumps(data, ensure_ascii=False, separators=(",", ":"))}</script>')

    # the list, by year
    years, stops = [], {}  # newest year first
    for s in series:
        y = TIMELINE[s["slug"]]["date"][:4]
        if y not in stops:
            years.append(y); stops[y] = []
        stops[y].append(s)
    groups = []
    for y in years:
        items = []
        for s in stops[y]:
            t = TIMELINE[s["slug"]]
            mon = int(t["date"][5:7])
            where = T(s["where"] or t.get("place", ""))
            strip, total = [s["cover"]], ar(s["cover"])
            for n in ids(s):
                if n != s["cover"] and total < 4.0 and len(strip) < 5:
                    strip.append(n); total += ar(n)
            title = ST(s)
            items.append(f"""      <article class="stop" id="t-{s["slug"]}" data-s="{s["slug"]}" data-title="{E(title)}" data-meta="{E(comma().join(x for x in (where, when(s)) if x))}">
        <p class="stop-when"><span class="stop-no" aria-hidden="true">{no[s["slug"]]}</span><time datetime="{t["date"][:7]}">{month_name(mon)}</time></p>
        <div class="stop-main">
          <h3><a href="../{s["slug"]}/">{E(title)}</a></h3>
          <p class="stop-where"><span>{E(where)}</span><span>{count(len(ids(s)))}</span></p>
          {row_html(strip, img, with_series=True, phone="row")}
        </div>
      </article>""")
        groups.append(f'    <section class="tl-year" aria-label="{y}">\n      <h2>{y}</h2>\n' + "\n".join(items) + "\n    </section>")

    places = sum(1 for s in series if TIMELINE[s["slug"]]["at"])
    if LANG == "zh":
        sub = f"{len(SERIES)} 个系列、{len(ORDER)} 张照片，{span}，在美国和中国。"
        desc = f"Jichu Mao 的摄影足迹：{len(SERIES)} 个系列由近到远排列，{span}，附拍摄地点的地球图。"
        full = "足迹 – Jichu Mao 摄影"
    else:
        sub = f"{len(SERIES)} series and {len(ORDER)} photographs, {span}, in the United States and China."
        desc = f"Photographs by Jichu Mao, newest first, {span}, on a globe of where they were made: {places} places in the United States and China."
        full = "Timeline – Photographs by Jichu Mao"
    body = f"""<div class="head"><h1>{T("Timeline")}</h1><p class="count">{E(sub)}</p></div>
<div class="tl">
  <div class="tl-map">
    {globe}
    <p class="tl-now" aria-hidden="true" data-idle="{E(span)}"><b></b><span>{E(span)}</span></p>
  </div>
  <div class="tl-list">
{chr(10).join(groups)}
  </div>
</div>"""
    return page(title=full, rel=rel, body=body, og="timeline", v=v, series=T("Timeline"), scripts=("viewer.js", "timeline.js"), desc=desc, current="timeline")


def build(root, v="1", strict=True, analytics=""):
    """Writes both editions and returns the pages' site-relative paths (for the sitemap)."""
    global LANG, ANALYTICS
    ANALYTICS = analytics
    assert len(ORDER) == len(set(ORDER)), "a photograph is used twice"
    tagged = {n for g in SUBJECTS for n in g["photos"]}
    assert tagged <= set(ORDER), f"SUBJECTS lists photographs that are in no series: {sorted(tagged - set(ORDER))}"
    assert set(ORDER) <= tagged, f"photographs without a subject: {sorted(set(ORDER) - tagged)}"
    assert set(PLACE) <= set(ORDER), f"PLACE names photographs that are in no series: {sorted(set(PLACE) - set(ORDER))}"
    assert sorted(TIMELINE) == sorted(BY_SLUG), "TIMELINE needs a date for every series, and nothing else"
    slugs = [s["slug"] for s in SERIES] + [g["slug"] for g in SUBJECTS] + ["all", "timeline"]
    assert len(slugs) == len(set(slugs)), "a series and a subject share a slug"
    assert "zh" not in slugs, "'zh' is the address of the Chinese edition"
    if strict:
        missing = [n for n in ORDER if not ALT.get(n)]
        assert not missing, f"no ALT text for {missing}"
    out, pages = {}, []
    for LANG, pre in (("en", "photography/"), ("zh", "photography/zh/")):
        out[pre + "index.html"] = build_home(v)
        for i, s in enumerate(SERIES):
            out[f'{pre}{s["slug"]}/index.html'] = build_series(i, v)
        out[pre + "all/index.html"] = build_subject("all", "All photographs", ORDER, v)
        out[pre + "timeline/index.html"] = build_timeline(v)
        for g in SUBJECTS:
            out[f'{pre}{g["slug"]}/index.html'] = build_subject(g["slug"], g["title"], g["photos"], v)
        pages += [pre] + [f"{pre}{x}/" for x in slugs]
    LANG = "en"
    for path, text in out.items():
        full = os.path.join(root, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    if MISSING:
        print("photography/zh: no Chinese yet for", len(MISSING), "items (shown in English); add them to tools/photography_zh.py:")
        for x in sorted(MISSING):
            print("   ", x)
    return pages


if __name__ == "__main__":
    pages = build(sys.argv[1] if len(sys.argv) > 1 else ".", strict="--draft" not in sys.argv)
    print("built", len(pages), "photography pages,", len(ORDER), "photographs")
