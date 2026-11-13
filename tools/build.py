"""Generator for the static jichu.art site.

Project facts come from the old WordPress site, the résumé and the project READMEs on GitHub.
Output is plain HTML. Usage, from the repository root:  python3 tools/build.py . tools/manifest.json
"""
import html, json, os, sys

OUT = sys.argv[1]
MAN = json.load(open(sys.argv[2], encoding="utf-8"))
SITE = "https://jichu.art"
E = html.escape
ASSET_V = "27"   # bump when site.css or the scripts change, so browsers do not reuse a cached copy

# Visitor statistics (GoatCounter: no cookies, so no consent banner). Empty = off.
# To switch on: create a free account at goatcounter.com, choose a code (the "mysite" of mysite.goatcounter.com),
# put that code between the quotes and rebuild. Every page of the site, photography included, then reports its views.
GOATCOUNTER = "jichu"
ANALYTICS = (f'\n<script data-goatcounter="https://{GOATCOUNTER}.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>'
             if GOATCOUNTER else "")

EMAIL = "maojichu@gmail.com"
SOCIAL = [
    ("LinkedIn", "https://www.linkedin.com/in/jichu-mao-a3a980226/", "briefcase"),
    ("GitHub", "https://github.com/jichumao", "code"),
    ("YouTube", "https://www.youtube.com/@supermao6744", "play"),
]

# Plain line icons (24px grid). Generic shapes only, no brand marks.
ICONS = {
    "mail": '<rect x="3" y="5.5" width="18" height="13" rx="1.5"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    "briefcase": '<rect x="3" y="7.5" width="18" height="12" rx="1.5"/><path d="M9 7.5V6a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 6v1.5"/><path d="M3 13h18"/>',
    "code": '<path d="m8.5 8-4.5 4 4.5 4"/><path d="m15.5 8 4.5 4-4.5 4"/><path d="m13.5 5.5-3 13"/>',
    "play": '<circle cx="12" cy="12" r="9"/><path d="m10 8.3 6.2 3.7-6.2 3.7z"/>',
    "external": '<path d="M14 5h5v5"/><path d="m19 5-8.5 8.5"/><path d="M11 7H5.5v11.5H17V13"/>',
    "paper": '<path d="M7 3.5h7l4 4v13H7z"/><path d="M14 3.5v4h4"/><path d="M10 12.5h5M10 16h5"/>',
    # facts row
    "camera": '<path d="M4 8h3l1.5-2.5h7L17 8h3v11H4z"/><circle cx="12" cy="13.2" r="3.4"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15" rx="1.5"/><path d="M3.5 9.5h17M8 3v4M16 3v4"/>',
    "user": '<circle cx="12" cy="8.5" r="3.2"/><path d="M5.5 19.5c.6-3.5 3.1-5.5 6.5-5.5s5.9 2 6.5 5.5"/>',
    "users": '<circle cx="9" cy="8.5" r="3"/><path d="M3.5 19c.5-3.2 2.7-5 5.5-5s5 1.8 5.5 5"/><path d="M15.5 5.8a3 3 0 0 1 0 5.4M17 14.3c1.9.6 3.1 2.2 3.5 4.7"/>',
    "book": '<path d="M5 4.5h10.5a2 2 0 0 1 2 2v13H7a2 2 0 0 1-2-2z"/><path d="M5 17.5a2 2 0 0 1 2-2h10.5"/>',
    "chip": '<rect x="7" y="7" width="10" height="10" rx="1"/><path d="M10 3.5V7M14 3.5V7M10 17v3.5M14 17v3.5M3.5 10H7M3.5 14H7M17 10h3.5M17 14h3.5"/>',
    "layers": '<path d="m12 4 8 4-8 4-8-4z"/><path d="m4 12 8 4 8-4M4 16l8 4 8-4"/>',
    "pin": '<path d="M12 20.5s6-5.4 6-10.2a6 6 0 0 0-12 0c0 4.8 6 10.2 6 10.2z"/><circle cx="12" cy="10" r="2.2"/>',
    # feature rows
    "grid": '<rect x="4" y="4" width="16" height="16" rx="1"/><path d="M4 9.3h16M4 14.7h16M9.3 4v16M14.7 4v16"/>',
    "repeat": '<path d="M4.5 12a7.5 7.5 0 0 1 12.8-5.3L19.5 9"/><path d="M19.5 4.5V9H15"/><path d="M19.5 12a7.5 7.5 0 0 1-12.8 5.3L4.5 15"/><path d="M4.5 19.5V15H9"/>',
    "sparkle": '<path d="M12 3.5v5M12 15.5v5M3.5 12h5M15.5 12h5M6.3 6.3l3 3M14.7 14.7l3 3M17.7 6.3l-3 3M9.3 14.7l-3 3"/>',
    "sun": '<circle cx="12" cy="12" r="3.5"/><path d="M12 3.5V6M12 18v2.5M3.5 12H6M18 12h2.5M6 6l1.7 1.7M16.3 16.3 18 18M18 6l-1.7 1.7M7.7 16.3 6 18"/>',
    "cube": '<path d="m12 3.5 7.5 4.2v8.6L12 20.5l-7.5-4.2V7.7z"/><path d="M4.5 7.7 12 12l7.5-4.3M12 12v8.5"/>',
    "lens": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3.2"/>',
    "image": '<rect x="3.5" y="5" width="17" height="14" rx="1.5"/><circle cx="8.5" cy="10" r="1.5"/><path d="m4 17 5-4.5 3.5 3 3-2.5 4.5 4"/>',
    "sliders": '<path d="M4.5 7h9.5M18 7h1.5M4.5 12h3.5M12 12h7.5M4.5 17h10.5"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="17" cy="17" r="2"/>',
    "zap": '<path d="M13 3.5 5.5 13.5H12l-1 7 7.5-10H12z"/>',
    "filter": '<path d="M4 5.5h16l-6 7.5v5l-4 2v-7z"/>',
    "wind": '<path d="M3.5 9h10a2.5 2.5 0 1 0-2.5-2.5M3.5 13h14a2.5 2.5 0 1 1-2.5 2.5M3.5 17h6"/>',
    "triangle": '<path d="M12 4.5 20 19H4z"/><path d="m8 11.75 4 7.25 4-7.25z"/>',
    "droplet": '<path d="M12 3.5c3 3.6 5.5 6.7 5.5 10a5.5 5.5 0 0 1-11 0c0-3.3 2.5-6.4 5.5-10z"/>',
    "mountain": '<path d="m3.5 18.5 5.5-9 3.5 5 2.5-3.5 5.5 7.5z"/>',
    "tree": '<path d="M12 20.5V10M12 14.5 8 11M12 12.5l4-4M8 11V7.5M16 8.5V5M12 10V6"/>',
    "curve": '<path d="M4 18c3-10 7-10 8-6s5 4 8-6"/>',
    "joints": '<circle cx="6" cy="17" r="2"/><circle cx="12" cy="9" r="2"/><circle cx="18.5" cy="14" r="2"/><path d="m7.2 15.4 3.6-4.8M13.8 10.2l3 2.6"/>',
    "particles": '<circle cx="7" cy="8" r="1.4"/><circle cx="15" cy="6" r="1.4"/><circle cx="18" cy="13" r="1.4"/><circle cx="10.5" cy="13.5" r="1.4"/><circle cx="6" cy="18" r="1.4"/><circle cx="14.5" cy="18.5" r="1.4"/>',
}
FACT_ICONS = {"Year": "calendar", "Team": "users", "Type": "user", "Built on": "layers", "Built with": "layers",
              "Tested on": "chip", "Reference": "paper", "Recorded at": "pin", "Shot with": "camera", "Maya plugin": "layers", "Houdini plugin": "layers"}

def icon(name):
    return (f'<svg class="icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')

CATEGORIES = [("rendering", "Rendering & GPU"), ("tools", "Tools"), ("games", "Games"), ("animation", "Animation"), ("art", "Art")]
CAT_LABEL = dict(CATEGORIES)

# ---------------------------------------------------------------- content

def shot(key, caption="", alt=""):
    return {"key": key, "caption": caption, "alt": alt or caption}

def clip(name, caption="", alt=""):
    return {"clip": name, "caption": caption, "alt": alt or caption}

GH = "https://github.com/jichumao/"

