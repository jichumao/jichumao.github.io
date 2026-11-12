"""Generator for the static jichu.art site.

Text for the first ten projects is carried over from the old WordPress site; the four newer
rendering projects come from the résumé and the project READMEs on GitHub.
Output is plain HTML that can also be edited by hand.
"""
import html, json, os, sys

OUT = sys.argv[1]
MAN = json.load(open(sys.argv[2], encoding="utf-8"))
SITE = "https://jichu.art"
E = html.escape
ASSET_V = "4"   # bump when site.css or the scripts change, so browsers do not reuse a cached copy

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
}

def icon(name):
    return (f'<svg class="icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')

CATEGORIES = [("rendering", "Rendering"), ("tools", "Tools"), ("games", "Games"), ("animation", "Animation"), ("art", "Art")]
CAT_LABEL = dict(CATEGORIES)

# ---------------------------------------------------------------- content

def shot(key, caption="", alt=""):
    return {"key": key, "caption": caption, "alt": alt or caption}

def clip(name, caption="", alt=""):
    return {"clip": name, "caption": caption, "alt": alt or caption}

GH = "https://github.com/jichumao/"

PROJECTS = [
  {
    "slug": "world-space-restir", "img": "world-space-restir",
    "title": "World-Space ReSTIR in Vulkan", "cats": ["rendering"], "tags": ["C++", "Vulkan", "GLSL", "Ray tracing", "ReSTIR"],
    "excerpt": "A world-space global illumination method implemented in a Vulkan ray-tracing pipeline. In large scenes it reaches about 40% higher accuracy than screen-space ReSTIR for roughly 5% extra render time.",
    "links": [("Source code", "https://github.com/zhiyi1801/CIS-565-2024Fall-Final", "code"), ("Paper", "https://wangningbei.github.io/2023/ReSTIR.html", "paper")],
    "blocks": [
      ("html", '<p>An implementation of <a href="https://wangningbei.github.io/2023/ReSTIR.html">World-Space Spatiotemporal Path Resampling for Path Tracing</a> with Vulkan ray tracing, built on Nvidia’s Vulkan ray-tracing renderer. It was the final project for CIS 565, GPU Programming and Architecture, at the University of Pennsylvania, made together with Zhiyi Zhou.</p>'),
      ("p", "In large scenes it reaches about 40% higher accuracy than screen-space ReSTIR for roughly 5% extra render time."),
      ("p", "The renderer runs in five passes:"),
      ("ul", ["G-buffer and initial path sampling",
              "Hash grid construction: path samples go into a world-space hash grid keyed by position and normal, with cells that grow with distance from the camera",
              "Spatiotemporal resampling: samples are reused from the previous frame and from neighbouring hash-grid cells",
              "Final shading of direct and indirect illumination",
              "Post-processing, including Intel Open Image Denoise"]),
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
      ("gallery-wide", [shot("chart-initial-sampling", "Initial sampling time by scene"), shot("chart-passes", "Time per pass by scene")]),
    ],
  },
  {
    "slug": "cuda-path-tracer", "img": "cuda-path-tracer",
    "title": "CUDA Path Tracer", "cats": ["rendering"], "tags": ["C++", "CUDA", "Path tracing", "glTF"],
    "excerpt": "A GPU-accelerated path tracer built with CUDA: glTF model loading, BSDF shading, stream compaction of ray paths, stochastic anti-aliasing, physically-based depth of field, environment maps, tone mapping and bounding-volume culling.",
    "links": [("Source code", GH + "CUDA-Path-Tracer", "code")],
    "blocks": [
      ("p", "A GPU path tracer built on CUDA, based on CIS 5650 at UPenn. It is rooted in physically-based rendering, loads glTF meshes and materials, and simulates light transport to produce soft shadows, caustics and depth of field."),
      ("p", "The highlight renders use 5,000 samples per pixel or more, with up to 8 bounces per ray."),
      ("p", "Visual features:"),
      ("ul", ["Diffuse, glossy, perfectly specular and refractive BSDFs", "Stochastic sampled anti-aliasing", "Physically-based depth of field with a thin-lens camera",
              "glTF mesh loading with texture mapping", "HDR environment maps", "ACES and Reinhard tone mapping, gamma correction"]),
      ("p", "Performance work:"),
      ("ul", ["Stream compaction removes finished rays; in open scenes render time drops from 25.7 ms to 18.2 ms",
              "Bounding-box culling for glTF meshes, 20–40% faster on low- to mid-poly models",
              "Material sorting was measured too, and turned out slower on small scenes"]),
      ("h2", "Highlights"),
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
                        shot("chart-bbox-culling", "Bounding-box culling: frame rate by triangle count")]),
    ],
  },
  {
    "slug": "webgpu-clustered-shading", "img": "webgpu-clustered-shading",
    "title": "WebGPU Forward+ and Clustered Deferred Shading", "cats": ["rendering"], "tags": ["TypeScript", "WebGPU", "WGSL", "Compute shaders"],
    "excerpt": "Forward+ and clustered deferred shading implemented in WebGPU. It handles more than 1,000 dynamic lights and raises the frame rate by about 25%.",
    "links": [("Live demo", "https://jichu.art/Project4-WebGPU-Forward-Plus-and-Clustered-Deferred/", "play"),
              ("Source code", GH + "Project4-WebGPU-Forward-Plus-and-Clustered-Deferred", "code")],
    "blocks": [
      ("p", "Forward+ and clustered deferred shading in WebGPU. The scene is the Sponza atrium with a large number of moving point lights, and the project compares the shading methods at high resolution with thousands of lights."),
      ("p", "In a 4K scene with 5,000 randomly moving lights, naive forward shading reaches about 3 frames per second, while clustered deferred shading stays above 100."),
      ("ul", ["Three pipelines: forward, clustered forward (Forward+) and clustered deferred",
              "A compute shader splits the view frustum into clusters, logarithmically along depth, and assigns lights to them",
              "Optional bloom post-process", "Compressed G-buffer"]),
      ("p", "The live demo needs a browser with WebGPU."),
      ("gallery-wide", [shot("sponza-4k-5000-lights", "Sponza at 4K with 5,000 lights")]),
      ("gallery", [clip("webgpu-moving-lights", "Random lights moving through the scene")]),
      ("h2", "G-buffer"),
      ("gallery", [shot("gbuffer-position", "Position"), shot("gbuffer-normal", "Normal"), shot("gbuffer-color", "Colour"), shot("gbuffer-depth", "Depth")]),
      ("h2", "Frame time at 4K"),
      ("table", {"head": ["Lights", "Naive", "Clustered forward", "Clustered deferred"],
                 "rows": [["256", "18.8 ms", "1.6 ms", "0.5 ms"], ["512", "34.4 ms", "3.4 ms", "1.1 ms"], ["1,024", "71.4 ms", "7.0 ms", "2.3 ms"],
                          ["2,048", "142.8 ms", "14.2 ms", "4.1 ms"], ["4,096", "273.6 ms", "27.7 ms", "8.2 ms"], ["8,192", "550.8 ms", "52.6 ms", "15.1 ms"]]}),
      ("gallery-wide", [shot("chart-lights", "Frame time by number of lights")]),
    ],
  },
  {
    "slug": "vulkan-grass-rendering", "img": "vulkan-grass-rendering",
    "title": "Vulkan Grass Rendering", "cats": ["rendering"], "tags": ["C++", "Vulkan", "GLSL", "Tessellation", "Compute shaders"],
    "excerpt": "Real-time grass for 3D scenes: a Vulkan grass simulator and renderer that uses a compute shader for physics and culling.",
    "links": [("Source code", GH + "Vulkan-Grass-Rendering", "code"),
              ("Paper", "https://www.cg.tuwien.ac.at/research/publications/2017/JAHRMANN-2017-RRTG/JAHRMANN-2017-RRTG-draft.pdf", "paper")],
    "blocks": [
      ("p", "A grass simulator and renderer written against the Vulkan API. Each blade is a Bézier curve. A compute shader applies gravity, wind and recovery forces to every blade and culls the ones that do not contribute to the frame; tessellation shaders turn the remaining curves into geometry, with more detail close to the camera."),
      ("html", '<p>It follows the paper <a href="https://www.cg.tuwien.ac.at/research/publications/2017/JAHRMANN-2017-RRTG/JAHRMANN-2017-RRTG-draft.pdf">Responsive Real-Time Grass Rendering for General 3D Scenes</a> by Jahrmann and Wimmer.</p>'),
      ("p", "With 32,768 blades, orientation, view-frustum and distance culling together raise the frame rate from 70.2 to 228.2 FPS."),
      ("gallery-wide", [clip("grass-showcase", "8,192 grass blades with dynamic tessellation levels")]),
      ("h2", "Level of detail"),
      ("gallery", [clip("grass-lod", "Tessellation level follows the distance to the camera")]),
      ("h2", "Culling"),
      ("gallery", [clip("grass-culling-orientation", "Orientation culling"), clip("grass-culling-frustum", "View-frustum culling"), clip("grass-culling-distance", "Distance culling")]),
      ("h2", "Performance"),
      ("gallery-wide", [shot("chart-culling", "Frame rate with each culling method, 32,768 blades"), shot("chart-blade-count", "Frame rate by number of blades, with and without culling")]),
    ],
  },
  {
    "slug": "physically-based-shaders", "old": "physically-based-shaders", "img": "physically-based-shaders",
    "title": "Physically-Based Shaders", "cats": ["rendering"], "tags": ["C++", "OpenGL", "GLSL", "Qt"],
    "excerpt": "The PBR implementation uses the Cook-Torrance model in a physically based rendering pipeline, along with image-based lighting, as well as custom scenes and environment maps.",
    "links": [("Source code", GH + "Physically-based-Shader", "code")],
    "blocks": [
      ("html", '<p>Based on the paper <a href="https://blog.selfshadow.com/publications/s2013-shading-course/karis/s2013_pbs_epic_notes_v2.pdf">“Real Shading in Unreal Engine 4”</a>, the PBR implementation uses the Cook-Torrance model in a physically based rendering pipeline, along with image-based lighting, as well as custom scenes and environment maps.</p>'),
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
      ("gallery", [shot("scene-skull", "A Skull"), shot("scene-gun", "Gun")]),
    ],
  },
  {
    "slug": "tree-creator-plugin-for-maya-houdini", "old": "tree-creator-plugin-for-maya-houdini", "img": "tree-creator",
    "title": "Tree Creator – Plugin for Maya & Houdini", "cats": ["tools"], "tags": ["Maya", "Houdini", "L-System"],
    "excerpt": "This is a Maya & Houdini plugin development project. The function of this plugin is to create different fractal plants in Maya or Houdini based on the L-System grammar input by the user.",
    "links": [("Source code", GH + "Tree-Creator", "code")],
    "blocks": [
      ("p", "This is a Maya & Houdini plugin development project. The function of this plugin is to create different fractal plants in Maya or Houdini based on the L-System grammar input by the user."),
      ("p", "I developed two separate plugins, each implementing the same functionality in Maya and Houdini, respectively. This plugin allows users to:"),
      ("ul", ["Customize the L-System grammar file", "Customize the Step Size", "Customize the branch rotation angle", "Customize the number of iteration steps"]),
      ("p", "Using the above files as parameters, it generates different models in Maya and Houdini."),
      ("p", "The following two videos showcase demos of the plugin."),
      ("label", "Maya Plugin Demo:"),
      ("video", {"file": "tree-creator-maya-demo", "w": 1920, "h": 1080, "title": "Tree Creator – Maya plugin demo"}),
      ("label", "Houdini Plugin Demo:"),
      ("video", {"file": "tree-creator-houdini-demo", "w": 1920, "h": 1080, "title": "Tree Creator – Houdini plugin demo"}),
    ],
  },
  {
    "slug": "monte-carlo-path-tracer", "old": "monte-carlo-path-tracer", "img": "monte-carlo-path-tracer",
    "title": "Monte Carlo Path Tracer", "cats": ["rendering"], "tags": ["C++", "Qt", "Path tracing", "MIS"],
    "excerpt": "Monte Carlo path tracer in C++ using Naive, Direct and Multiple Importance Sampling – Direct Lighting Integrator using LTE with Multiple light sources, Multiple materials (BSDF – BRDFs and BTDFs, Fresnel) with Stratified, grid and random sampling techniques.",
    "links": [("Source code", GH + "Monte-Carlo-Path-Tracer", "code")],
    "blocks": [
      ("p", "Monte Carlo path tracer in C++ using Naive, Direct and Multiple Importance Sampling – Direct Lighting Integrator using LTE with Multiple light sources, Multiple materials (BSDF – BRDFs and BTDFs, Fresnel) with Stratified, grid and random sampling techniques."),
      ("p", "Sample Renders are as follows:"),
      ("gallery", [shot("specular-brdfs", "Specular BRDFs"), shot("naive-integrator", "Naive Integrator"), shot("microfacet-brdfs", "Microfacet BRDFs"),
                   shot("direct-sample-spot-light", "DirectSampleSpotLight"), shot("direct-sample-point-light", "DirectSamplePointLight"),
                   shot("direct-lighting", "Direct Lighting"), shot("mis-2", "Multiple Importance Sampling 2"), shot("mis-1", "Multiple Importance Sampling 1"),
                   shot("direct-lighting-cornell-two-lights", "DirectLighting – CornellBoxTwoLights"), shot("specular-btdfs", "Specular BTDFs"),
                   shot("dielectric-materials", "Specular BTDFs – Dielectric materials"), shot("veach-naive", "Veach Scene (BSDF Integrator)"),
                   shot("veach-direct", "Veach Scene (Direct Light Integrator)"), shot("veach-mis", "Veach Scene (MIS Integrator)")]),
    ],
  },
  {
    "slug": "mini-minecraft", "old": "hello-world", "img": "mini-minecraft",
    "title": "Mini Minecraft", "cats": ["games"], "tags": ["C++", "OpenGL", "GLSL", "Qt6"],
    "excerpt": "This is a Minecraft-like game, using OpenGL, C++ and Qt6 for development. Many important features are implemented from 0 to 1 by me in this game.",
    "links": [("Source code", GH + "miniMC", "code")],
    "blocks": [
      ("p", "This is a Minecraft-like game, using OpenGL and C++."),
      ("p", "I mainly implemented following features in this game:"),
      ("ul", ["Procedural Terrain", "Texturing and Texture Animation", "Additional Biomes", "Procedurally Placed Assets", "Procedural Buildings with Shape Grammars"]),
      ("p", "Here is the demo for our games:"),
      ("label", "On YouTube:"),
      ("embed", {"src": "https://www.youtube-nocookie.com/embed/gNmsVbQdZX0", "title": "Mini Minecraft demo on YouTube"}),
      ("label", "On Bilibili:"),
      ("embed", {"src": "https://player.bilibili.com/player.html?bvid=BV1Ru4y1n7Bg&autoplay=0", "title": "Mini Minecraft demo on Bilibili"}),
      ("gallery-wide", [shot("screenshot-1", "", "Mini Minecraft title screen over procedural terrain"), shot("screenshot-2", "", "Mini Minecraft in-game screenshot")]),
    ],
  },
  {
    "slug": "glsl-shaders", "old": "glsl-shaders", "img": "glsl-shaders",
    "title": "GLSL Shaders", "cats": ["rendering"], "tags": ["GLSL", "OpenGL", "C++"],
    "excerpt": "Programmed portions of OpenGL’s graphics pipeline by writing a few different vertex and fragment shaders to apply different coloration effects to the surfaces of 3D models.",
    "links": [("Source code", GH + "GLSL-Shaders", "code")],
    "blocks": [
      ("p", "Programmed portions of OpenGL’s graphics pipeline by writing a few different vertex and fragment shaders to apply different coloration effects to the surfaces of 3D models."),
      ("p", "Shaders demo video and images as follows:"),
      ("video", {"file": "glsl-shaders", "w": 1920, "h": 1080, "title": "GLSL shaders demo"}),
      ("gallery", [shot("matcap-blue-purple", "", "Matcap shader, blue-purple"), shot("matcap-chrome", "", "Matcap shader, chrome"),
                   shot("matcap-orange-green", "", "Matcap shader, orange-green"), shot("matcap-outline", "", "Matcap shader, outline"),
                   shot("matcap-pearl", "", "Matcap shader, pearl"), shot("matcap-red-clay", "", "Matcap shader, red clay"),
                   shot("matcap-red-plastic", "", "Matcap shader, red plastic"), shot("surface-normals", "", "Surface normals shader"),
                   shot("vertex-deformation", "", "Vertex deformation shader"), shot("bloom", "", "Bloom post-process shader"),
                   shot("overview", "", "Overview of all shaders"), shot("gaussian-blur", "", "Gaussian blur post-process shader"),
                   shot("greyscale", "", "Greyscale post-process shader"), shot("custom-shader", "", "Custom shader"),
                   shot("sobel", "", "Sobel edge-detection shader"), shot("worley-noise", "", "Worley noise shader"),
                   shot("lambert", "", "Lambert shader"), shot("blinn-phong", "", "Blinn-Phong shader")]),
    ],
  },
  {
    "slug": "animation-toolkit", "old": "animation-toolkit", "img": "animation-toolkit",
    "title": "Animation Toolkit", "cats": ["animation", "tools"], "tags": ["Curve editor", "FK / IK", "Particle systems"],
    "excerpt": "An Interactive 2D animation toolkit that includes: Curve Editor Rotations, FK, IK, Particle Systems, Firework Simulation, Behavioural Animation",
    "blocks": [
      ("p", "An Interactive 2D animation toolkit that includes:"),
      ("ul", ["Curve Editor", "Rotations", "FK", "IK", "Particle Systems", "Firework Simulation", "Behavioural Animation"]),
      ("label", "Demo on YouTube:"),
      ("embed", {"src": "https://www.youtube-nocookie.com/embed/IqU5NDMYwRg", "title": "Animation Toolkit demo on YouTube"}),
      ("label", "On Bilibili:"),
      ("embed", {"src": "https://player.bilibili.com/player.html?bvid=BV1rr421H7VA&autoplay=0", "title": "Animation Toolkit demo on Bilibili"}),
    ],
  },
  {
    "slug": "maya-3d-scene-modeling-project", "old": "maya-3d-scene-modeling-project", "img": "maya-3d-scene-modeling",
    "title": "Maya 3D Scene Modeling Project", "cats": ["art"], "tags": ["Maya 2024", "Modeling", "Lighting"],
    "excerpt": "A room modeling project using Maya 2024. After modeling, mapping and finally lighting, I built a room.",
    "blocks": [
      ("p", "A room modeling project using Maya 2024. After modeling, mapping and finally lighting, I built a room."),
      ("p", "Final renders are as follows:"),
      ("gallery-wide", [shot("render-2", "", "Room render, view 2"), shot("render-1", "", "Room render, view 1"), shot("render-3", "", "Room render, view 3"),
                        shot("render-5", "", "Room render, view 5"), shot("render-4", "", "Room render, view 4")]),
    ],
  },
  {
    "slug": "motion-capture", "old": "motion-caption", "img": "motion-capture",
    "title": "Motion Capture", "cats": ["animation"], "tags": ["MotionBuilder 2024", "Motion capture"],
    "excerpt": "A motion capture animation production project, I used the motion capture equipment of the SIGLAB at the University of Pennsylvania and produced motion capture animation using MotionBuilder 2024.",
    "blocks": [
      ("p", "This is a motion capture animation production project, I used the motion capture equipment of the SIGLAB at the University of Pennsylvania and produced motion capture animation using MotionBuilder 2024."),
      ("p", "In the animation below, I removed the T-Pose between three different actions and smoothed the transitions. Here is the final motion capture animation production effect along with behind-the-scenes footage."),
      ("video", {"file": "motion-capture", "w": 1920, "h": 1080, "title": "Final motion capture animation"}),
      ("video", {"file": "motion-capture-behind-the-scenes", "w": 1920, "h": 1080, "title": "Motion capture behind the scenes"}),
    ],
  },
  {
    "slug": "houdini-based-fireworks-simulation", "old": "houdini-based-fireworks-simulation", "img": "houdini-fireworks",
    "title": "Houdini-based Fireworks Simulation", "cats": ["animation"], "tags": ["Houdini", "Particle simulation"],
    "excerpt": "This is a fireworks physics simulation project created with Houdini, in which I produced particle simulations for four different types of fireworks effects.",
    "blocks": [
      ("p", "This is a fireworks physics simulation project created with Houdini, in which I produced particle simulations for four different types of fireworks effects."),
      ("video", {"file": "houdini-fireworks", "w": 1920, "h": 1080, "title": "Houdini fireworks simulation"}),
    ],
  },
  {
    "slug": "gem-match-game", "old": "jewel-crush-mini-game", "img": "gem-match-game",
    "title": "Gem Match Game", "cats": ["games"], "tags": ["C++", "Qt", "Easy2D"],
    "excerpt": "This is a classic gem puzzle game written in C++, Qt Widget and the Easy2D game engine.",
    "links": [("Source code", GH + "Gem-Match", "code")],
    "blocks": [
      ("p", "This is a classic gem puzzle game written in C++, Qt6, and the Easy2D game engine."),
      ("p", "In this game, I was responsible for creating the game animations, developing the game client logic, and contributing to the game’s art design. The game client was developed using Qt Widgets and the Easy2D engine. For the gem elimination animations, we implemented an animation delay-lock system to ensure that animations play correctly during consecutive eliminations."),
      ("video", {"file": "gem-match-game", "w": 1742, "h": 728, "title": "Gem Match Game gameplay"}),
    ],
  },
]

