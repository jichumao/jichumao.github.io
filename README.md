# jichu.art

Static portfolio site (it used to run on WordPress). Plain HTML, CSS and a few small scripts, no framework. GitHub Pages serves the files as they are, behind Tencent Cloud EdgeOne for visitors in China and elsewhere.

## Layout

```
index.html                    home page (opening, five large projects, the rest as a compact grid with a category filter, about)
about/index.html              about page (experience, education, skills)
resume/index.html             one-page résumé, written from the same data as the about page
assets/Jichu-Mao-Resume.pdf   the résumé as a PDF (the "Résumé (PDF)" buttons link to it)
works/<project>/index.html    one page per project
index.php/<old-slug>/         redirects from the old WordPress URLs
404.html
assets/css/site.css           all styles
assets/js/works.js            category filter on the compact grid ("More work")
assets/js/previews.js         plays a large card's preview while the card is in the middle of the screen, or hovered
assets/js/studio.js           the home page's opening: JICHU · ART path traced live (WebGL2)
assets/js/home.js             the home page's scroll fade and covers converging into view
assets/js/clips.js            plays the short looping clips, and the preview on a project page's cover, while they are on screen
assets/js/lightbox.js         full-size image viewer for galleries
assets/img/<project>/         images (WebP): name.webp is full size, name-thumb.webp is the thumbnail
assets/video/                 videos and clips (H.264 MP4, faststart) and their poster images
assets/fonts/                 Playfair Display (titles, figures), Open Sans (text), JetBrains Mono (tech stack, table numbers); all SIL Open Font License
tools/build.py                generator for every HTML page; all the text lives in it
tools/covers.py               builds the project covers
tools/previews.py             builds the short preview loops that play on the cards
tools/cover-src/              video frames and screenshots that the covers use, and the scripts behind the three drawn covers
tools/resume.py               prints resume/index.html to the PDF
tools/og.py                   writes the pictures shown when a page is shared (og.jpg)
tools/manifest.json           image and clip dimensions the generator reads

photography/index.html        photography: opening slideshow, subject links, one tile per series, about
photography/<series>/         one page per series
photography/<subject>/        one page per subject (landscape, coast, night ...), plus all/ with every photograph
photography/zh/               the same pages in Chinese (same photographs, stylesheet and scripts)
photography/assets/           photo.css (all styles), viewer.js (full-screen viewer), hero.js (opening slideshow), timeline.js (the timeline and its globe); written by hand
photography/img/              NNN-2400.webp, NNN-1400.webp, NNN-700.webp for each photograph (long side in pixels)
tools/photography.py          generator for the photography pages: series, order, rows, captions, timeline
tools/footprint.py, footprint.json   which dots of the timeline's globe are land (made once from Natural Earth)
tools/photography_zh.py       the Chinese text of the photography section
tools/photos.py               prepares new photographs (resize, sRGB, strip metadata)
tools/photos.json             pixel sizes, placeholder colour and camera settings of each photograph
```

## Editing

The pages are generated, so the text of the whole site sits in one file, `tools/build.py`:

- `PROJECTS`: one entry per project. The order of the list is the order of the compact grid on the home page and of the Previous / Next links.
- `FEATURED`: the five projects shown large at the top of the home page, in order. The first gets the full-width card with its `stats`. Every other project appears under "More work".
- `CATEGORIES`: the filter buttons above "More work".
- `HOME_ABOUT`: the two paragraphs at the foot of the home page.
- `ABOUT_INTRO`, `WORK`, `EDU`, `SKILLS`, `HOBBIES`: the about page. `WORK`, `EDU`, `SKILLS` and `FEATURED` also fill the résumé.
- `EMAIL`, `SOCIAL`: contact links in the footer and on the about page.
- `GOATCOUNTER`: visitor statistics, off while it is empty (see below).

Fields of a project:

| Field | Where it shows |
| --- | --- |
| `title`, `year`, `kind` | card and page header (`kind` is "Team project", "Individual project" or empty) |
| `tags` | tech stack under the title, spelled the way a résumé or job posting spells it. The home page shows the first three; the project page shows all |
| `excerpt` | card text and the page's meta description |
| `lead` | opening sentence of the project page |
| `facts` | label and value pairs under the page header |
| `stats` | measured results as figure and description; leave out when there are none |
| `links` | buttons for source code, demo, paper |
| `blocks` | text blocks (`p`, `html`, `ul`, `h3`, `features`) fill the left column, media blocks (`h2`, `label`, `note`, `steps`, `bars`, `video`, `embed`, `table`, `gallery`, `gallery-wide`) the right |