# Order on the home page: rendering and GPU work first (most complex first), then tools and
# games, then content-creation pieces; newer work first within each group.
#
# Per project:
#   year, kind      shown above the title on the card and in the facts row
#   tags            tech stack, written the way a résumé or job posting spells it
#   excerpt         card text and meta description
#   lead            opening sentence of the project page
#   facts           (label, value) pairs under the page header
#   stats           measured results as (figure, what it measures); leave out when there are none
#   blocks          text blocks (p, html, ul) go in the left column, the rest in the media column
PROJECTS = [
  {
    "slug": "world-space-restir", "img": "world-space-restir",
    "title": "World-Space ReSTIR in Vulkan", "cats": ["rendering"], "year": "2024", "kind": "Team of two",
    "tags": ["C++", "Vulkan", "GLSL", "Ray Tracing", "Global Illumination", "ReSTIR"],
    "excerpt": "World-space global illumination in a Vulkan ray-tracing pipeline. About 40% more accurate than screen-space ReSTIR in large scenes, for roughly 5% more render time.",
    "lead": "A world-space global illumination method in a Vulkan ray-tracing pipeline. Path samples are cached in a spatial hash grid and reused across frames and neighbouring cells.",
    "cover_alt": "Two scenes, each shown twice: a subway car and a toy robot as rendered, and the same views coloured by the hash-grid cells the renderer shades from",
    "facts": [("Year", "2024"), ("Team", "Two people, with Zhiyi Zhou"), ("Built on", "Nvidia’s Vulkan ray-tracing renderer")],
    "stats": [("≈40%", "higher accuracy than screen-space ReSTIR in large scenes"), ("≈5%", "extra render time"),
              ("1.3 M", "triangles in the subway test scene, at 1 sample per pixel")],
    "links": [("Source code", "https://github.com/zhiyi1801/CIS-565-2024Fall-Final", "code"), ("Paper", "https://wangningbei.github.io/2023/ReSTIR.html", "paper")],
    "blocks": [
      ("html", '<p>An implementation of <a href="https://wangningbei.github.io/2023/ReSTIR.html">World-Space Spatiotemporal Path Resampling for Path Tracing</a> with Vulkan ray tracing, made together with Zhiyi Zhou.</p>'),
      ("p", "The renderer can switch between three paths: the ray-tracing pipeline, ray queries in a compute shader, and world-space ReSTIR."),
      ("h3", "My part"),
      ("features", [
          ("grid", "World-space hash grid", "A compound key of position and normal groups samples that are close in space and in orientation. Cells grow with distance from the camera."),
          ("repeat", "Temporal and spatial reuse", "Motion vectors from the camera transform carry last frame’s samples forward. Neighbours come from the hash grid and are checked by angle and depth before they join the reservoir."),
          ("sparkle", "Denoising", "Intel Open Image Denoise on albedo, normal and noisy colour. The round trip through the CPU costs about 250 ms per frame, which the project lists as its main bottleneck."),
      ]),
      ("h2", "One frame, five passes"),
      ("steps", [("G-buffer", "and initial path sampling"), ("Hash grid", "built in world space"), ("Resampling", "temporal, then spatial"),
                 ("Shading", "direct and indirect light"), ("Post-process", "Open Image Denoise")]),
      ("h2", "Hash grid"),
      ("gallery", [clip("restir-hash-grid", "Hash grid cells on the robot-toon scene"), shot("hash-grid-sponza", "Hash grid cells on Sponza")]),
      ("h2", "World-space ReSTIR DI"),
      ("gallery", [clip("restir-di", "Light samples cached in the grid and reused across frames")]),
      ("h2", "Spatiotemporal resampling"),
      ("gallery", [clip("restir-spatiotemporal", "Temporal and spatial reuse")]),
      ("label", "Sponza at 1 sample per pixel"),
      ("gallery", [shot("sponza-1spp-ours", "Ours"), shot("sponza-1spp-path-tracing", "Path tracing")]),
      ("label", "Rough surface"),
      ("gallery", [shot("rough-ours", "Ours"), shot("rough-path-tracing", "Path tracing")]),
      ("label", "Smooth surface"),
      ("gallery", [shot("smooth-ours", "Ours"), shot("smooth-path-tracing", "Path tracing")]),
      ("h2", "Subway scene: 1 sample per pixel, 1.3 million triangles"),
      ("gallery", [shot("subway-ours", "Ours"), shot("subway-path-tracing", "Path tracing"), shot("subway-hash-grid", "Hash grid"), shot("subway-reference", "Reference")]),
      ("h2", "Result"),
      ("gallery", [shot("restir-gi", "World-space ReSTIR GI"), shot("sponza-hash-grid-split", "Sponza, with the hash grid shown across the diagonal")]),
      ("h2", "Denoising"),
      ("gallery-wide", [shot("denoise", "Open Image Denoise uses albedo and normal buffers to clean up the noisy colour output")]),
      ("h2", "Performance"),
      ("gallery-wide", [shot("chart-initial-sampling", "Initial sampling time by scene"), shot("chart-passes", "Time per pass by scene")])
    ],
  },
  {
    "slug": "cuda-path-tracer", "img": "cuda-path-tracer",
    "title": "CUDA Path Tracer", "cats": ["rendering"], "year": "2024", "kind": "Individual project",
    "tags": ["C++", "CUDA", "GPU Programming", "Path Tracing", "glTF", "Performance Optimization"],
    "excerpt": "A GPU path tracer in CUDA with glTF scenes, physically based materials, depth of field and environment lighting. Stream compaction cuts frame time from 25.7 to 18.2 ms in open scenes.",
    "lead": "A GPU path tracer written in CUDA. It loads glTF meshes and materials and simulates light transport for soft shadows, caustics and depth of field, with stream compaction and bounding-box culling to cut the work per frame.",
    "cover_alt": "Path-traced renders: a giant rubber duck in a living room, a toy dog with two rubber ducks, and a golden dragon",
    "facts": [("Year", "2024"), ("Type", "Individual project"), ("Tested on", "RTX 4090, i7-13700K, Windows 11")],
    "stats": [("25.7 → 18.2 ms", "per frame with stream compaction, open scene"), ("20–40%", "faster with bounding-box culling on low- to mid-poly models"),
              ("43,200", "samples per pixel in the dragon render")],
    "links": [("Source code", GH + "CUDA-Path-Tracer", "code")],
    "blocks": [
      ("p", "The highlight renders use 5,000 samples per pixel or more, with up to 8 bounces per ray."),
      ("h3", "Visual features"),
      ("features", [
          ("droplet", "BSDFs", "Diffuse, glossy, perfectly specular and refractive"),
          ("sparkle", "Anti-aliasing", "Stochastic sampling"),
          ("lens", "Depth of field", "Physically based, with a thin-lens camera"),
          ("cube", "glTF meshes", "Loaded with texture mapping"),
          ("image", "Environment maps", "HDR lighting"),
          ("sliders", "Tone mapping", "ACES and Reinhard, plus gamma correction"),
      ]),
      ("h3", "Performance work"),
      ("features", [
          ("filter", "Stream compaction", "Removes finished rays. In open scenes, frame time drops from 25.7 ms to 18.2 ms."),
          ("cube", "Bounding-box culling", "20–40% faster on low- to mid-poly glTF models"),
          ("zap", "Material sorting", "Measured too, and turned out slower on small scenes"),
      ]),
      ("h2", "Highlights"),
      ("gallery", [shot("duck-room", "Rubber duck lit by an environment map, 14,496 spp at 1200 × 1200")]),
      ("gallery", [shot("duck-doggy-duck", "Duck-Doggy-Duck, 5,000 spp"), shot("dragon", "The Dragon Beneath Starlit Skies, 43,200 spp"),
                   shot("shanghai-nights", "Shanghai Nights, 5,000 spp"), shot("stone-cat", "Stone Cat Guardian, 5,000 spp")]),
      ("h2", "Material shading"),
      ("gallery", [shot("bsdf-diffuse", "Diffuse"), shot("bsdf-diffuse-specular", "Partially diffuse and specular"), shot("bsdf-specular", "Perfectly specular"), shot("bsdf-refractive", "Refractive")]),
      ("h2", "Anti-aliasing"),
      ("gallery", [shot("aa-off", "Anti-aliasing off"), shot("aa-on", "Anti-aliasing on")]),
      ("h2", "Depth of field"),
      ("label", "Focal length 9.0, lens radius 0, 0.5 and 1.0"),
      ("gallery", [shot("dof-lens-00", "Lens radius 0.0"), shot("dof-lens-05", "Lens radius 0.5"), shot("dof-lens-10", "Lens radius 1.0")]),
      ("label", "Lens radius 0.1, focal length 5, 8 and 15"),
      ("gallery", [shot("dof-focal-05", "Focal length 5.0"), shot("dof-focal-08", "Focal length 8.0"), shot("dof-focal-15", "Focal length 15.0")]),
      ("h2", "glTF meshes and textures"),
      ("gallery", [shot("gltf-untextured", "Model without texture"), shot("gltf-textured", "Texture sampled with interpolated UVs")]),
      ("h2", "Environment map"),
      ("gallery", [shot("env-off", "Environment map off"), shot("env-on", "Environment map on")]),
      ("h2", "Tone mapping"),
      ("gallery", [shot("tone-none", "No tone mapping"), shot("tone-reinhard", "Reinhard"), shot("tone-aces", "ACES"), shot("gamma", "With gamma correction")]),
      ("h2", "Performance"),
      ("gallery-wide", [shot("chart-compaction-depth", "Stream compaction: rays remaining at each trace depth, open scene"),
                        shot("chart-compaction-scene", "Stream compaction: render time, open and closed scene"),
                        shot("chart-bbox-culling", "Bounding-box culling: frame rate by triangle count")])
    ],
  },
  {
    "slug": "webgpu-clustered-shading", "img": "webgpu-clustered-shading",
    "title": "WebGPU Forward+ and Clustered Deferred Shading", "cats": ["rendering"], "year": "2024", "kind": "Individual project",
    "tags": ["TypeScript", "WebGPU", "WGSL", "Compute Shaders", "Deferred Shading", "Real-Time Rendering"],
    "excerpt": "Forward+ and clustered deferred shading in the browser. With 5,000 moving lights at 4K, clustered deferred runs above 100 fps where naive forward shading manages 3.",
    "lead": "Three ways to light the Sponza atrium with thousands of moving point lights, in the browser: naive forward, Forward+ and clustered deferred shading, compared at 4K.",
    "cover_alt": "Sponza atrium lit by thousands of coloured point lights, with two close views of its curtains",
    "facts": [("Year", "2024"), ("Type", "Individual project"), ("Tested on", "RTX 4090, i7-13700K, Windows 11")],
    "stats": [("3 → 100+ fps", "5,000 lights at 4K, naive forward against clustered deferred"), ("550.8 → 15.1 ms", "per frame at 8,192 lights"),
              ("0.5 ms", "per frame at 256 lights with clustered deferred")],
    "links": [("Live demo", "https://jichu.art/Project4-WebGPU-Forward-Plus-and-Clustered-Deferred/", "play"),
              ("Source code", GH + "Project4-WebGPU-Forward-Plus-and-Clustered-Deferred", "code")],
    "blocks": [
      ("p", "The project compares the three shading methods at high resolution with thousands of lights:"),
      ("features", [
          ("layers", "Three pipelines", "Forward, clustered forward (Forward+) and clustered deferred"),
          ("grid", "Light clustering", "A compute shader splits the view frustum into clusters, logarithmically along depth, and assigns lights to them"),
          ("sparkle", "Bloom", "Optional post-process"),
          ("image", "G-buffer", "Compressed layout"),
      ]),
      ("p", "The live demo needs a browser with WebGPU."),
      ("gallery-wide", [shot("sponza-4k-5000-lights", "Sponza at 4K with 5,000 lights")]),
      ("gallery", [clip("webgpu-moving-lights", "Random lights moving through the scene")]),
      ("h2", "G-buffer"),
      ("gallery", [shot("gbuffer-position", "Position"), shot("gbuffer-normal", "Normal"), shot("gbuffer-color", "Colour"), shot("gbuffer-depth", "Depth")]),
      ("h2", "Frame time at 4K"),
      ("table", {"head": ["Lights", "Naive", "Clustered forward", "Clustered deferred"],
                 "rows": [["256", "18.8 ms", "1.6 ms", "0.5 ms"], ["512", "34.4 ms", "3.4 ms", "1.1 ms"], ["1,024", "71.4 ms", "7.0 ms", "2.3 ms"],
                          ["2,048", "142.8 ms", "14.2 ms", "4.1 ms"], ["4,096", "273.6 ms", "27.7 ms", "8.2 ms"], ["8,192", "550.8 ms", "52.6 ms", "15.1 ms"]]}),
      ("gallery-wide", [shot("chart-lights", "Frame time by number of lights")])
    ],
  },
  {
    "slug": "vulkan-grass-rendering", "img": "vulkan-grass-rendering",
    "title": "Vulkan Grass Rendering", "cats": ["rendering"], "year": "2024", "kind": "Individual project",
    "tags": ["C++", "Vulkan", "GLSL", "Compute Shaders", "Tessellation", "Real-Time Rendering"],
    "excerpt": "Real-time grass in Vulkan. A compute shader simulates and culls every blade; with 32,768 blades, culling lifts the frame rate from 70 to 228 fps.",
    "lead": "A grass simulator and renderer on the Vulkan API. Every blade is a Bézier curve: a compute shader applies gravity, wind and recovery forces and culls the blades that do not contribute, then tessellation shaders turn the rest into geometry.",
    "cover_alt": "Six views of real-time grass: a field, dense blades up close, sparse blades on bare ground and tessellated blades in wireframe",
    "facts": [("Year", "2024"), ("Type", "Individual project"), ("Tested on", "RTX 4090, i7-13700K, Windows 11")],
    "stats": [("70.2 → 228.2 fps", "with orientation, frustum and distance culling, 32,768 blades"),
              ("219.5 fps", "at 1,048,576 blades with culling, against 74.2 without")],
    "links": [("Source code", GH + "Vulkan-Grass-Rendering", "code"),
              ("Paper", "https://www.cg.tuwien.ac.at/research/publications/2017/JAHRMANN-2017-RRTG/JAHRMANN-2017-RRTG-draft.pdf", "paper")],
    "blocks": [
      ("html", '<p>It follows the paper <a href="https://www.cg.tuwien.ac.at/research/publications/2017/JAHRMANN-2017-RRTG/JAHRMANN-2017-RRTG-draft.pdf">Responsive Real-Time Grass Rendering for General 3D Scenes</a> by Jahrmann and Wimmer.</p>'),
      ("features", [
          ("wind", "Physics", "Gravity, wind and recovery forces on every blade, in a compute shader"),
          ("filter", "Culling", "Orientation, view-frustum and distance tests in the same shader"),
          ("triangle", "Level of detail", "Tessellation level follows each blade’s distance to the camera"),
      ]),
      ("gallery-wide", [clip("grass-showcase", "8,192 grass blades with dynamic tessellation levels")]),
      ("h2", "Level of detail"),
      ("gallery", [clip("grass-lod", "Tessellation level follows the distance to the camera")]),
      ("h2", "Culling"),
      ("gallery", [clip("grass-culling-orientation", "Orientation culling"), clip("grass-culling-frustum", "View-frustum culling"), clip("grass-culling-distance", "Distance culling")]),
      ("h2", "Performance"),
      ("gallery-wide", [shot("chart-culling", "Frame rate with each culling method, 32,768 blades"), shot("chart-blade-count", "Frame rate by number of blades, with and without culling")])
    ],
  },
  {
    "slug": "cuda-flocking", "img": "cuda-flocking",
    "title": "CUDA Flocking", "cats": ["rendering"], "year": "2024", "kind": "Individual project",
    "tags": ["C++", "CUDA", "GPU Programming", "Parallel Computing", "Spatial Data Structures", "Performance Optimization"],
    "excerpt": "Reynolds’ boids simulated on the GPU with CUDA. A coherent uniform grid runs 100,000 boids at 2,677 fps where brute force manages 43.",
    "lead": "A flocking simulation in CUDA after Craig Reynolds’ boids model: cohesion, separation and alignment for up to ten million boids, with three neighbour searches compared.",
    "cover_alt": "Clouds of coloured boids flocking inside a cube",
    "facts": [("Year", "2024"), ("Type", "Individual project"), ("Tested on", "RTX 4090, i7-13700K, Windows 11")],
    "stats": [("43 → 2,677 fps", "100,000 boids, brute force against the coherent uniform grid"),
              ("18 fps", "at 10 million boids on the coherent grid, where brute force shows 0"),
              ("3", "neighbour-search implementations compared")],
    "links": [("Source code", GH + "CUDA-Flocking", "code")],
    "blocks": [
      ("features", [
          ("particles", "Three rules", "Cohesion, separation and alignment"),
          ("layers", "Brute force", "Every boid checks every other boid"),
          ("grid", "Scattered uniform grid", "Boids are binned into cells, so only nearby cells are searched"),
          ("zap", "Coherent uniform grid", "Boid data is reordered to follow the cells, which makes memory access contiguous"),
      ]),
      ("p", "Finer cells helped more than expected. Above 100,000 boids, a cell width of 1× the rule distance beat 2×, although 27 cells are checked instead of 8: the coherent grid then reaches 791 fps at 1 million boids and 18 fps at 10 million."),
      ("gallery", [clip("flocking-swarm", "", "Boids flocking"), clip("flocking-dense", "", "A dense flock filling the simulation cube")]),
      ("h2", "Frames per second, cell width 2×, no visualization"),
      ("table", {"head": ["Boids", "Brute force", "Scattered grid", "Coherent grid"],
                 "rows": [["5,000", "1,206.4", "2,788.5", "2,758.6"], ["100,000", "43.0", "2,578.5", "2,676.8"], ["1,000,000", "0.6", "312.1", "455.7"],
                          ["10,000,000", "0.0", "4.0", "6.5"]]}),
      ("gallery", [shot("chart-boids-2x", "Frame rate by number of boids, cell width 2×"), shot("chart-boids-1x", "Frame rate by number of boids, cell width 1×"),
                   shot("chart-block-size", "Frame rate by block size"), shot("chart-visualization", "Coherent grid with and without visualization")]),
    ],
  },
  {
    "slug": "cuda-stream-compaction", "img": "stream-compaction",
    "title": "CUDA Stream Compaction", "cats": ["rendering"], "year": "2024", "kind": "Individual project",
    "tags": ["C++", "CUDA", "GPU Programming", "Parallel Algorithms", "Performance Profiling", "Nsight Compute"],
    "excerpt": "Scan and stream compaction on the GPU in CUDA, profiled with Nsight Compute. The work-efficient scan handles 134 million elements in 26 ms; the CPU needs 190.",
    "lead": "Prefix-sum scan and stream compaction in CUDA: a CPU baseline, a naive GPU scan, a work-efficient GPU scan and Thrust, timed against each other and profiled with Nsight Compute.",
    "cover_alt": "Diagram of stream compaction: a row of 32 cells, 16 of them filled, and below it the same 16 packed to the front, each joined to its new position by a curve",
    "facts": [("Year", "2024"), ("Type", "Individual project"), ("Tested on", "RTX 4090, i7-13700K, Windows 11")],
    "stats": [("190.1 → 26.2 ms", "exclusive scan of 134 million elements, CPU against the work-efficient GPU scan"),
              ("251.3 → 31.4 ms", "stream compaction, fastest CPU version against the GPU"),
              ("43.66%", "under-used streaming multiprocessors in the up-sweep, found with Nsight Compute")],
    "links": [("Source code", GH + "Stream-Compaction", "code")],
    "blocks": [
      ("p", "Stream compaction removes the elements a later stage no longer needs, such as terminated rays in a path tracer. It is built on scan, so most of the work went into the scan."),
      ("features", [
          ("layers", "CPU baseline", "Scan and compaction in plain loops, used to check the GPU results"),
          ("grid", "Naive GPU scan", "One kernel launch per level, working in global memory"),
          ("zap", "Work-efficient GPU scan", "Up-sweep and down-sweep over a balanced tree, with arrays padded to a power of two"),
          ("filter", "Stream compaction", "Map to booleans, scan, then scatter"),
          ("chip", "Thrust", "thrust::exclusive_scan as the reference"),
      ]),
      ("h3", "What the profiler showed"),
      ("p", "In Nsight Compute the up-sweep takes most of the time: 28.38 ms per kernel on average, against 20.26 ms for the down-sweep. Some streaming multiprocessors run up to 43.66% below the average load, so the next step would be to balance the work across them and tighten memory access."),
      ("h2", "Exclusive scan, 134 million elements"),
      ("bars", {"unit": "ms", "rows": [("CPU", 190.1, False), ("Naive GPU", 35.0, False), ("Work-efficient GPU", 26.2, True), ("Thrust", 2.9, False)]}),
      ("note", "Block size 256, power-of-two array. Thrust stays well ahead of both hand-written versions."),
      ("h2", "Stream compaction, 134 million elements"),
      ("bars", {"unit": "ms", "rows": [("CPU, with scan", 565.4, False), ("CPU, without scan", 251.3, False), ("Work-efficient GPU", 31.4, True)]}),
      ("h2", "Charts and profile"),
      ("gallery", [shot("chart-size", "Run time by array size"), shot("chart-block-size", "Run time by block size"),
                   shot("nsight-compute", "Nsight Compute profile of the work-efficient scan")]),
    ],
  },
  {
    "slug": "physically-based-shaders", "old": "physically-based-shaders", "img": "physically-based-shaders",
    "title": "Physically-Based Shaders", "cats": ["rendering"], "year": "2023", "kind": "Individual project",
    "tags": ["C++", "OpenGL", "GLSL", "PBR", "Image-Based Lighting", "Qt"],
    "excerpt": "Physically based shading in OpenGL: a Cook-Torrance BRDF with image-based lighting, plus metallic, roughness, normal-map and displacement controls.",
    "lead": "Physically based shading in OpenGL: the Cook-Torrance model in a PBR pipeline, lit by environment maps, with custom scenes and models.",
    "cover_alt": "A turquoise skull and an engraved revolver rendered with physically based shading, above one red metal sphere shown five times from mirror-smooth to fully rough",
    "facts": [("Year", "2023"), ("Type", "Individual project"), ("Built with", "C++, OpenGL, GLSL, Qt"), ("Reference", "Real Shading in Unreal Engine 4 (Karis, 2013)")],
    "links": [("Source code", GH + "Physically-based-Shader", "code")],
    "blocks": [
      ("html", '<p>Based on the paper <a href="https://blog.selfshadow.com/publications/s2013-shading-course/karis/s2013_pbs_epic_notes_v2.pdf">“Real Shading in Unreal Engine 4”</a>, the PBR implementation uses the Cook-Torrance model in a physically based rendering pipeline, along with image-based lighting, as well as custom scenes and environment maps.</p>'),
      ("features", [
          ("droplet", "Material controls", "Albedo, metallic, roughness and ambient occlusion"),
          ("cube", "Surface detail", "Normal mapping and displacement mapping"),
          ("image", "Scenes", "Loads environment maps, JSON scenes and OBJ models"),
      ]),
      ("h2", "Renders (RGB = 1, 1, 1)"),
      ("gallery", [shot("white-metal0-rough0", "0 Metallic 0 Roughness"), shot("white-metal1-rough0", "1 Metallic 0 Roughness"),
                   shot("white-metal1-rough025", "1 Metallic 0.25 Roughness")]),
      ("h2", "Renders (RGB = 0.5, 0, 0)"),
      ("gallery", [shot("red-metal0-rough0", "0 Metallic 0 Roughness"), shot("red-metal1-rough0", "1 Metallic 0 Roughness"),
                   shot("red-metal1-rough025", "1 Metallic 0.25 Roughness"), shot("red-metal1-rough050", "1 Metallic 0.5 Roughness"),
                   shot("red-metal1-rough075", "1 Metallic 0.75 Roughness"), shot("red-metal1-rough100", "1 Metallic 1 Roughness")]),
      ("h2", "Normal Mapping and Displacement Mapping"),
      ("gallery", [shot("displacement-000", "With no Displacement"), shot("displacement-020", "With 0.20 Displacement"),
                   shot("displacement-040", "With 0.40 Displacement"), shot("displacement-100", "With 1.00 Displacement")]),
      ("h2", "Other JSON Scenes"),
      ("gallery", [shot("scene-skull", "A Skull"), shot("scene-gun", "Gun")])
    ],
  },
  {
    "slug": "mini-minecraft", "old": "hello-world", "img": "mini-minecraft",
    "title": "Mini Minecraft", "cats": ["games"], "year": "2023", "kind": "Team project",
    "tags": ["C++", "OpenGL", "GLSL", "Qt", "Procedural Generation", "Game Development"],
    "excerpt": "A Minecraft-like game in C++ and OpenGL with no game engine. I built the procedural terrain, the biomes, texture animation and shape-grammar buildings.",
    "lead": "A Minecraft-like game written in C++ and OpenGL. We did not use a game engine: every visual effect is built from OpenGL and Qt.",
    "cover_alt": "Mini Minecraft title over procedurally generated voxel terrain under a purple sky",
    "facts": [("Year", "2023"), ("Type", "Team project"), ("Built with", "C++, OpenGL, GLSL, Qt 6")],
    "links": [("Source code", GH + "miniMC", "code")],
    "blocks": [
      ("p", "I mainly implemented the following features in this game:"),
      ("features", [
          ("mountain", "Procedural terrain", "Four biomes: grassland, desert, mountain and snowfield"),
          ("image", "Texturing", "Textures and texture animation"),
          ("tree", "Procedural assets", "Placed procedurally across the terrain"),
          ("layers", "Procedural buildings", "Shape grammars (L-systems)"),
          ("zap", "Rendering", "Cube-face rendering optimization, custom culling and shadows"),
      ]),
      ("label", "On YouTube:"),
      ("embed", {"src": "https://www.youtube-nocookie.com/embed/gNmsVbQdZX0", "title": "Mini Minecraft demo on YouTube"}),
      ("label", "On Bilibili:"),
      ("embed", {"src": "https://player.bilibili.com/player.html?bvid=BV1Ru4y1n7Bg&autoplay=0", "title": "Mini Minecraft demo on Bilibili"}),
      ("gallery-wide", [shot("screenshot-1", "", "Mini Minecraft title screen over procedural terrain"), shot("screenshot-2", "", "Mini Minecraft in-game screenshot")]),
      ("h2", "Biomes"),
      ("gallery", [shot("biome-grassland", "Grassland"), shot("biome-desert", "Desert"), shot("biome-snow", "Snowfield"), shot("biome-mountain", "Mountain")]),
    ],
  },
  {
    "slug": "virtual-subway", "old": "", "img": "virtual-subway",
    "title": "Virtual Subway", "cats": ["art"], "year": "2025", "kind": "Individual project",
    "tags": ["Unreal Engine", "Photography", "Black and White"],
    "excerpt": "A subway car built in Unreal Engine, then photographed off a 4K monitor with a Canon 5D Mark IV and a polarising filter.",
    "lead": "A subway car that exists only in Unreal Engine, photographed with a real camera: a Canon 5D Mark IV pointed at a 4K monitor.",
    "cover_alt": "Black-and-white photograph of an empty subway car interior, benches along both sides",
    "links": [("See it as a photo series", SITE + "/photography/subway/", "external")],
    "facts": [("Year", "2025"), ("Type", "Individual project"), ("Built with", "Unreal Engine"), ("Shot with", "Canon 5D Mark IV, 50 mm lens, polarising filter")],
    "blocks": [
      ("p", "The subject is not a real place: I built the subway scene in Unreal Engine on my own computer, then photographed it the way I would photograph a real one."),
      ("p", "Each frame is a photograph of my 4K monitor, taken with a Canon 5D Mark IV and a 50 mm lens with a polarising filter on it. Afterwards I edited the photographs to take the digital edge off the image."),
      ("p", "The result is ten black-and-white photographs: the outside of the car, its doors and windows, and the empty interior."),
      ("gallery-wide", [shot("interior", "", "The empty interior of the car, benches along both sides")]),
      ("gallery", [shot("side", "", "The side of the car: the number 8805 and a flag decal beside a window"),
                   shot("doors", "", "The car's double doors, with stickers reading 'Do not hold doors'"),
                   shot("front", "", "The end of the car, with its headlights and end door"),
                   shot("door-window", "", "A door window beside a 'No exit' sign and graffiti")]),
      ("gallery-wide", [shot("aisle", "", "The aisle seen from floor level")]),
      ("gallery", [shot("end-door", "", "The door at the end of the car, graffiti on the wall beside it"),
                   shot("bench", "", "A bench and a framed poster seen across the aisle"),
                   shot("reflection", "", "Ceiling lights and advertisements blurred and mirrored in a window"),
                   shot("window", "", "Looking into the car through a window; the sign above the seats reads 'Emergency'")]),
    ],
  },
  {
    "slug": "monte-carlo-path-tracer", "old": "monte-carlo-path-tracer", "img": "monte-carlo-path-tracer",
    "title": "Monte Carlo Path Tracer", "cats": ["rendering"], "year": "2024", "kind": "Individual project",
    "tags": ["C++", "GLSL", "OpenGL", "Path Tracing", "Multiple Importance Sampling", "BSDF"],
    "excerpt": "A Monte Carlo path tracer in C++ and GLSL with naive, direct-lighting and multiple-importance-sampling integrators, and BRDF / BTDF materials with Fresnel.",
    "lead": "A Monte Carlo path tracer in C++ and GLSL. It solves the light transport equation with naive, direct-lighting and multiple-importance-sampling integrators, across specular, microfacet and dielectric materials.",
    "cover_alt": "Six path-traced test scenes: Cornell boxes under two coloured lights and a spot light, glass spheres in front of a rock wall, a microfacet material test and the Veach scene",
    "facts": [("Year", "2024"), ("Type", "Individual project"), ("Built with", "C++, GLSL, OpenGL, Qt")],
    "links": [("Source code", GH + "Monte-Carlo-Path-Tracer", "code")],
    "blocks": [
      ("features", [
          ("layers", "Integrators", "Naive, direct lighting, and multiple importance sampling (MIS)"),
          ("sun", "Lights", "Direct lighting from multiple sources, including point and spot lights"),
          ("droplet", "Materials", "BRDFs and BTDFs with Fresnel: specular, microfacet and dielectric"),
          ("grid", "Sampling", "Stratified, grid and random"),
      ]),
      ("gallery", [shot("specular-brdfs", "Specular BRDFs"), shot("naive-integrator", "Naive Integrator"), shot("microfacet-brdfs", "Microfacet BRDFs"),
                   shot("direct-sample-spot-light", "DirectSampleSpotLight"), shot("direct-sample-point-light", "DirectSamplePointLight"),
                   shot("direct-lighting", "Direct Lighting"), shot("mis-2", "Multiple Importance Sampling 2"), shot("mis-1", "Multiple Importance Sampling 1"),
                   shot("direct-lighting-cornell-two-lights", "DirectLighting – CornellBoxTwoLights"), shot("specular-btdfs", "Specular BTDFs"),
                   shot("dielectric-materials", "Specular BTDFs – Dielectric materials"), shot("veach-naive", "Veach Scene (BSDF Integrator)"),
                   shot("veach-direct", "Veach Scene (Direct Light Integrator)"), shot("veach-mis", "Veach Scene (MIS Integrator)")])
    ],
  },
  {
    "slug": "glsl-shaders", "old": "glsl-shaders", "img": "glsl-shaders",
    "title": "GLSL Shaders", "cats": ["rendering"], "year": "2023", "kind": "Individual project",
    "tags": ["GLSL", "OpenGL", "C++", "Shader Programming", "Post-Processing"],
    "excerpt": "Vertex and fragment shaders for OpenGL: Blinn-Phong lighting, matcaps, vertex deformation, and post-process effects such as bloom, blur, Sobel edges and Worley noise.",
    "lead": "Portions of OpenGL’s graphics pipeline, programmed by hand: a set of vertex and fragment shaders that apply different coloration effects to the surfaces of 3D models.",
    "cover_alt": "The same 3D model rendered sixteen times, once with each shader: matcaps, Blinn-Phong, surface normals, colour gradient, vertex deformation, bloom, greyscale, Sobel edges, Worley noise and others",
    "facts": [("Year", "2023"), ("Type", "Individual project"), ("Built with", "GLSL, OpenGL, C++, Qt")],
    "links": [("Source code", GH + "GLSL-Shaders", "code")],
    "blocks": [
      ("features", [
          ("droplet", "Surface shaders", "Lambert, Blinn-Phong, matcaps, surface normals and a colour gradient"),
          ("wind", "Vertex deformation", "Vertices displaced along the normal over time"),
          ("sparkle", "Post-processing", "Greyscale, Gaussian blur, Sobel edge detection, bloom and Worley noise"),
      ]),
      ("video", {"file": "glsl-shaders", "w": 1920, "h": 1080, "title": "GLSL shaders demo"}),
      ("gallery", [shot("matcap-blue-purple", "", "Matcap shader, blue-purple"), shot("matcap-chrome", "", "Matcap shader, chrome"),
                   shot("matcap-orange-green", "", "Matcap shader, orange-green"), shot("matcap-outline", "", "Matcap shader, outline"),
                   shot("matcap-pearl", "", "Matcap shader, pearl"), shot("matcap-red-clay", "", "Matcap shader, red clay"),
                   shot("matcap-red-plastic", "", "Matcap shader, red plastic"), shot("surface-normals", "", "Surface normals shader"),
                   shot("vertex-deformation", "", "Vertex deformation shader"), shot("bloom", "", "Bloom post-process shader"),
                   shot("color-gradient", "", "Colour gradient shader"), shot("gaussian-blur", "", "Gaussian blur post-process shader"),
                   shot("greyscale", "", "Greyscale post-process shader"), shot("custom-shader", "", "Custom shader"),
                   shot("sobel", "", "Sobel edge-detection shader"), shot("worley-noise", "", "Worley noise shader"),
                   shot("lambert", "", "Lambert shader"), shot("blinn-phong", "", "Blinn-Phong shader")])
    ],
  },
  {
    "slug": "procedural-fireball", "img": "procedural-fireball",
    "title": "Procedural Fireball", "cats": ["rendering"], "year": "2024", "kind": "Individual project",
    "tags": ["WebGL", "GLSL", "TypeScript", "Procedural Graphics", "Shader Programming", "Noise Functions"],
    "excerpt": "A WebGL fireball shaped by 3D Perlin noise and FBM, with live controls for colour, amplitude and frequency. It runs in the browser.",
    "lead": "A procedural fireball in WebGL: multi-octave noise pushes the vertices of a sphere along their normals over time, and the size of that offset sets the colour.",
    "cover_alt": "A fireball in three states: spiky, molten and smooth",
    "facts": [("Year", "2024"), ("Type", "Individual project")],
    "links": [("Live demo", "https://jichu.art/CIS5660-hw01-fireball/", "play"), ("Source code", GH + "CIS5660-hw01-fireball", "code")],
    "blocks": [
      ("features", [
          ("wind", "Noise", "3D Perlin noise and FBM for low- and high-frequency offsets that change over time"),
          ("curve", "Toolbox functions", "Four of them time the animation of the surface"),
          ("droplet", "Colour", "A gradient interpolated from each vertex’s offset"),
          ("sliders", "Controls", "Initial colour, amplitude, frequency and time factor for three parts of the fireball"),
          ("image", "Background", "A gradient that shifts over time"),
      ]),
      ("gallery", [clip("fireball", "", "The fireball changing shape and colour")]),
    ],
  },
  {
    "slug": "unity-stylized-scene", "img": "unity-stylization",
    "title": "Stylized 3D Scene in Unity", "cats": ["rendering"], "year": "2024", "kind": "Individual project",
    "tags": ["Unity", "Shader Graph", "C#", "Non-Photorealistic Rendering", "Post-Processing", "Technical Art"],
    "excerpt": "A stylized real-time scene in Unity after concept art from the game GRIS: rim lighting, textured shadows, animated colours, Sobel outlines and ACES tone mapping.",
    "lead": "A piece of 2D concept art from the game GRIS, rebuilt as a real-time 3D scene in Unity with non-photorealistic shading.",
    "cover_alt": "A small cube-headed character among red plants and butterflies, shown in green, orange and yellow colour themes",
    "facts": [("Year", "2024"), ("Type", "Individual project"), ("Built with", "Unity, Shader Graph, C#")],
    "links": [("Source code", GH + "CIS5660-hw04-stylization", "code")],
    "blocks": [
      ("features", [
          ("sun", "Lighting", "A surface shader that supports multiple lights, with a rim light on back-lit edges"),
          ("grid", "Textured shadows", "Shadow materials sampled in object UV space, with a tiling control"),
          ("droplet", "Animated colour", "The leaves shift between four colour schemes over time"),
          ("curve", "Outlines", "A full-screen pass runs a Sobel filter on depth and normals; noise makes the lines move"),
          ("sliders", "Tone mapping", "A second full-screen pass applies ACES"),
          ("repeat", "Three modes", "The space bar switches the colour theme, the camera speed and the butterflies’ colours"),
      ]),
      ("html", '<p>The character and butterfly models are by other artists on Sketchfab: <a href="https://sketchfab.com/3d-models/gris-forest-friend-8378306886034f2fa590978d8d2506dc0">Forest Friend</a> and <a href="https://sketchfab.com/3d-models/butterflies-poster-2-444a930949e44c3abaa085fbb5a63e0c">Butterflies</a>.</p>'),
      ("gallery-wide", [clip("stylization-1", "", "The camera moving through the stylized scene")]),
      ("gallery", [clip("stylization-2", "", "The scene switching to the orange theme"), clip("stylization-3", "", "The scene in the yellow theme")]),
      ("h2", "Shading"),
      ("gallery", [shot("rim-light", "Rim light"), shot("shadow-texture", "Custom shadow texture"), shot("tone-mapping", "With ACES tone mapping")]),
      ("h2", "Three modes"),
      ("gallery", [shot("mode-1", "Mode 1"), shot("mode-2", "Mode 2"), shot("mode-3", "Mode 3")]),
    ],
  },
  {
    "slug": "tree-creator-plugin-for-maya-houdini", "old": "tree-creator-plugin-for-maya-houdini", "img": "tree-creator",
    "title": "Tree Creator – Plugin for Maya & Houdini", "cats": ["tools"], "year": "2024", "kind": "Individual project",
    "tags": ["C++", "Python", "Maya API", "Houdini HDK", "L-System", "Plugin Development"],
    "excerpt": "Two plugins, one for Maya and one for Houdini, that grow fractal plants from an L-system grammar the user writes.",
    "lead": "One L-system, two hosts: a plugin for Maya and another for Houdini that create fractal plants from the grammar the user enters.",
    "cover_alt": "Five plants grown by the plugin’s L-system core from its bundled grammars, each labelled with its production rule",
    "facts": [("Year", "2024"), ("Type", "Individual project"), ("Maya plugin", "C++, Python, MEL"), ("Houdini plugin", "C++ with the HDK")],
    "links": [("Source code", GH + "Tree-Creator", "code")],
    "blocks": [
      ("p", "I developed two separate plugins, each implementing the same functionality in Maya and Houdini, respectively. The plugin lets the user customize:"),
      ("ul", ["The L-system grammar file", "The step size", "The branch rotation angle", "The number of iteration steps"]),
      ("p", "Using these parameters, it generates different models in Maya and Houdini. The two videos show the plugin in each application."),
      ("p", "The image at the top of this page is the plugin’s own L-system core run on the grammars that ship with it: five plants, each drawn with its production rule, branch angle δ and iteration count n."),
      ("label", "Maya Plugin Demo:"),
      ("video", {"file": "tree-creator-maya-demo", "w": 1920, "h": 1080, "title": "Tree Creator – Maya plugin demo"}),
      ("label", "Houdini Plugin Demo:"),
      ("video", {"file": "tree-creator-houdini-demo", "w": 1920, "h": 1080, "title": "Tree Creator – Houdini plugin demo"})
    ],
  },
  {
    "slug": "houdini-procedural-modeling", "img": "houdini-procedural",
    "title": "Procedural Jellyfish and Buildings in Houdini", "cats": ["animation", "tools"], "year": "2024", "kind": "Individual project",
    "tags": ["Houdini", "Procedural Modeling", "Vellum Simulation", "Houdini Digital Asset", "Technical Art"],
    "excerpt": "A jellyfish modelled and animated procedurally in Houdini, and a digital asset that generates multi-floor buildings with adjustable windows, doors and balconies.",
    "lead": "Two procedural modeling projects in Houdini: a jellyfish whose bell, arms, veins, organs and tentacles each come out of a node network, and a digital asset that stacks floors into a building.",
    "cover_alt": "A procedurally modelled jellyfish, its network of veins, and a generated multi-floor building",
    "facts": [("Year", "2024"), ("Type", "Individual project"), ("Built with", "Houdini, Vellum, SideFX Labs")],
    "links": [("Jellyfish source", GH + "CIS5660-hw02-jellyfish", "code"), ("Buildings source", GH + "CIS5660-hw03-buildings", "code")],
    "blocks": [
      ("h3", "Jellyfish"),
      ("features", [
          ("droplet", "Bell", "A profile curve revolved around the y-axis, shaped by two Bend nodes and animated with keyframes"),
          ("wind", "Arms", "Cloth simulation: Vellum constraints, then the Vellum solver"),
          ("tree", "Veins", "The bell is remeshed into triangles, Find Shortest Path grows the branches, and they are resampled, fused and smoothed"),
          ("curve", "Organs", "A Bézier curve swept into a tube, rotated and copied, with Mountain noise for variation"),
          ("particles", "Tentacles", "Lines copied onto points of the rim and simulated with Vellum, the way hair is"),
      ]),
      ("h3", "Building generator"),
      ("p", "A Houdini Digital Asset that stacks boxes into floors and adds pillars, borders, and supports under overhangs. Windows, doors and balconies have width and height controls, and an alternative set of models can be switched in with one click."),
      ("html", '<p>The setup follows <a href="https://www.youtube.com/watch?v=uIe97023sDk">Simon Houdini’s procedural house tutorial</a>. The alternative door, balcony and window models come from Sketchfab and are credited in the repository.</p>'),
      ("gallery", [clip("jellyfish", "", "The jellyfish swimming"), shot("jellyfish", "", "The finished jellyfish")]),
      ("h2", "Parts of the jellyfish"),
      ("gallery", [shot("bell", "Bell"), shot("arms", "Arms"), shot("veins", "Veins"), shot("organs", "Organs"), shot("tentacles", "Tentacles"), shot("node-graph", "Node network")]),
      ("h2", "Building generator"),
      ("video", {"file": "houdini-buildings", "title": "Building generator demo in Houdini", "w": 1448, "h": 960}),
      ("gallery", [shot("building-1", "", "A generated building"), shot("building-2", "", "A second generated building")]),
    ],
  },
  {
    "slug": "animation-toolkit", "old": "animation-toolkit", "img": "animation-toolkit",
    "title": "Animation Toolkit", "cats": ["animation", "tools"], "year": "2024", "kind": "Individual project",
    "tags": ["Computer Animation", "Inverse Kinematics", "Particle Systems", "Behavioral Animation", "Spline Curves"],
    "excerpt": "An interactive animation toolkit: curve and rotation editors, forward and inverse kinematics, particle systems with fireworks, and behavioural animation.",
    "lead": "An interactive animation toolkit: curve editing and rotations, forward and inverse kinematics, particle systems and behavioural animation.",
    "cover_alt": "Six views of the toolkit: a spline with its control handles, two models rotating, a character posed by IK targets, an agent among cone obstacles, and two firework bursts",
    "facts": [("Year", "2024"), ("Type", "Individual project")],
    "blocks": [
      ("features", [
          ("curve", "Curve editor", "Spline curves and rotations"),
          ("joints", "Kinematics", "Forward (FK) and inverse (IK)"),
          ("particles", "Particle systems", "Including a firework simulation"),
          ("users", "Behavioural animation", "Groups of agents driven by behaviours"),
      ]),
      ("gallery", [clip("animation-curve", "Curve editor: a Hermite spline and its control points"),
                   clip("animation-rotation", "Curve editor: one rotation interpolated with Euler angles (left) and quaternions (right)")]),
      ("gallery", [clip("animation-ik", "IK editor: the limb-based solver following targets at the hands and feet"),
                   clip("animation-behavior", "Behaviour editor: an agent avoiding obstacles on the way to its target")]),
      ("gallery", [clip("animation-fireworks", "Particle editor: fireworks")]),
      ("label", "Demo on YouTube:"),
      ("embed", {"src": "https://www.youtube-nocookie.com/embed/IqU5NDMYwRg", "title": "Animation Toolkit demo on YouTube"}),
      ("label", "On Bilibili:"),
      ("embed", {"src": "https://player.bilibili.com/player.html?bvid=BV1rr421H7VA&autoplay=0", "title": "Animation Toolkit demo on Bilibili"})
    ],
  },
  {
    "slug": "gem-match-game", "old": "jewel-crush-mini-game", "img": "gem-match-game",
    "title": "Gem Match Game", "cats": ["games"], "year": "2021", "kind": "Team project",
    "tags": ["C++", "Qt", "Easy2D", "Game Development"],
    "excerpt": "A classic gem puzzle game in C++ with Qt Widgets and the Easy2D engine. I wrote the client logic and the gem animations.",
    "lead": "A classic gem puzzle game written in C++ with Qt Widgets and the Easy2D game engine.",
    "cover_alt": "A grid of colourful animal-shaped gems with the game’s score panel",
    "facts": [("Year", "2021"), ("Type", "Team project"), ("Built with", "C++, Qt Widgets, Easy2D")],
    "links": [("Source code", GH + "Gem-Match", "code")],
    "blocks": [
      ("p", "In this game, I was responsible for creating the game animations, developing the game client logic, and contributing to the game’s art design."),
      ("p", "For the gem elimination animations, we implemented an animation delay-lock system to ensure that animations play correctly during consecutive eliminations. Chains are found with graph traversal over connected gems."),
      ("video", {"file": "gem-match-game", "w": 1742, "h": 728, "title": "Gem Match Game gameplay"})
    ],
  },
  {
    "slug": "maya-3d-scene-modeling-project", "old": "maya-3d-scene-modeling-project", "img": "maya-3d-scene-modeling",
    "title": "Maya 3D Scene Modeling Project", "cats": ["art"], "year": "2023", "kind": "Individual project",
    "tags": ["Maya", "3D Modeling", "Texturing", "Lighting"],
    "excerpt": "A bedroom modelled, textured and lit in Maya 2024.",
    "lead": "A room modelling project in Maya 2024: after modelling, mapping and finally lighting, I built a room.",
    "cover_alt": "Renders of a modelled bedroom: a desk under a window, a bed and a standing fan",
    "facts": [("Year", "2023"), ("Type", "Individual project"), ("Built with", "Maya 2024")],
    "blocks": [
      ("p", "The final renders show the room from five camera angles."),
      ("gallery-wide", [shot("render-2", "", "Room render, view 2"), shot("render-1", "", "Room render, view 1"), shot("render-3", "", "Room render, view 3"),
                        shot("render-5", "", "Room render, view 5"), shot("render-4", "", "Room render, view 4")])
    ],
  },
  {
    "slug": "motion-capture", "old": "motion-caption", "img": "motion-capture",
    "title": "Motion Capture", "cats": ["animation"], "year": "2023", "kind": "Individual project",
    "tags": ["Motion Capture", "MotionBuilder", "Character Animation"],
    "excerpt": "Motion capture recorded at UPenn’s SIG Lab and finished in MotionBuilder: three actions cleaned up and blended into one animation.",
    "lead": "A motion capture animation, from the capture session to the finished clip: recorded with the equipment of the SIG Lab at the University of Pennsylvania and produced in MotionBuilder 2024.",
    "cover_alt": "Five poses of a robot character from the finished animation, side by side: a stride, a high kick, a hand shading the eyes, a pointing arm and a walk away",
    "facts": [("Year", "2023"), ("Type", "Individual project"), ("Recorded at", "SIG Lab, University of Pennsylvania"), ("Built with", "MotionBuilder 2024")],
    "blocks": [
      ("p", "The capture data was cleaned up and retargeted in MotionBuilder. I removed the T-pose between three different actions and smoothed the transitions."),
      ("p", "The first video is the final animation; the second is behind-the-scenes footage of the capture."),
      ("video", {"file": "motion-capture", "w": 1920, "h": 1080, "title": "Final motion capture animation"}),
      ("video", {"file": "motion-capture-behind-the-scenes", "w": 1920, "h": 1080, "title": "Motion capture behind the scenes"})
    ],
  },
  {
    "slug": "houdini-based-fireworks-simulation", "old": "houdini-based-fireworks-simulation", "img": "houdini-fireworks",
    "title": "Houdini-based Fireworks Simulation", "cats": ["animation"], "year": "2023", "kind": "Individual project",
    "tags": ["Houdini", "Particle Simulation", "VFX"],
    "excerpt": "A fireworks physics simulation in Houdini: particle simulations shaped by bounce and wind, attractive, repulsive and interparticle forces.",
    "lead": "A fireworks physics simulation created with Houdini, in which I produced particle simulations for four different types of fireworks effects.",
    "cover_alt": "Coloured firework particles bursting over a glowing grid floor in Houdini",
    "facts": [("Year", "2023"), ("Type", "Individual project"), ("Built with", "Houdini")],
    "blocks": [
      ("p", "After a plain firework burst, the video shows four force-driven variants:"),
      ("ul", ["Bounce and wind forces", "Attractive forces", "Repulsive forces", "Interparticle forces"]),
      ("video", {"file": "houdini-fireworks", "w": 1920, "h": 1080, "title": "Houdini fireworks simulation"})
    ],
  },
]