HOME_ABOUT = [
    "Hi! I’m Jichu! I am really glad that you have come to my website!",
    "I’m a <strong>Graphics Performance Engineer</strong> at <strong>TikTok</strong>, optimizing its real-time effect rendering engine. I graduated from the University of Pennsylvania (UPenn) in <strong>May 2026</strong> with a master’s in <strong>Computer Science &amp; Computer Graphics</strong>.",
    'Before that, I interned at TikTok, <a href="https://www.infoldgames.com/en/home">Infold Games</a>, <a href="https://www.apple.com/">Apple Inc.</a> and the <a href="https://www.ualberta.ca/en/index.html">University of Alberta</a>, and was a teaching assistant for UPenn’s computer graphics courses. During my studies in Software Engineering and Computer Graphics, I designed &amp; developed various interesting games and software toolkits.',
    "I have shared my previous works here, and I will be really excited if you like it! &lt;3",
]

ABOUT_INTRO = [
    "Hi! I’m Jichu! I am really glad that you have come to my website!",
    "I’m a <strong>Graphics Performance Engineer</strong> at <strong>TikTok</strong>, where I optimize the real-time effect rendering engine used by hundreds of millions of creators every day.",
    "I graduated from the University of Pennsylvania (UPenn) in May 2026 with a Master of Science in Engineering in Computer Science &amp; Computer Graphics. I specialize in GPU rendering, real-time graphics and advanced rendering techniques, with hands-on experience in CUDA, OpenGL, Vulkan and Unreal Engine.",
    "During my studies in Software Engineering and Computer Graphics, I designed &amp; developed various interesting games and software toolkits.",
]
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