`features` is a list of `(icon, name, detail)` rows; the icon names are the keys of `ICONS`. `steps` is a numbered sequence of `(name, detail)`, for things that really happen in order. `bars` is a bar chart drawn in HTML: `{"unit": "ms", "rows": [(label, value, highlight), ...]}`, every bar on the same scale; `note` is a small line of text under it. Images whose name starts with `chart-` are shown inverted so that light spreadsheet charts match the dark page.

After editing, rebuild from the repository root (Python 3, no packages needed):

```
python3 tools/build.py . tools/manifest.json
```

A quick text fix can also be made straight in the HTML. Make the same change in `tools/build.py`, otherwise the next rebuild overwrites it.

The stylesheet and scripts are linked as `site.css?v=13`, `works.js?v=13`, and so on. After changing one of them, raise `ASSET_V` in `tools/build.py` and rebuild, so browsers fetch the new file instead of a cached one.

All links are relative, so the site works both at a domain root and under a sub-path.

## Home page opening

The top of the home page is the site's name, JICHU · ART, path traced live in the visitor's browser by `assets/js/studio.js` (WebGL2, no libraries). The letters stand on a wet black floor in front of a thin arch of light (half a torus, ray-marched only through the slab it lies in), which the floor reflects into a full ring. The letters are light, neutral materials, so that they read against the dark and the coloured light plays over them: a frosted-glass J, a milky U and a frosted A that light travels through (random-walk subsurface scattering inside the letter, each with its own scattering density), a chrome I, a brushed-silver C and a satin-aluminium R (GGX microfacets with Smith shadowing and Schlick Fresnel), a neon H, a glowing dot and a porcelain T. They stand in light haze (free-flight sampling, Henyey-Greenstein phase function; the light the haze scatters towards the camera is estimated once along every camera ray, and at every scattering event further along a path). The letters are signed distance fields, strokes extruded with rounded edges, ray-marched inside each letter's bounding box; the H's tubes, the dot and the arch are lights, sampled over their surfaces, and light sampling and BSDF sampling are combined by multiple importance sampling. A white softbox behind the camera and a cool strip above the letters (kept out of the floor's reflections: light linking) give the white light.

The colours flow without tracing again. Light transport is linear in what the lights emit, so each group of lights is traced with white light into its own running average (multiple render targets: the white lights, and three coloured groups), and the groups are mixed in their colours of the moment every frame (`COMBINE`). The arch's colour runs smoothly along it because it is split across the three groups by quadratic Bernstein weights of the position along the arch, so any three colours blend along it exactly; the H belongs to the first group and the dot to the second. The colours are `FLOW` and `colours(t)`: amber, coral, rose, violet and indigo and back, each group a little behind the one on its left, about 40 s there and back. Once the picture has converged nothing more is traced; only the mix is redone, about 20 times a second.

Each frame is denoised before it is shown: an edge-aware à-trous wavelet filter (as in SVGF), four passes over the mixed picture, guided by what the camera ray hit first (normal and distance) and by how noisy each pixel's average still is (that noise averaged over its 3 × 3 neighbours, so a pixel whose few samples all missed a light does not stay as a dark speck). It smooths hard at the start and lets go by itself as samples accumulate, so it stays on to the end. Then a thin lens, ACES tone mapping and a glow around the brightest light. The letters' shapes are the `strokes` function in the shader; materials, lights and the haze density are the constants at its top; where each letter stands is `layout()` (one gently curved row on wide screens, JICHU behind ·ART on tall ones) and the arch is `arch()`. The picture starts as noise and converges, stopping at 512 samples per pixel. The far wall ends a path after the light it receives directly (it is nearly black, so what it would bounce on is invisible), which keeps the upper half of the picture cheap. Dragging sideways turns the camera. The resolution is set so a frame costs the GPU about 10 ms (from timer queries where the browser has them), up to the screen's own pixels (at most about 4.5 million); once it is at full resolution, a GPU with time to spare traces several samples each frame (up to eight, still within ~10 ms), so on a fast desktop GPU it converges in a few seconds. A sample that comes out NaN or infinite is dropped. It stops while off screen or in a hidden tab. It needs five render targets; with fewer it shows the still picture.

Where it cannot run (no WebGL2 or float render targets, "reduce motion", no JavaScript) the page shows `assets/img/home/studio-1600.webp` / `studio-1000.webp` (wide) and `studio-tall-720.webp` (tall) instead. They are this same renderer's output at the default colours (`time` 1.3): in a browser, `Studio.make(canvas, {preserve: true})`, `size(w, h)` at the file's pixel size, `step()` until 1,024 samples (the denoiser on, as on the page), then the canvas saved as WebP. Render them again after changing the scene. The home page's sharing picture is cut from the wide one.

When the page scrolls, the opening falls behind it (darker, slower, the name fading), and each work cover starts as a noisy, unconverged render that settles into the picture as it comes into view (`assets/img/home/speckle.png`); both are in `assets/js/home.js`. Visitors who ask for reduced motion get the still picture and no scroll effects. The words on the opening are the name, one line under it (`hero-lead`) and the caption, all in `build_home()`.

To use another picture: export it at the same five sizes under the same names (or change the names in `build_home()`), keep the important part right of centre because the text covers the left, then run `python3 tools/og.py .` so the sharing picture follows.

## Résumé

`resume/index.html` is written by `tools/build.py` from `WORK`, `EDU`, `SKILLS` and the `FEATURED` projects; it carries the e-mail address and the public links and nothing more personal. The PDF is that page printed:

```
python3 tools/build.py . tools/manifest.json
python3 tools/resume.py .          # needs Chrome, Chromium or Edge; or print the page to PDF by hand
```

To use a résumé written elsewhere, replace `assets/Jichu-Mao-Resume.pdf` with it and skip `tools/resume.py`. Keep it to one page: if the text grows, lower the font size in the `<style>` of `build_resume()`.

## Visitor statistics

On. The site reports page views to GoatCounter, which counts without cookies, so no consent banner is needed. The numbers are at https://jichu.goatcounter.com (sign in with the account that owns the code `jichu`). The code is `GOATCOUNTER` near the top of `tools/build.py`; every page, photography included, loads one small script from `gc.zgo.at`. Set it to `""` and rebuild to switch statistics off.

## Brand icons on links

Links to GitHub, YouTube, LinkedIn and Bilibili show plain line icons until that service's own SVG is placed in `assets/icons/`. `assets/icons/README.md` lists the file names and the official pages to download them from.

## Covers

Every cover is 1500 x 1000 px, and `tools/covers.py` lists, per project, its source pictures and the crop for each. Page images are read from `assets/img/<project>/`; video frames and other screenshots from `tools/cover-src/`. There are four layouts:

| Entry | Looks like | Used for |
| --- | --- | --- |
| `[main, tile, tile]` | a square main panel on the left, two tiles on the right | a project with one picture strong and large enough to lead |
| `("full", image, crop)` | one image across the whole frame | Mini Minecraft's title art, the drawn covers |
| `("grid", columns, [pictures])` | equal cells, row by row | a set of variants (GLSL Shaders shows sixteen), or sources too small for a big panel |
| `("rows", [(share, [pictures]), ...])` | rows of different heights | Physically-Based Shaders: two scenes over a five-step roughness strip |

A cover looks soft when a picture is enlarged beyond its own pixels. The script prints the largest enlargement in each cover: keep it near 1.0 for a main panel, and choose a grid when the sources are small.

```
python3 tools/covers.py . tools/manifest.json                 # all covers
python3 tools/covers.py . tools/manifest.json cuda-path-tracer # one project
python3 tools/build.py . tools/manifest.json
```

The script needs Pillow and NumPy (`pip install pillow numpy`). For each project it writes `cover.webp`, `cover-thumb.webp` (cards), `cover-mini.webp` (Previous / Next links) and `glow.webp` (the blurred colour behind the page header).

### Previews

Each card also has `assets/video/preview-<project>.mp4`: a silent 600 x 600 loop of a few seconds that covers the main panel (900 x 600 over the whole frame for a full-frame cover). It plays while the card is in the middle of the screen or hovered. `tools/previews.py` cuts it from the project's video, or cross-fades a few of its renders when there is no video. It needs ffmpeg and Pillow.

```
python3 tools/previews.py .                    # all previews
python3 tools/previews.py . cuda-path-tracer   # one project
```

Three covers are not made from screenshots; each has its script next to its source in `tools/cover-src/`:

- `tree-creator`: a new render produced by running the plugin's own L-system core outside Maya. `tools/cover-src/tree-plate/README.md` says exactly how, and the project page says so too.
- `motion-capture`: five poses cut out of the finished animation's own video frames and set side by side (`tools/cover-src/mocap-poses/poses.py`; needs ffmpeg, NumPy and SciPy).
- `stream-compaction`: a drawing of the algorithm, each kept element joined to its compacted position (`tools/cover-src/stream-compaction/diagram.py`). It also writes the two stage pictures the preview fades through.

## Adding a project

1. Put images in `assets/img/<project>/`: a full-size WebP (long side up to about 2500 px) and a `-thumb` version about 800 px wide. Galleries offer both to the browser, which takes the full-size file on sharp screens and in wide slots, so keep the full size genuinely larger than the thumbnail.
2. Add each image to `tools/manifest.json` with its width and height (`w`, `h` for the full size, `tw`, `th` for the thumbnail). Copy the shape of an existing entry.
3. Add the project's three cover panels to `COVERS` in `tools/covers.py` and its preview to `PREVIEWS` in `tools/previews.py`, then run both.
4. Add an entry to `PROJECTS` in `tools/build.py` and rebuild. The card, the project page, the Previous / Next links and `sitemap.xml` are all written for you. Add its slug to `FEATURED` if it should be one of the large cards.
5. Run `python3 tools/og.py .` so the new page has its sharing picture.

A project made of photographs that are already in the photography section (Virtual Subway is one) can reuse them instead of steps 1 and 2: `python3 tools/photos.py --project virtual-subway 391:interior 398:side` copies photographs 391 and 398 into `assets/img/virtual-subway/` under those names and records them in the manifest.

## Photography

`jichu.art/photography/` is a separate section with its own look (black ground, no page chrome around the pictures). It shares only the fonts and the favicon with the rest of the site, and `tools/build.py` builds it along with everything else.

**How the pages are laid out.** No photograph is ever cropped on a series page. Each series is a list of rows; a row is as wide as the screen unless that would make it taller than the screen, in which case it is as tall as the screen and centred. So a row of one landscape frame fills the height, and a row of two or three frames fills the width. On a phone held upright the same sequence runs one photograph per line. The rule is three lines of CSS (`.row` in `photo.css`); the generator only supplies each photograph's aspect ratio.

**Everything editable is in `tools/photography.py`:**

- `SERIES`: one entry per series. `rows` is the sequence, for example `[[58], [57, 54], [61]]` is one frame, then a pair, then one frame. `cover` is the photograph on the index tile. `focus` (optional) says which part of the cover to keep where it has to be cropped: the "More series" tiles at the foot of a series and the share image.
- `CHAPTERS`: the index page. Each chapter has a title, one sentence, the series in it and how many covers sit in a row on a wide screen (`per_row`: 2, 3 or 4; a row of four becomes two rows of two below 1000 px). Covers are never cropped there: the covers of a row share one height and divide the width in proportion, as on a series page, so a portrait or square cover is shown as it was shot. Every series belongs to exactly one chapter, and the order here is the order of the whole section.
- `SLIDES`: the opening slideshow. Each entry is a photograph for wide screens, one for upright phones, and the series it links to. They are the strongest pictures of the whole section, judged at the slideshow's own full-screen crop, one per series.
- `SUBJECTS`: the subject pages. A photograph can sit under several subjects and must sit under at least one; the rows on these pages are packed automatically.
- `TIMELINE`: the timeline page (`photography/timeline/`, 足迹 in Chinese), which lists the series newest first: for each series the day it was made (orders the page; only the month is shown), where it was made (latitude, longitude; none for Subway) and, if the series has no "where", what to show instead. `MAP_LABELS` are the names written on the globe beside it. On wide screens the globe stays beside the list and `photography/assets/timeline.js` turns it to the series in the middle of the screen, lighting the places passed so far and drawing an arc from each to the next; on narrow screens it sits above the list and turns slowly. Its dots are an even spread of points over the sphere; which of them are land is in `tools/footprint.json`, made once by `tools/footprint.py` from Natural Earth's public-domain outline (instructions at the top of that file). The page's sharing picture is drawn from the same data by `tools/og.py`.
- `PLACE`: where a single photograph was taken, when that is more exact than its series' `where`. Shown in the viewer's caption.
- `ALT`: one plain sentence per photograph. The build stops if one is missing.
- `ABOUT`: the text at the foot of the index page.
- A series can carry `link=("How it was made", "works/virtual-subway/")`: a line under its note that leads to a page of the main site.

**The Chinese edition.** `photography/zh/` holds every page again in Chinese, and each page links to its counterpart in the top bar (中文 / EN). The Chinese text is in `tools/photography_zh.py`: `ZH` maps each English title, place and note, exactly as written in `tools/photography.py`, to its Chinese, and `ALT_ZH` holds the photograph descriptions. Whatever is missing there is shown in English, and the build prints a list of it, so a new series still builds before it is translated.

**Adding photographs.**

1. Pick an unused number for each and run `python3 tools/photos.py 401 path/to/a.jpg 402 path/to/b.jpg`. It writes the three sizes into `photography/img/` and records them in `tools/photos.json`. Nothing from the file's metadata is copied (no GPS, serial number or date); only focal length, aperture, shutter speed and ISO are kept for the caption. Each output file is then tagged with the author and a rights statement (XMP, invisible; `AUTHOR`, `RIGHTS` in `tools/photos.py`). Numbers listed in `UNTAGGED` are left without the tag: use it for pictures someone else took. `python3 tools/photos.py --stamp` tags every file again after a change, without touching the picture data.
2. Put the numbers into a series' `rows` (or add a new series and list it in a chapter of `CHAPTERS`), write their `ALT` lines (and the Chinese ones in `tools/photography_zh.py`), and rebuild.

Rows read best when the aspect ratios in a row add up to between 1.5 and 3.5: one landscape; a landscape and a portrait; two squares; three portraits. A portrait on its own leaves most of a wide screen empty.

## Media

- Images: `cwebp -q 88 in.png -o out.webp`, thumbnails at about 800 px wide and `-q 82`.
- Videos: `ffmpeg -i in.mp4 -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart out.mp4`
- Short looping clips (converted from GIFs): same command with `-an` instead of the audio options, plus a poster image taken from the first frame.
- Keep single files well under 50 MB; GitHub rejects files over 100 MB.

## Domain, hosting and HTTPS

The `CNAME` file holds the custom domain (`jichu.art`); GitHub Pages is the origin. In front of it is Tencent Cloud EdgeOne (site `zone-35jv4gv2ke36`, Personal plan, service area global including mainland China), so visitors in China are served from mainland nodes. DNS is hosted on DNSPod: `@` and `www` are CNAMEs to `jichu.art.eo.dnse0.com` and `www.jichu.art.eo.dnse0.com` (the old A records to GitHub are paused, not deleted). Both accelerated domains pull from `jichumao.github.io` over HTTPS with the visitor's host (`jichu.art` / `www.jichu.art`) as the Host header, so GitHub serves the site and redirects `www` to the bare domain. EdgeOne does not verify the origin's certificate by default, so it keeps working if GitHub can no longer renew its own certificate for `jichu.art` (it cannot see the domain's DNS any more). Visitors get EdgeOne's free certificate (TrustAsia, issued and renewed automatically through DNSPod), HTTP is redirected to HTTPS (301). Caching at the edge: HTML follows GitHub's `Cache-Control: max-age=600`, so a new page is visible everywhere within about ten minutes; images, fonts, video, CSS and JS are kept for 30 days whatever GitHub says (rule engine rule `静态站缓存-jichu.art`, forced caching), so even a rarely visited page is served from a mainland node. Two consequences: CSS and JS URLs carry `?v=ASSET_V`, so bump `ASSET_V` in `tools/build.py` whenever they change, and always build with `tools/build.py` (it builds the photography pages with the same version; running `tools/photography.py` on its own writes `?v=1`); and after replacing an image or a video under the same file name, purge that URL in the EdgeOne console (清除缓存 → URL), or the old one stays at the edge for up to 30 days. The query string is part of the cache key. Pages served from mainland China must show the ICP filing number: it is in every footer (京ICP备2024041560号-1, linked to beian.miit.gov.cn). Keeping the domain served through Tencent Cloud is also what keeps the filing's access record alive. To go back to GitHub alone: resume the paused A records and delete the two CNAMEs in DNSPod.