HOME_ABOUT = [
    'I work on real-time rendering and GPU performance, currently on the effect rendering engine at TikTok. Before that: a master’s in Computer Science &amp; Computer Graphics at the University of Pennsylvania, and internships at <a href="https://www.infoldgames.com/en/home">Infold Games</a>, <a href="https://www.apple.com/">Apple</a>, TikTok and the <a href="https://www.ualberta.ca/en/index.html">University of Alberta</a>.',
    'Away from the GPU I take <a href="photography/">photographs</a>.',
]

ABOUT_INTRO = [
    "I’m a <strong>Graphics Performance Engineer</strong> at <strong>TikTok</strong>, where I optimize the real-time effect rendering engine used by hundreds of millions of creators every day.",
    "I graduated from the University of Pennsylvania in May 2026 with a Master of Science in Engineering in Computer Science &amp; Computer Graphics. I specialize in GPU rendering, real-time graphics and advanced rendering techniques, with hands-on experience in CUDA, OpenGL, Vulkan and Unreal Engine.",
    'The projects on this site come from those years: renderers, shaders, tools and games. Away from the GPU I take photographs: landscapes, cities after dark and the odd portrait. <a href="../photography/">See the photographs</a>.',
]

# The projects shown large at the top of the home page, in this order. The first gets the widest card.
FEATURED = ["world-space-restir", "cuda-path-tracer", "webgpu-clustered-shading", "vulkan-grass-rendering", "cuda-flocking"]
RESUME = "assets/Jichu-Mao-Resume.pdf"