def social(indent="      "):
    items = "".join(f'\n{indent}  <li><a href="{E(u)}">{icon(i)}{E(n)}</a></li>' for n, u, i in SOCIAL)
    return f'<ul class="social">{items}\n{indent}</ul>'

def tags_html(p, indent="        "):
    items = "".join(f'<li class="cat">{E(CAT_LABEL[c])}</li>' for c in p["cats"]) + "".join(f"<li>{E(t)}</li>" for t in p["tags"])
    return f'{indent}<ul class="tags" aria-label="Category and tech stack">{items}</ul>'

def page(*, root, path, title, desc, body, og_image, current="", scripts=()):
    canonical = f"{SITE}/{path}"
    nav = [("Works", f"{root}#works", "works"), ("About", f"{root}about/", "about")]
    cur = ' aria-current="page"'
    nav_html = "".join(f'\n      <a href="{u}"{cur if key == current else ""}>{n}</a>' for n, u, key in nav)
    js = "".join(f'\n<script src="{root}assets/js/{s}?v={ASSET_V}" defer></script>' for s in scripts)
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
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="preload" href="{root}assets/fonts/playfair-display-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{root}assets/fonts/playfair-display-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/css/site.css?v={ASSET_V}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header class="site-header">
  <div class="wrap">
    <p class="site-title"><a href="{root}">Jichu · Art</a></p>
    <p class="site-tagline">A site about Jichu &amp; Art</p>
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
    {social(indent="    ")}
    <p class="copyright">© Jichu Mao</p>
  </div>
