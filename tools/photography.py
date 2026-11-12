"""Builds the photography section (photography/).

Run through tools/build.py, or on its own from the repo root:
    python3 tools/photography.py .

Everything editable is in this file: SERIES (order, titles, rows), HOME_ROWS,
SLIDES, SUBJECTS, PLACE and ALT (one description per photograph). tools/photos.json holds what was measured
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

# One entry per series, in the order they appear on the index page.
#   rows   the sequence. Each inner list is one row on a wide screen; on a
#          phone held upright the same order runs top to bottom.
#   cover  the photograph used for the tile on the index page.
#   focus  optional. Where to hold the cover when a tile has to crop it
#          ("More series" at the foot of a series page), as a CSS position.
#   link   optional. (text, page on the main site) shown under the note.
SERIES = [
    dict(slug="above-the-fog", title="Above the Fog", where="Ridge Trailhead, California", when="July 2025",
         note="An evening on a ridge trail while the marine layer filled the valleys below.",
         rows=[[4], [3, 7], [5], [1, 2, 0], [14, 13], [12], [16, 17]], cover=12),
    dict(slug="rooftop", title="Rooftop", where="Chongqing", when="June 2026",
         note="LED glasses and two light sticks, high above the city at night.",
         rows=[[18, 20, 22], [25, 21]], cover=20, focus="50% 52%"),
    dict(slug="macau", title="Macau", where="Macau Peninsula and Cotai", when="January 2026",
         note="An afternoon in the old town, then the casinos after dark.",
         rows=[[242, 241], [246, 244, 247], [249, 255, 251], [252]], cover=252),
    dict(slug="salt", title="Salt", where="Alviso Marina County Park, San Jose", when="June 2025",
         note="Salt ponds at the southern end of San Francisco Bay.",
         rows=[[58], [57, 54], [60, 56], [61], [62, 52, 64], [63, 53]], cover=62, focus="50% 58%"),
    dict(slug="rose", title="Rose", where="Quzhou, Zhejiang", when="May 2025",
         note="A portrait session in a café.",
         rows=[[127, 136], [129, 132, 137], [138, 140], [142, 145, 146]], cover=132, focus="50% 30%"),
    dict(slug="fourth-of-july", title="Fourth of July", where="Yerba Buena Island, San Francisco", when="July 2025",
         note="From dusk to the fireworks, seen from the middle of the bay.",
         rows=[[114, 115], [117], [116, 118], [120, 122], [126, 124]], cover=117),
    dict(slug="guangzhou", title="Guangzhou", where="", when="January 2026",
         note="Museum halls by day, the Pearl River after dark.",
         rows=[[214, 216], [213, 215], [219, 308, 220], [221]], cover=221, focus="50% 45%"),
    dict(slug="evening-walk", title="Evening Walk", where="Fushan Park, Quzhou, Zhejiang", when="May 2025",
         note="Portraits in a park, from the last daylight until the lamps came on.",
         rows=[[43, 38, 40], [46, 49, 51]], cover=38, focus="50% 30%"),
    dict(slug="pacific", title="Pacific", where="Ocean Beach and Sutro Baths, San Francisco", when="July 2025",
         note="The western edge of the city on a clear afternoon.",
         rows=[[90], [95, 96], [89, 97], [101, 92], [91], [103, 100], [98, 104], [87, 88]], cover=104, focus="50% 42%"),
    dict(slug="dry-hills", title="Dry Hills", where="Hills east of San Jose, California", when="July 2025",
         note="Sunset from the grazing land above the valley.",
         rows=[[71], [73, 74], [72], [77, 79], [76], [68, 81], [80]], cover=80),
    dict(slug="subway", title="Subway", where="", when="April 2025",
         note="A subway car I built in Unreal Engine, photographed off a 4K monitor with a Canon 5D Mark IV, a 50 mm lens and a polarising filter, then finished to take the digital edge off. Final project for a photography class.",
         rows=[[398], [399, 397], [391], [393, 396], [394, 392], [395, 400]], cover=398, link=("How it was made", "works/virtual-subway/")),
    dict(slug="cherry-blossom", title="Cherry Blossom", where="Philadelphia", when="March 2026",
         note="The spring festival: blossom overhead, drums on the stage.",
         rows=[[173, 165, 171], [168, 172]], cover=165),
    dict(slug="zhuhai", title="Zhuhai", where="", when="January 2026",
         note="The opera house on the water, from late afternoon into the night.",
         rows=[[228, 222, 226], [230], [232], [240], [256, 238]], cover=232),
    dict(slug="tea-hills", title="Tea Hills", where="Wuyi, Jinhua, Zhejiang", when="December 2025",
         note="A tea estate built around a château-style hotel.",
         rows=[[200, 201], [197, 198], [202, 199], [206, 205]], cover=200, focus="50% 40%"),
    dict(slug="off-season", title="Off-season", where="Atlantic City and Cape May, New Jersey", when="March 2025",
         note="The Jersey Shore before the summer crowds.",
         rows=[[261], [390, 363], [267, 366], [368, 270], [373, 374], [372, 284], [289], [285], [384, 288]], cover=288),
    dict(slug="pennsylvania", title="Pennsylvania", where="Near Allentown", when="October 2025",
         note="A gorge overlook, an orchard and a small town in autumn.",
         rows=[[187], [183, 181], [182, 174], [188, 194, 189], [190, 193]], cover=187),
    dict(slug="elliot", title="Elliot", where="", when="February 2025",
         note="Elliot, a tabby kitten, and a lens held very close.",
         rows=[[299], [300, 302], [303, 301]], cover=300),
    dict(slug="february", title="February", where="Philadelphia", when="2025",
         note="Homework from my first weeks in a photography class: tail lights, a crescent moon, a squirrel.",
         rows=[[324], [320, 323], [337, 321]], cover=324),
]

# Rows of series tiles on the index page, by slug. Every series appears once.
HOME_ROWS = [
    ["above-the-fog", "rooftop"],
    ["macau", "salt"],
    ["rose", "fourth-of-july"],
    ["guangzhou", "evening-walk"],
    ["pacific", "dry-hills"],
    ["subway", "cherry-blossom"],
    ["zhuhai", "tea-hills"],
    ["off-season", "pennsylvania"],
    ["elliot", "february"],
]

# Opening slideshow of the index page: (photograph for wide screens, photograph for upright phones, series it links to).
SLIDES = [
    (16, 13, "above-the-fog"),
    (252, 247, "macau"),
    (58, 57, "salt"),
    (117, 114, "fourth-of-july"),
    (221, 308, "guangzhou"),
    (232, 228, "zhuhai"),
]

# Subject pages. A photograph can be listed under more than one subject; every photograph needs at least one.
SUBJECTS = [
    dict(slug="landscape", title="Landscape",
         photos=[4, 3, 7, 5, 2, 14, 13, 12, 16, 17, 58, 57, 60, 56, 62, 52, 71, 73, 74, 72, 77, 79, 68, 81, 80, 200, 201, 198, 187, 183, 285]),
    dict(slug="coast", title="Coast",
         photos=[90, 95, 96, 89, 97, 101, 91, 103, 100, 104, 228, 222, 226, 261, 390, 366, 284, 289, 285, 384, 288]),
    dict(slug="night", title="Night",
         photos=[251, 252, 255, 308, 220, 221, 114, 115, 117, 116, 118, 120, 122, 126, 124, 206, 205, 240, 256, 238, 324, 18, 20, 22, 25, 21, 80]),
    dict(slug="architecture", title="Architecture",
         photos=[242, 241, 244, 249, 251, 252, 64, 63, 214, 216, 213, 215, 219, 88, 201, 197, 202, 199, 206, 230, 232, 240, 222, 363, 267, 373, 374]),
    dict(slug="street", title="Street",
         photos=[246, 247, 53, 87, 98, 76, 74, 368, 372, 188, 194, 189, 168, 214, 7]),
    dict(slug="portrait", title="Portrait",
         photos=[127, 136, 129, 132, 137, 138, 140, 142, 145, 146, 43, 38, 40, 46, 49, 51, 18, 20, 22, 25, 21, 194, 189]),
    dict(slug="black-and-white", title="Black and White",
         photos=[398, 399, 397, 391, 393, 396, 394, 392, 395, 400, 267]),
    dict(slug="animals", title="Animals",
         photos=[95, 96, 101, 92, 81, 80, 270, 299, 300, 302, 303, 301, 337]),
    dict(slug="details", title="Details",
         photos=[1, 0, 17, 54, 61, 215, 255, 395, 181, 182, 174, 190, 193, 165, 171, 173, 172, 323, 321, 320]),
]

# Where a single photograph was taken, when that is more exact than its series' "where".
PLACE = {
    242: "Grand Lisboa", 244: "Grand Lisboa", 246: "Casino Lisboa", 252: "Wynn Palace, Cotai",
    249: "The Venetian Macao, Cotai", 251: "The Londoner Macao, Cotai",
    308: "Canton Tower", 220: "Chigang Pagoda", 221: "Haixin Bridge and Zhujiang New Town",
    232: "Zhuhai Opera House", 230: "Zhuhai Opera House", 240: "Zhuhai Opera House", 226: "Fisher Girl statue",
    90: "Ocean Beach, San Francisco", 95: "Ocean Beach, San Francisco", 96: "Ocean Beach, San Francisco",
    89: "Ocean Beach, San Francisco", 97: "Ocean Beach, San Francisco",
    91: "Sutro Baths, San Francisco", 101: "Sutro Baths, San Francisco", 103: "Sutro Baths, San Francisco",
    100: "Seal Rocks, San Francisco", 104: "Golden Gate Bridge",
    116: "Bay Bridge, east span", 117: "Bay Bridge and San Francisco",
    261: "Atlantic City", 390: "Steel Pier, Atlantic City", 363: "Atlantic City", 267: "Atlantic City",
    366: "Atlantic City", 368: "Atlantic City", 374: "Cape May", 289: "Cape May",
    284: "Cape May Lighthouse", 285: "Cape May Lighthouse", 384: "Sunset Beach, Cape May", 288: "Sunset Beach, Cape May",
    183: "Orchard near Allentown", 181: "Orchard near Allentown", 182: "Orchard near Allentown", 174: "Orchard near Allentown",
}

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
    # added later
    7: "Two long shadows fall across a dirt trail through golden grass.",
    14: "The sun sinking into the fog beyond a ridge, seen through grass stalks.",
    56: "A lump of salt standing in still red water.",
    60: "A white salt flat with a shallow pool winding through it.",
    68: "Layered ridges fading into haze under an orange sky.",
    72: "A rounded hill catching the last light above dry grass.",
    73: "The valley and its city at golden hour, seen past a slope scattered with rocks.",
    74: "Three people on a grassy hill looking out over the city below.",
    81: "A black cow standing by a fence post above the valley lights at dusk.",
    89: "Bands of sand, surf and sky on an empty beach.",
    92: "A dog lying in the sun on a concrete ledge.",
    100: "Sea stacks beyond a bank of yellow flowers.",
    103: "A grassy ledge and a ruined pool wall, with rocks offshore.",
    117: "The Bay Bridge strung with lights, leading to the San Francisco skyline at night.",
    138: "She crouches beside the sofa, looking down.",
    140: "She crouches beside the sofa and looks up at the camera.",
    142: "Close portrait: she smiles, shelves and warm light behind her.",
    183: "Dark red apples on a branch above rows of orchard trees and distant hills.",
    197: "A stone clock tower behind beds of red and yellow flowers.",
    199: "The clock tower at dusk beside a wet road.",
    226: "A statue of a woman holding a pearl aloft, on a rock in the sea.",
    267: "Cloud shadows on a blank white wall behind a row of lamp posts, in black and white.",
    284: "A boardwalk ramp zigzagging toward a distant lighthouse.",
    270: "A squirrel on a weathered boardwalk beside a steel rail.",
    363: "A pale tower rising behind a curved wall of blue glass.",
    374: "A Victorian porch hung with pink bows and mirror balls.",
    390: "An amusement pier with a Ferris wheel, seen from above the shoreline.",
    384: "The sun low over the sea under heavy cloud, a wreck on the horizon.",
    366: "A yellow bulldozer at the water's edge beyond dune grass.",
    393: "A door window beside a 'No exit' sign and graffiti.",
    165: "A branch of cherry blossom against a blue sky.",
    171: "Dense pink cherry blossom.",
    173: "A cherry tree in full bloom beside a road.",
    168: "Taiko drummers performing on an outdoor stage.",
    172: "Blossom-covered branches filling the frame.",
    299: "Elliot, a tabby kitten, lying on a dark duvet and looking at the camera.",
    300: "The cat's face in profile, its eye in sharp focus.",
    302: "The cat resting its chin, eyes half closed.",
    303: "The cat looking straight ahead, ears up.",
    301: "The cat's front paws stretched out on the bed.",
    324: "A city avenue at night seen from above, tail lights streaking red.",
    320: "A thin crescent moon in a violet sky beside a brick wall and a railing.",
    323: "Lights blurred behind a perforated metal screen.",
    337: "A squirrel clinging head-down to a tree trunk.",
    321: "A hand holding up a dry maple leaf against bare trees.",
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


def share(a, total):
    return f"(max-width: 760px) and (orientation: portrait) 100vw, {max(10, round(100 * a / total))}vw"


def row_html(row, img, *, eager=False, with_series=False):
    total = sum(ar(n) for n in row)
    cells = []
    for n in row:
        p = ph(n)
        big = p["files"][-1][0]
        st = f' data-settings="{E(p["settings"])}"' if p["settings"] else ""
        cap = place(n)
        if with_series:
            title = T(SERIES_OF[n]["title"])
            cap = title if not cap or cap == title else f"{title}{comma()}{cap}"
        cp = f' data-cap="{E(cap)}"' if cap else ""
        cells.append(f'<a class="ph" href="{img}{n:03d}-{big}.webp" style="--ar:{ar(n):.4f};--c:{p["color"]}" '
                     f'data-w="{p["w"]}" data-h="{p["h"]}" data-srcset="{srcset(n, img)}"{st}{cp}>'
                     f'{img_tag(n, img, share(ar(n), total), eager=eager)}</a>')
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
    text = (f'<span class="tile-text"><span class="tile-title">{E(T(s["title"]))}</span>'
            f'<span class="tile-meta">{E(meta) + "<br>" if meta else ""}{count(len(ids(s)))}</span></span>')
    sizes = "(max-width: 760px) and (orientation: portrait) 100vw, 50vw" if fixed else share(ar(n), total)
    pos = f';--pos:{s["focus"]}' if fixed and s.get("focus") else ""
    return (f'<a class="ph tile" href="{home}{s["slug"]}/" style="--ar:{ar(n):.4f};--c:{ph(n)["color"]}{pos}">'
            f'{img_tag(n, img, sizes, alt="")}{text}</a>')


def subjects_nav(home, current=""):
    cur = ' aria-current="page"'
    links = [f'<a href="{home}all/"{cur if current == "all" else ""}>{T("All")}<sup>{len(ORDER)}</sup></a>']
    links += [f'<a href="{home}{g["slug"]}/"{cur if current == g["slug"] else ""}>{E(T(g["title"]))}<sup>{len(g["photos"])}</sup></a>' for g in SUBJECTS]
    return f'<nav class="subjects" id="subjects" aria-label="{T("Subjects")}"><span class="subjects-label">{T("By subject")}</span>{"".join(links)}</nav>'


def base(rel):
    """From a page to photography/ itself, where img/ and assets/ are. `rel` is the page's place in its edition: "" or "macau/"."""
    return ("../" if rel else "") + ("../" if LANG == "zh" else "")