WORK = [
    ("TikTok", "Jul 2026 – Present", "Graphics Performance Engineer",
     "Optimizing TikTok’s real-time effect rendering engine (C++), used by hundreds of millions of creators daily: frame-rate and latency optimization across the GPU pipeline, shaders, memory and thread scheduling on Android, plus performance profiling and AI-assisted regression analysis across low-end to flagship devices."),
    ("TikTok", "Jun 2025 – Aug 2025", "Software Engineer Intern",
     "Effect House team. Built a real-time performance analysis system for the Effects engine, instrumenting the C++ rendering core with Tracy, and an LLM-agent pipeline that reads renderer parameters and the scene graph to diagnose effects and generate semantic tags."),
    ("University of Pennsylvania", "Aug 2024 – May 2025", "Teaching Assistant",
     "Held office hours and graded assignments for Interactive Computer Graphics (CIS 4600) and Advanced Rendering (CIS 4610)."),
    ("Infold Games", "Jun 2024 – Aug 2024", "Graphics Rendering Intern",
     "Worked on an Unreal Engine rendering pipeline matched to the project’s art style: engine customization for lighting, rendering and resource management, and graphics performance and compatibility work across platforms."),
    ("Apple", "Jan 2023 – May 2023", "Software Engineer Intern", "Software development for the Rel Engineering team in Shanghai."),
    ("University of Alberta", "Jul 2022 – Oct 2022", "Software Research Intern",
     "Mixed reality development: improved DICOM model conversion and volume rendering on a dataset from more than 50 patients, with about 35% faster image loading. Funded by the China Scholarship Council."),
]
EDU = [("University of Pennsylvania", "Aug 2023 – May 2026", "Master of Science in Engineering, Computer Science & Computer Graphics"),
       ("Beijing Jiaotong University", "Sep 2019 – Jun 2023", "Bachelor’s degree, Computer Software Engineering")]