</footer>{js}
</body>
</html>
"""

def img_tag(key, root, *, thumb=True, cls="", alt="", lazy=True):
    m = MAN[key]
    src = f"{root}assets/img/{key}{'-thumb' if thumb else ''}.webp"
    w, h = (m["tw"], m["th"]) if thumb else (m["w"], m["h"])
    c = f' class="{cls}"' if cls else ""
    l = ' loading="lazy" decoding="async"' if lazy else ""
    return f'<img{c} src="{src}" width="{w}" height="{h}" alt="{E(alt)}"{l}>'

def gallery(proj, items, root, wide=False):
    n = len(items)
    cols = "one" if n == 1 else "two" if n in (2, 4) else "three" if n in (3, 5, 6, 9) else "many"
    out = [f'<ul class="gallery{" wide" if wide else ""} {cols}">']
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
            inner = f'<a class="shot" href="{root}assets/img/{key}.webp"{dc}>{img_tag(key, root, alt=s["alt"])}</a>'
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
        elif kind == "ul":
            prose.append("        <ul>\n" + "\n".join(f"          <li>{E(i)}</li>" for i in val) + "\n        </ul>")
        elif kind == "h2":
            media.append(f"      <h2>{E(val)}</h2>")
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

def links_html(proj):
    if not proj.get("links"):
        return ""
    items = "".join(f'\n        <li><a class="button" href="{E(u)}">{icon(i)}{E(n)}</a></li>' for n, u, i in proj["links"])
    return f'\n      <ul class="project-links">{items}\n      </ul>'

# ---------------------------------------------------------------- pages

def build_home():
    root = ""
    cards = []
    for p in PROJECTS:
        key = f'{p["img"]}/cover'
        cards.append(f"""      <li class="work" data-cats="{" ".join(p["cats"])}">
        <div class="work-frame">{img_tag(key, root, cls="work-thumb", alt="")}</div>
        <h3><a href="works/{p["slug"]}/">{E(p["title"])}</a></h3>
{tags_html(p)}
        <p class="work-excerpt">{E(p["excerpt"])}</p>
        <span class="button" aria-hidden="true">Read more</span>
      </li>""")
    counts = {c: sum(c in p["cats"] for p in PROJECTS) for c, _ in CATEGORIES}
    filters = f'<button type="button" data-cat="all" aria-pressed="true">All <span>{len(PROJECTS)}</span></button>' + "".join(
        f'<button type="button" data-cat="{c}" aria-pressed="false">{E(label)} <span>{counts[c]}</span></button>' for c, label in CATEGORIES)
    about = "\n".join(f"      <p>{t}</p>" for t in HOME_ABOUT)
    hero = MAN["home/hero"]
    body = f"""<section class="hero">
  <div class="hero-media">
    <img class="hero-art" src="assets/img/home/hero.webp" srcset="assets/img/home/hero-thumb.webp 1200w, assets/img/home/hero.webp 2400w" sizes="100vw" width="{hero["w"]}" height="{hero["h"]}" alt="" fetchpriority="high">
    <canvas class="hero-canvas" aria-hidden="true"></canvas>
  </div>
  <div class="wrap hero-text">
    <p class="hero-year" id="year">2026</p>
    <script>document.getElementById("year").textContent = new Date().getFullYear();</script>
    <h1>Jichu Mao</h1>
    <p class="hero-role">Graphics Performance Engineer at TikTok</p>
    <p class="hero-lead">I work on real-time rendering and GPU performance. This site is my hub for art, CG and games: the renderers, shaders, tools and games I’ve built along the way.</p>
    <p class="hero-actions"><a class="button-fill" href="#works">See the work</a><a class="button" href="about/">About me</a></p>
  </div>