def page(*, title, desc, rel, body, og, v, series="", scripts=()):
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
  <p><a href="{site}">jichu.art</a></p>
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
      <span class="slide-cap"><b>{E(T(s["title"]))}</b><span>{E(meta_line(s))}<br>{count(len(ids(s)))}</span></span>
    </a>""")
        dots.append(f'<button class="dot" type="button" aria-label="{E(("Show " + s["title"]) if LANG == "en" else ("显示" + T(s["title"])))}"{" aria-current=" + chr(34) + "true" + chr(34) if first else ""}></button>')
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
    seen = [x for row in HOME_ROWS for x in row]
    assert sorted(seen) == sorted(BY_SLUG), "HOME_ROWS must list every series once"
    rows = []
    for row in HOME_ROWS:
        ss = [BY_SLUG[x] for x in row]
        total = sum(ar(s["cover"]) for s in ss)
        rows.append(f'<div class="row" style="--sum:{total:.4f};--n:{len(ss)}">' + "".join(tile(s, "", img, total) for s in ss) + "</div>")
    about = "".join(f"<p>{E(T(x))}</p>" for x in ABOUT)
    body = hero + f"""{subjects_nav("")}
<section class="series-index rows" id="series" aria-label="{T("Series")}">
<h2 class="hide">{T("Series")}</h2>
{chr(10).join(rows)}
</section>
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
    title, note = T(s["title"]), T(s["note"])
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
  <div class="row">{more}</div>
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
        t = T(SERIES_OF[n]["title"])
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
    body = head + '\n<div class="rows grid">\n' + "\n".join(row_html(r, img, eager=i == 0, with_series=True) for i, r in enumerate(rows)) + "\n</div>"
    return page(title=full, rel=rel, body=body, og=slug, v=v, series=title, scripts=("viewer.js",), desc=desc)


def build(root, v="1", strict=True, analytics=""):
    """Writes both editions and returns the pages' site-relative paths (for the sitemap)."""
    global LANG, ANALYTICS
    ANALYTICS = analytics
    assert len(ORDER) == len(set(ORDER)), "a photograph is used twice"
    tagged = {n for g in SUBJECTS for n in g["photos"]}
    assert tagged <= set(ORDER), f"SUBJECTS lists photographs that are in no series: {sorted(tagged - set(ORDER))}"
    assert set(ORDER) <= tagged, f"photographs without a subject: {sorted(set(ORDER) - tagged)}"
    assert set(PLACE) <= set(ORDER), f"PLACE names photographs that are in no series: {sorted(set(PLACE) - set(ORDER))}"
    slugs = [s["slug"] for s in SERIES] + [g["slug"] for g in SUBJECTS] + ["all"]
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