SKILLS = [
    ("Languages", "C++, CUDA, GLSL / HLSL, TypeScript, JavaScript, Python"),
    ("Graphics APIs", "OpenGL, Vulkan, WebGL"),
    ("Graphics debugging", "Nvidia Nsight Graphics, RenderDoc"),
    ("Content tools", "Maya, Houdini, Qt"),
    ("Other", "Perforce, Git, Unity, Unreal Engine"),
]
HOBBIES = [
    ("Video Games:", ["Owns over 700 games on Steam.",
                      "Enjoys experiencing and collecting a wide variety of games, including: VR and XR games, FPS, Rhythm games, Survival games, Souls-like games, Open-world Role-Playing Games (RPGs)."]),
    ("Singing:", ["Served as the tenor section leader in the Beijing Jiaotong University Choir.",
                  "Participated in the National College Students’ Choral Competition and won a second-place award."]),
    ("Photography:", ["Shoots landscapes, cities after dark and portraits, mostly on a Sony α7C II.",
                       "The photographs have their own section of this site, under Photography in the menu."]),
    ("Volunteering:", ["Served as the Deputy Director of the Volunteer Work Department at Beijing Jiaotong University.",
                       "Organized activities to select volunteers for the Winter Olympics.",
                       "Participated in volunteer activities with several public welfare organizations, such as the Apple Volunteers and Wheat Project."]),
]