</section>

<section class="works" id="works">
  <div class="wrap">
    <div class="section-head">
      <p class="eyebrow">Portfolio</p>
      <h2>Selected Works</h2>
      <p>Renderers, shaders, tools, games and animation. Open a project for demos, renders and source code.</p>
      <div class="work-filter" role="group" aria-label="Filter works by category" hidden>{filters}</div>
    </div>
    <ul class="work-grid">
{chr(10).join(cards)}
    </ul>
  </div>
</section>

<section class="about-band" id="about">
  <div class="wrap about-grid">
    <div class="about-side">
      {img_tag("home/avatar", root, thumb=False, cls="avatar", alt="Portrait of Jichu Mao")}
      {social()}
    </div>
    <div class="about-main">
      <p class="eyebrow">About me</p>
      <h2>Jichu Mao</h2>
{about}
      <a class="button-fill" href="about/">Read more</a>
    </div>
  </div>
</section>"""
    write("index.html", page(root=root, path="", title="Jichu Mao – Graphics Performance Engineer | Jichu · Art",
                             desc="Portfolio of Jichu Mao, Graphics Performance Engineer at TikTok: real-time rendering, GPU path tracing, shaders, graphics tools, games and animation.",
                             body=body, og_image="assets/img/home/hero-thumb.webp", current="", scripts=("hero.js", "works.js")))

def build_projects():
    root = "../../"
    for i, p in enumerate(PROJECTS):
        prose, media, scripts = render_blocks(p, root)
        prev_p, next_p = PROJECTS[i - 1] if i > 0 else None, PROJECTS[i + 1] if i + 1 < len(PROJECTS) else None
        prev_html = f'<a class="prev" href="../{prev_p["slug"]}/"><span>Previous</span>{E(prev_p["title"])}</a>' if prev_p else "<span></span>"
        next_html = f'<a class="next" href="../{next_p["slug"]}/"><span>Next</span>{E(next_p["title"])}</a>' if next_p else "<span></span>"
        body = f"""<article class="project wrap">
  <a class="back" href="{root}#works">← All works</a>
  <div class="project-grid">
    <header class="project-info">
      <h1>{E(p["title"])}</h1>
{tags_html(p, indent="      ")}
      <div class="prose">
{prose}
      </div>{links_html(p)}
    </header>
    <div class="project-media">
{media}
    </div>
  </div>
  <nav class="pager" aria-label="More works">
    {prev_html}
    {next_html}
  </nav>
</article>"""
        write(f'works/{p["slug"]}/index.html',
              page(root=root, path=f'works/{p["slug"]}/', title=f'{p["title"]} – Jichu · Art', desc=p["excerpt"],
                   body=body, og_image=f'assets/img/{p["img"]}/cover-thumb.webp', current="works", scripts=scripts))

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
      {social()}
    </div>
    <div class="about-main">
      <h1>Jichu Mao</h1>
{intro}
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
                                   body=body, og_image="assets/img/home/avatar.webp", current="about"))

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
    urls = [""] + ["about/"] + [f'works/{p["slug"]}/' for p in PROJECTS]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{SITE}/{u}</loc></url>\n" for u in urls) + "</urlset>\n")

build_home(); build_projects(); build_about(); build_redirects(); build_misc()
print("built", len(PROJECTS), "project pages")