# ---------------------------------------------------------------- helpers

def write(rel, text):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

# A link to one of these services shows that service's own icon when its file is in assets/icons/, and a plain line icon otherwise.
# The folder holds only files the site's owner has put there: the brands' official SVGs, downloaded from their brand pages and not altered.
BRANDS = {"github.com": "github", "youtube.com": "youtube", "youtu.be": "youtube", "linkedin.com": "linkedin", "bilibili.com": "bilibili"}

def link_icon(url, fallback, root):
    for host, name in BRANDS.items():
        if host in url and os.path.exists(os.path.join(OUT, "assets", "icons", name + ".svg")):
            return f'<img class="icon brand" src="{root}assets/icons/{name}.svg" width="18" height="18" alt="">'
    return icon(fallback)

def social(root, indent="      "):
    items = "".join(f'\n{indent}  <li><a href="{E(u)}">{link_icon(u, i, root)}{E(n)}</a></li>' for n, u, i in SOCIAL)
    return f'<ul class="social">{items}\n{indent}</ul>'

def tags_html(p, indent="        ", limit=None, cats=True):
    items = ("".join(f'<li class="cat">{E(CAT_LABEL[c])}</li>' for c in p["cats"]) if cats else "") + "".join(f"<li>{E(t)}</li>" for t in p["tags"][:limit])
    return f'{indent}<ul class="tags" aria-label="{"Category and tech stack" if cats else "Tech stack"}">{items}</ul>'

PERSON = json.dumps({
    "@context": "https://schema.org", "@type": "Person", "name": "Jichu Mao", "url": SITE + "/",
    "jobTitle": "Graphics Performance Engineer", "worksFor": {"@type": "Organization", "name": "TikTok"},
    "alumniOf": [{"@type": "CollegeOrUniversity", "name": "University of Pennsylvania"},
                 {"@type": "CollegeOrUniversity", "name": "Beijing Jiaotong University"}],
    "sameAs": [u for _, u, _ in SOCIAL],
}, ensure_ascii=False)

def page(*, root, path, title, desc, body, og_image, current="", scripts=(), person=False, cls=""):
    canonical = f"{SITE}/{path}"
    nav = [("Works", f"{root}#works", "works"), ("Photography", f"{root}photography/", "photography"), ("About", f"{root}about/", "about")]
    cur = ' aria-current="page"'
    nav_html = "".join(f'\n      <a href="{u}"{cur if key == current else ""}>{n}</a>' for n, u, key in nav)
    js = "".join(f'\n<script src="{root}assets/js/{s}?v={ASSET_V}" defer></script>' for s in scripts)
    ld = f'\n<script type="application/ld+json">{PERSON}</script>' if person else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Jichu · Art">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#000000">{ld}
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{root}assets/fonts/playfair-display-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{root}assets/fonts/playfair-display-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/css/site.css?v={ASSET_V}">{ANALYTICS}
</head>
<body{' class="' + cls + '"' if cls else ''}>
<a class="skip" href="#main">Skip to content</a>

<header class="site-header">
  <div class="wrap site-bar">
    <a class="site-name" href="{root or "./"}">Jichu Mao</a>
    <nav class="site-nav" aria-label="Main">{nav_html}
    </nav>
  </div>
</header>

<main id="main">
{body}
</main>

<footer class="site-footer">
  <div class="contact-band">
    <div class="wrap">
      <h2>Contact me</h2>
      <p><a class="mail" href="mailto:{EMAIL}">{icon("mail")}{EMAIL}</a></p>
    </div>
  </div>
  <div class="wrap footer-end">
    {social(root, indent="    ")}
    <p class="copyright">© Jichu Mao</p>
  </div>
</footer>{js}
</body>
</html>
"""

def img_tag(key, root, *, thumb=True, cls="", alt="", lazy=True, sizes=""):
    """`sizes`: offer the full-size file next to the thumbnail, for sharp screens and wide slots."""
    m = MAN[key]
    src = f"{root}assets/img/{key}{'-thumb' if thumb else ''}.webp"
    w, h = (m["tw"], m["th"]) if thumb else (m["w"], m["h"])
    c = f' class="{cls}"' if cls else ""
    l = ' loading="lazy" decoding="async"' if lazy else ""
    ss = (f' srcset="{src} {m["tw"]}w, {root}assets/img/{key}.webp {m["w"]}w" sizes="{sizes}"' if sizes and thumb and m["w"] > m["tw"] else "")
    return f'<img{c} src="{src}"{ss} width="{w}" height="{h}" alt="{E(alt)}"{l}>'

def gallery(proj, items, root, wide=False):
    n = len(items)
    cols = "one" if n == 1 else "two" if n in (2, 4) else "three" if n in (3, 5, 6, 9) else "many"
    out = [f'<ul class="gallery{" wide" if wide else ""} {cols}">']
    # how wide one picture is drawn (the media column is at most 880px), so the browser can pick the thumbnail or the full-size file
    slot = {"one": 880 if wide else 560, "two": 430, "three": 280, "many": 430 if wide else 280}[cols]
    sizes = f"(max-width: 900px) {'calc(100vw - 40px)' if cols == 'one' or wide else '46vw'}, {slot}px"
    for s in items:
        cap = s["caption"]
        fc = f"\n            <figcaption>{E(cap)}</figcaption>" if cap else ""
        if "clip" in s:
            m = MAN[f'clip/{s["clip"]}']
            inner = (f'<video class="clip" data-autoplay controls loop muted playsinline preload="none" width="{m["w"]}" height="{m["h"]}" '
                     f'poster="{root}assets/video/{s["clip"]}-poster.webp" aria-label="{E(s["alt"])}">'
                     f'<source src="{root}assets/video/{s["clip"]}.mp4" type="video/mp4"></video>')
        else:
            key = f'{proj["img"]}/{s["key"]}'
            dc = f' data-caption="{E(cap)}"' if cap else ""
            cls = "shot chart" if s["key"].startswith("chart-") else "shot"
            inner = f'<a class="{cls}" href="{root}assets/img/{key}.webp"{dc}>{img_tag(key, root, alt=s["alt"], sizes=sizes)}</a>'
        out.append(f"""        <li>
          <figure>
            {inner}{fc}
          </figure>
        </li>""")
    out.append("      </ul>")
    return "\n".join(out)

def render_blocks(proj, root):
    """Split a project's blocks into the text column and the media column."""
    prose, media, scripts = [], [], set()
    for kind, val in proj["blocks"]:
        if kind == "p":
            prose.append(f"        <p>{E(val)}</p>")
        elif kind == "html":
            prose.append(f"        {val}")
        elif kind == "h3":
            prose.append(f"        <h3>{E(val)}</h3>")
        elif kind == "features":
            rows = "\n".join(f"          <li>{icon(i)}<div><strong>{E(t)}</strong><span>{E(d)}</span></div></li>" for i, t, d in val)
            prose.append(f'        <ul class="features">\n{rows}\n        </ul>')
        elif kind == "steps":
            rows = "\n".join(f"        <li><strong>{E(t)}</strong><span>{E(d)}</span></li>" for t, d in val)
            media.append(f'      <ol class="steps">\n{rows}\n      </ol>')
        elif kind == "bars":
            top = max(v for _, v, _ in val["rows"])
            rows = "\n".join(f'        <div class="bars-row{" hi" if hi else ""}"><dt>{E(n)}</dt><dd><i class="bar" style="flex-basis: {v / top * 80:.2f}%"></i>'
                             f'<span>{v:.1f} {E(val["unit"])}</span></dd></div>' for n, v, hi in val["rows"])
            media.append(f'      <dl class="bars">\n{rows}\n      </dl>')
        elif kind == "ul":
            prose.append("        <ul>\n" + "\n".join(f"          <li>{E(i)}</li>" for i in val) + "\n        </ul>")
        elif kind == "h2":
            media.append(f"      <h2>{E(val)}</h2>")
        elif kind == "note":
            media.append(f'      <p class="media-note">{E(val)}</p>')
        elif kind == "label":
            media.append(f'      <p class="media-label">{E(val)}</p>')
        elif kind == "video":
            ar = "" if (val["w"], val["h"]) == (1920, 1080) else f' style="aspect-ratio: {val["w"]} / {val["h"]}"'
            media.append(f"""      <figure class="player">
        <video controls preload="none" playsinline width="{val["w"]}" height="{val["h"]}"{ar} poster="{root}assets/video/{val["file"]}-poster.webp" aria-label="{E(val["title"])}">
          <source src="{root}assets/video/{val["file"]}.mp4" type="video/mp4">
          <a href="{root}assets/video/{val["file"]}.mp4">Download the video</a>
        </video>
      </figure>""")
        elif kind == "embed":
            media.append(f"""      <figure class="player">
        <iframe src="{E(val["src"])}" title="{E(val["title"])}" loading="lazy" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe>
      </figure>""")
        elif kind == "table":
            head = "".join(f"<th scope=\"col\">{E(h)}</th>" for h in val["head"])
            rows = "\n".join("          <tr>" + "".join(f"<td>{E(c)}</td>" for c in r) + "</tr>" for r in val["rows"])
            media.append(f"""      <div class="table-wrap">
        <table>
          <thead><tr>{head}</tr></thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </div>""")
        elif kind in ("gallery", "gallery-wide"):
            if any("clip" in s for s in val): scripts.add("clips.js")
            if any("key" in s for s in val): scripts.add("lightbox.js")
            media.append("      " + gallery(proj, val, root, wide=(kind == "gallery-wide")))
    return "\n".join(prose), "\n".join(media), tuple(sorted(scripts))

def cover_tag(p, root, *, cls, sizes, lazy=True, alt=""):
    key = f'{p["img"]}/cover'
    m = MAN[key]
    base = f"{root}assets/img/{key}"
    load = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
    return (f'<img class="{cls}" src="{base}-thumb.webp" srcset="{base}-thumb.webp {m["tw"]}w, {base}.webp {m["w"]}w" sizes="{sizes}" '
            f'width="{m["w"]}" height="{m["h"]}" alt="{E(alt)}"{load}>')

def frame_cls(p):
    """A full-frame cover's preview spans the whole frame, not just the main panel."""
    return " full" if MAN[f'{p["img"]}/cover'].get("layout") == "full" else ""

def meta_html(p, indent="        "):
    parts = [p["year"]] + ([p["kind"]] if p.get("kind") else [])
    return f'{indent}<p class="work-meta">' + "".join(f"<span>{E(t)}</span>" for t in parts) + "</p>"

def facts_html(p):
    def ic(k, v):
        return icon("users" if k == "Type" and "Team" in v else FACT_ICONS.get(k, "layers"))
    rows = "".join(f"\n        <div><dt>{ic(k, v)}{E(k)}</dt><dd>{E(v)}</dd></div>" for k, v in p["facts"])
    return f'<dl class="facts">{rows}\n      </dl>'

def stats_html(p):
    if not p.get("stats"):
        return ""
    items = "".join(f"\n        <li><strong>{E(n)}</strong><span>{E(t)}</span></li>" for n, t in p["stats"])
    return f'\n      <ul class="stats" aria-label="Measured results">{items}\n      </ul>'

def pager_link(p, root, cls, label):
    if not p:
        return "<span></span>"
    thumb = f'<img src="{root}assets/img/{p["img"]}/cover-mini.webp" width="360" height="240" alt="" loading="lazy" decoding="async">'
    text = f'<span class="pager-text"><span class="pager-label">{label}</span>{E(p["title"])}</span>'
    inner = thumb + text if cls == "prev" else text + thumb
    return f'<a class="{cls}" href="../{p["slug"]}/">{inner}</a>'

def card_links(p, indent="          "):
    """Short links under a featured card: where the code is, a live demo, the paper, a video."""
    out = []
    for name, url, ic in p.get("links", []):
        label = "GitHub" if "github.com" in url else name
        out.append((label, url, ic))
    for kind, val in p["blocks"]:
        if kind == "embed" and "youtube" in val["src"]:
            out.append(("YouTube", "https://www.youtube.com/watch?v=" + val["src"].rsplit("/", 1)[1], "play"))
    if not out:
        return ""
    items = "".join(f'<li><a href="{E(u)}">{link_icon(u, i, "")}{E(n)}</a></li>' for n, u, i in out[:4])
    return f'\n{indent}<ul class="feat-links">{items}</ul>'

def links_html(proj):
    if not proj.get("links"):
        return ""
    items = "".join(f'\n            <li><a class="button" href="{E(u)}">{link_icon(u, i, "../../")}{E(n)}</a></li>' for n, u, i in proj["links"])
    return f'\n          <ul class="project-links">{items}\n          </ul>'

# ---------------------------------------------------------------- pages

# The opening of the home page: a small studio scene path traced live in the browser (assets/js/studio.js).
# Where that cannot run (no WebGL2, "reduce motion", no JavaScript) the still picture is shown instead; it was
# rendered by the same code, see the README.
HERO_ALT = ("The letters JICHU · ART standing on a wet black floor, each in a different material, warm on the left "
            "and cool on the right: a crystal J with rainbow edges, a chrome I, a gold C, a red neon H, a milky "
            "translucent U, a glowing blue dot, a sapphire-blue glass A, a titanium R shading from gold to blue and a "
            "white porcelain T, all reflected in the floor")

def build_home():
    root = ""
    by = {p["slug"]: p for p in PROJECTS}
    frame = lambda p, tag: (f'<div class="work-frame{frame_cls(p)}">{tag}<video class="work-preview" muted loop playsinline preload="none" tabindex="-1" aria-hidden="true" '
                            f'data-src="assets/video/preview-{p["img"]}.mp4"></video><span class="work-live" aria-hidden="true">{icon("play")}Preview</span></div>')
    feats = []
    for i, slug in enumerate(FEATURED):
        p = by[slug]
        lead = i == 0
        sizes = "(max-width: 900px) calc(100vw - 40px), 780px" if lead else "(max-width: 900px) calc(100vw - 40px), 668px"
        stats = ""
        if lead and p.get("stats"):
            stats = '\n          <ul class="feat-stats">' + "".join(f"<li><strong>{E(n)}</strong><span>{E(t)}</span></li>" for n, t in p["stats"][:3]) + "</ul>"
        feats.append(f"""      <li class="work feat{" lead" if lead else ""}">
        {frame(p, cover_tag(p, root, cls="work-thumb", sizes=sizes, lazy=not lead))}
        <div class="feat-text">
{meta_html(p, "          ")}
          <h3><a href="works/{p["slug"]}/">{E(p["title"])}</a></h3>
          <p class="work-excerpt">{E(p["excerpt"])}</p>{stats}
{tags_html(p, "          ", limit=4, cats=False)}{card_links(p)}
        </div>
      </li>""")
    rest = [p for p in PROJECTS if p["slug"] not in FEATURED]
    minis = []
    for p in rest:
        m = MAN[f'{p["img"]}/cover']
        base = f'assets/img/{p["img"]}/cover'
        tag = (f'<img class="work-thumb" src="{base}-mini.webp" srcset="{base}-mini.webp 360w, {base}-thumb.webp {m["tw"]}w" '
               f'sizes="(max-width: 600px) 116px, (max-width: 1000px) 46vw, 420px" width="{m["w"]}" height="{m["h"]}" alt="" loading="lazy" decoding="async">')
        minis.append(f"""      <li class="work mini" data-cats="{" ".join(p["cats"])}">
        <div class="work-frame">{tag}</div>
        <h3><a href="works/{p["slug"]}/">{E(p["title"])}</a></h3>
        <p class="work-meta"><span>{E(CAT_LABEL[p["cats"][0]])}</span><span>{E(p["year"])}</span></p>
      </li>""")
    counts = {c: sum(c in p["cats"] for p in rest) for c, _ in CATEGORIES}
    filters = f'<button type="button" data-cat="all" aria-pressed="true">All <span>{len(rest)}</span></button>' + "".join(
        f'<button type="button" data-cat="{c}" aria-pressed="false">{E(label)} <span>{counts[c]}</span></button>' for c, label in CATEGORIES if counts[c])
    about = "\n".join(f"      <p>{t}</p>" for t in HOME_ABOUT)
    body = f"""<section class="hero hero-pt">
  <figure class="hero-media">
    <canvas class="hero-live" aria-hidden="true"></canvas>
    <picture class="hero-still" hidden>
      <source media="(max-aspect-ratio: 1/1)" data-srcset="assets/img/home/studio-tall-720.webp 720w" sizes="100vw" width="720" height="1440">
      <img data-srcset="assets/img/home/studio-1000.webp 1000w, assets/img/home/studio-1600.webp 1600w" sizes="100vw" width="1600" height="900" alt="{E(HERO_ALT)}">
    </picture>
    <noscript><img class="hero-still" src="assets/img/home/studio-1600.webp" width="1600" height="900" alt="{E(HERO_ALT)}"></noscript>
    <figcaption><span class="cap-live">Path traced live in your browser, every letter a different material: dispersive crystal, chrome, gold, neon, subsurface scattering, a light, absorbing sapphire glass, thin-film titanium and porcelain, denoised as it converges. <span class="spp"></span><span class="hint"> Drag to turn it.</span></span><span class="cap-still">Path traced by this page’s own renderer, every letter a different material: dispersive crystal, chrome, gold, neon, subsurface scattering, a light, absorbing sapphire glass, thin-film titanium and porcelain.</span></figcaption>
  </figure>
  <div class="wrap hero-text">
    <h1>Jichu Mao</h1>
    <p class="hero-lead">Graphics engineer: real-time rendering, path tracing and GPU performance</p>
  </div>
</section>

<section class="works" id="works">
  <div class="wrap">
    <h2 class="section-title">Selected work</h2>
    <ul class="feat-grid">
{chr(10).join(feats)}
    </ul>
    <div class="more-head">
      <h2 class="section-title">More work</h2>
      <div class="work-filter" role="group" aria-label="Filter the projects below by category" hidden>{filters}</div>
    </div>
    <ul class="mini-grid">
{chr(10).join(minis)}
    </ul>
  </div>
</section>

<section class="about-band" id="about">
  <div class="wrap about-grid">
    <div class="about-side">
      {img_tag("home/avatar", root, thumb=False, cls="avatar", alt="Portrait of Jichu Mao")}
    </div>
    <div class="about-main">
      <h2>About</h2>
{about}
      <p class="about-actions"><a class="button-fill" href="about/">More about me</a><a class="button" href="{RESUME}">Résumé (PDF)</a></p>
    </div>
  </div>
</section>"""
    write("index.html", page(root=root, path="", title="Jichu Mao – Graphics Performance Engineer | Jichu · Art",
                             desc="Portfolio of Jichu Mao, graphics engineer: real-time rendering, GPU path tracing, shaders, graphics tools, games and animation.",
                             body=body, og_image="assets/img/home/og.jpg", current="", scripts=("works.js", "previews.js", "studio.js", "home.js"), person=True, cls="home"))

def build_projects():
    root = "../../"
    for i, p in enumerate(PROJECTS):
        prose, media, scripts = render_blocks(p, root)
        prev_p, next_p = PROJECTS[i - 1] if i > 0 else None, PROJECTS[i + 1] if i + 1 < len(PROJECTS) else None
        body = f"""<article class="project">
  <header class="project-hero">
    <div class="project-glow" style="background-image: url({root}assets/img/{p["img"]}/glow.webp)" aria-hidden="true"></div>
    <div class="wrap">
      <a class="back" href="{root}#works">← All works</a>
      <div class="project-head">
        <div class="project-title">
          <h1>{E(p["title"])}</h1>
          <p class="project-lead">{E(p["lead"])}</p>
{tags_html(p, indent="          ")}{links_html(p)}
        </div>
        <figure class="project-cover{frame_cls(p)}">{cover_tag(p, root, cls="", sizes="(max-width: 900px) calc(100vw - 40px), 780px", lazy=False, alt=p["cover_alt"])}<video class="work-preview" data-autoplay muted loop playsinline preload="none" tabindex="-1" aria-hidden="true"><source src="{root}assets/video/preview-{p["img"]}.mp4" type="video/mp4"></video></figure>
      </div>
      {facts_html(p)}{stats_html(p)}
    </div>
  </header>
  <div class="wrap">
    <div class="project-grid">
      <div class="project-info">
        <h2>Overview</h2>
        <div class="prose">
{prose}
        </div>
      </div>
      <div class="project-media">
{media}
      </div>
    </div>
    <nav class="pager" aria-label="More works">
      {pager_link(prev_p, root, "prev", "Previous")}
      {pager_link(next_p, root, "next", "Next")}
    </nav>
  </div>
</article>"""
        write(f'works/{p["slug"]}/index.html',
              page(root=root, path=f'works/{p["slug"]}/', title=f'{p["title"]} – Jichu · Art', desc=p["excerpt"],
                   body=body, og_image=f'assets/img/{p["img"]}/og.jpg', current="works", scripts=tuple(sorted(set(scripts) | {"clips.js"}))))

def build_about():
    root = "../"
    intro = "\n".join(f"      <p>{t}</p>" for t in ABOUT_INTRO)
    def cv(rows):
        out = []
        for row in rows:
            org, when, role = row[:3]
            desc = f'\n          <p class="cv-desc">{E(row[3])}</p>' if len(row) > 3 and row[3] else ""
            out.append(f"""        <li>
          <span class="cv-org">{E(org)}</span>
          <span class="cv-when">{E(when)}</span>
          <span class="cv-role">{E(role)}</span>{desc}
        </li>""")
        return "\n".join(out)
    skills = "\n".join(f"          <div><dt>{E(k)}</dt><dd>{E(v)}</dd></div>" for k, v in SKILLS)
    hobbies = "\n".join(
        f'        <h3>{E(h)}</h3>\n        <ul class="plain">\n' + "\n".join(f"          <li>{E(i)}</li>" for i in items) + "\n        </ul>"
        for h, items in HOBBIES)
    body = f"""<div class="about-page wrap">
  <div class="about-grid">
    <div class="about-side">
      {img_tag("home/avatar", root, thumb=False, cls="avatar", alt="Portrait of Jichu Mao", lazy=False)}
      {social(root)}
    </div>
    <div class="about-main">
      <h1>Jichu Mao</h1>
{intro}
      <p class="about-actions"><a class="button" href="{root}{RESUME}">Résumé (PDF)</a></p>
      <div class="cv">
        <h2>Work Experience</h2>
        <ul class="cv-list">
{cv(WORK)}
        </ul>
        <h2>Education</h2>
        <ul class="cv-list">
{cv(EDU)}
        </ul>
        <h2>Skills</h2>
        <dl class="skills">
{skills}
        </dl>
        <h2>Hobbies</h2>
{hobbies}
      </div>
    </div>
  </div>
</div>"""
    write("about/index.html", page(root=root, path="about/", title="About – Jichu · Art",
                                   desc="About Jichu Mao, Graphics Performance Engineer at TikTok: background, work experience, education, skills and hobbies.",
                                   body=body, og_image="assets/img/home/og.jpg", current="about", person=True))

def redirect(rel_dir, target_rel, target_abs_path):
    """Keep old WordPress URLs alive: /index.php/<slug>/ -> new page."""
    write(f"{rel_dir}/index.html", f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Redirecting…</title>
<link rel="canonical" href="{SITE}/{target_abs_path}">
<meta http-equiv="refresh" content="0; url={target_rel}">
<meta name="robots" content="noindex">
</head>
<body>
<p>This page has moved. <a href="{target_rel}">Continue</a>.</p>
</body>
</html>
""")

def build_resume():
    """A one-page résumé written from the same data as the About page. tools/resume.py prints it to the PDF at RESUME."""
    root = "../"
    by = {p["slug"]: p for p in PROJECTS}
    jobs = "\n".join(f"""    <div class="item">
      <p class="line"><span><strong>{E(org)}</strong>, {E(role)}</span><span class="when">{E(dates)}</span></p>
      <p>{E(desc)}</p>
    </div>""" for org, dates, role, desc in WORK)
    projects = "\n".join(f"""    <div class="item">
      <p class="line"><span><strong><a href="{SITE}/works/{slug}/">{E(by[slug]["title"])}</a></strong>, {E(by[slug]["kind"].lower())}</span><span class="when">{E(by[slug]["year"])}</span></p>
      <p>{E(by[slug]["excerpt"])}</p>
    </div>""" for slug in FEATURED)
    edu = "\n".join(f'      <div class="item"><p class="line"><strong>{E(org)}</strong><span class="when">{E(dates)}</span></p><p>{E(what)}</p></div>' for org, dates, what in EDU)
    skills = "\n".join(f"      <p><strong>{E(k)}:</strong> {E(v)}</p>" for k, v in SKILLS)
    links = " · ".join(f'<a href="{E(u)}">{E(u.split("//")[1].removeprefix("www.").rstrip("/"))}</a>' for _, u, _ in SOCIAL[:2])
    write("resume/index.html", f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jichu Mao – Résumé</title>
<meta name="description" content="Résumé of Jichu Mao, Graphics Performance Engineer at TikTok: experience, selected projects, education and skills.">
<link rel="canonical" href="{SITE}/resume/">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">{ANALYTICS}
<style>
@font-face {{ font-family: "Playfair Display"; src: url("{root}assets/fonts/playfair-display-latin-700-normal.woff2") format("woff2"); font-weight: 700; font-display: swap; }}
@font-face {{ font-family: "Open Sans"; src: url("{root}assets/fonts/open-sans-latin-400-normal.woff2") format("woff2"); font-weight: 400; font-display: swap; }}
@font-face {{ font-family: "Open Sans"; src: url("{root}assets/fonts/open-sans-latin-600-normal.woff2") format("woff2"); font-weight: 600; font-display: swap; }}
@page {{ size: Letter; margin: .42in .6in; }}
* {{ box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body {{ margin: 0; background: #1b1b1b; color: #111; font: 400 9pt/1.42 "Open Sans", Arial, sans-serif; }}
a {{ color: inherit; text-decoration: none; }}
.bar {{ max-width: 8.5in; margin: 0 auto; padding: 18px 4px; display: flex; justify-content: space-between; align-items: center; font-size: 14px; }}
.bar a {{ color: #fff; }}
.bar .get {{ padding: 9px 18px; background: #db4f3d; font-weight: 600; }}
.sheet {{ max-width: 8.5in; margin: 0 auto 40px; padding: .42in .6in; background: #fff; }}
h1 {{ margin: 0; font: 700 24pt/1.05 "Playfair Display", Georgia, serif; }}
.head {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; padding-bottom: 9pt; border-bottom: 1.2pt solid #111; }}
.role {{ margin: 4pt 0 0; font-size: 10.5pt; }}
.contact {{ margin: 0; text-align: right; line-height: 1.55; }}
.contact a, .sheet section a {{ text-decoration: underline; text-decoration-color: #db4f3d; text-decoration-thickness: .7pt; text-underline-offset: 2.2pt; }}
h2 {{ margin: 11pt 0 4.5pt; font: 700 12.5pt/1.2 "Playfair Display", Georgia, serif; }}
p {{ margin: 0; }}
strong {{ font-weight: 600; }}
.item {{ margin-bottom: 5.6pt; break-inside: avoid; }}
.line {{ display: flex; justify-content: space-between; gap: 14px; }}
.when {{ flex: none; color: #555; }}
.item p + p {{ color: #2b2b2b; }}
.pair {{ break-inside: avoid; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 0 .4in; }}
.skills p + p {{ margin-top: 2.5pt; }}
@media (max-width: 640px) {{
  body {{ font-size: 14px; }}
  .sheet {{ padding: 24px 20px; }}
  .head, .line {{ flex-direction: column; align-items: flex-start; gap: 2px; }}
  .pair {{ grid-template-columns: minmax(0, 1fr); }}
  .contact {{ text-align: left; margin-top: 10px; }}
}}
@media print {{
  body {{ background: #fff; }}
  .bar {{ display: none; }}
  .sheet {{ max-width: none; margin: 0; padding: 0; }}
}}
</style>
</head>
<body>
<p class="bar"><a href="{root}">← jichu.art</a><a class="get" href="{root}{RESUME}" download>Download PDF</a></p>
<main class="sheet">
  <header class="head">
    <div>
      <h1>Jichu Mao</h1>
      <p class="role">Graphics Performance Engineer</p>
    </div>
    <p class="contact"><a href="mailto:{EMAIL}">{EMAIL}</a> · <a href="{SITE}/">jichu.art</a><br>{links}</p>
  </header>
  <section>
    <h2>Experience</h2>
{jobs}
  </section>
  <section>
    <h2>Selected projects</h2>
{projects}
  </section>
  <div class="pair">
    <section>
      <h2>Education</h2>
{edu}
    </section>
    <section class="skills">
      <h2>Skills</h2>
{skills}
    </section>
  </div>
</main>
</body>
</html>
""")

def build_redirects():
    for p in PROJECTS:
        if p.get("old"):
            redirect(f'index.php/{p["old"]}', f'../../works/{p["slug"]}/', f'works/{p["slug"]}/')
    redirect("index.php/personal-page", "../../about/", "about/")
    for c in ("softwares", "games", "animation", "art-designs"):
        redirect(f"index.php/category/{c}", "../../../#works", "")

def build_misc():
    write("404.html", """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Page not found – Jichu · Art</title>
<style>
  body { margin: 0; min-height: 100vh; display: grid; place-items: center; background: #000; color: #c4c4c4;
         font: 17px/1.7 "Open Sans", system-ui, sans-serif; text-align: center; padding: 24px; }
  h1 { font: 700 42px/1.25 "Playfair Display", Georgia, serif; color: #fff; margin: 0 0 12px; }
  a { color: #db4f3d; }
</style>
</head>
<body>
  <div>
    <h1>Page not found</h1>
    <p>That address doesn’t exist on this site. <a href="/">Go to the home page</a> to see all works.</p>
  </div>
</body>
</html>
""")
    write("assets/favicon.svg", """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" fill="#000"/>
  <text x="29" y="47" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="46" fill="#fff">J</text>
  <circle cx="47" cy="43" r="5" fill="#db4f3d"/>
</svg>
""")
    write(".nojekyll", "")
    write("CNAME", "jichu.art\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    urls = [""] + ["about/", "resume/"] + [f'works/{p["slug"]}/' for p in PROJECTS] + PHOTO_PAGES
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{SITE}/{u}</loc></url>\n" for u in urls) + "</urlset>\n")

# The photography section has its own generator (tools/photography.py); it is built here so that
# one command rebuilds the whole site and its pages land in the sitemap.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photography
PHOTO_PAGES = photography.build(OUT, ASSET_V, analytics=ANALYTICS)

build_home(); build_projects(); build_about(); build_resume(); build_redirects(); build_misc()
print("built", len(PROJECTS), "project pages and", len(PHOTO_PAGES), "photography pages")
