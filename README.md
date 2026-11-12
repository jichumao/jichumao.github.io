# jichu.art

Static portfolio site (it used to run on WordPress). Plain HTML, CSS and a few small scripts, no framework. GitHub Pages serves the files as they are.

## Layout

```
index.html                    home page (hero, works grid with category filter, about)
about/index.html              about page (experience, education, skills)
works/<project>/index.html    one page per project
index.php/<old-slug>/         redirects from the old WordPress URLs
404.html
assets/css/site.css           all styles
assets/js/hero.js             home hero: WebGL shader that makes the artwork drift (falls back to the plain image)
assets/js/works.js            category filter on the works grid
assets/js/previews.js         plays a card's preview while the card is in the middle of the screen, or hovered
assets/js/clips.js            plays the short looping clips, and the preview on a project page's cover, while they are on screen
assets/js/lightbox.js         full-size image viewer for galleries
assets/img/<project>/         images (WebP): name.webp is full size, name-thumb.webp is the thumbnail
assets/video/                 videos and clips (H.264 MP4, faststart) and their poster images
assets/fonts/                 Playfair Display (titles, figures), Open Sans (text), JetBrains Mono (tech stack, table numbers); all SIL Open Font License
tools/build.py                generator for every HTML page; all the text lives in it
tools/covers.py               builds the project covers
tools/previews.py             builds the short preview loops that play on the cards
tools/cover-src/              video frames and screenshots that the covers use
tools/manifest.json           image and clip dimensions the generator reads

photography/index.html        photography: opening slideshow, subject links, one tile per series, about
photography/<series>/         one page per series
photography/<subject>/        one page per subject (landscape, coast, night ...), plus all/ with every photograph
photography/assets/           photo.css (all styles), viewer.js (full-screen viewer), hero.js (opening slideshow); written by hand
photography/img/              NNN-2400.webp, NNN-1400.webp, NNN-700.webp for each photograph (long side in pixels)
tools/photography.py          generator for the photography pages: series, order, rows, captions
tools/photos.py               prepares new photographs (resize, sRGB, strip metadata)
tools/photos.json             pixel sizes, placeholder colour and camera settings of each photograph
```

## Editing

The pages are generated, so the text of the whole site sits in one file, `tools/build.py`:

- `PROJECTS`: one entry per project. The order of the list is the order on the home page.
- `CATEGORIES`: the filter buttons on the home page.
- `ABOUT_INTRO`, `WORK`, `EDU`, `SKILLS`, `HOBBIES`: the about page.
- `EMAIL`, `SOCIAL`: contact links in the footer and on the about page.

Fields of a project:

| Field | Where it shows |
| --- | --- |
| `title`, `year`, `kind` | card and page header (`kind` is "Team project", "Individual project" or empty) |
| `tags` | tech stack under the title, spelled the way a résumé or job posting spells it |
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

The stylesheet and scripts are linked as `site.css?v=8`, `hero.js?v=8`, and so on. After changing one of them, raise `ASSET_V` in `tools/build.py` and rebuild, so browsers fetch the new file instead of a cached one.

All links are relative, so the site works both at a domain root and under a sub-path.

## Covers

Every cover is 1500 x 1000 px. Most use a square main panel on the left and two square tiles on the right. A project with one strong wide image can use it across the whole frame instead: write its entry as `("full", image, crop)`. Mini Minecraft does, with the team's own title art. `tools/covers.py` lists, per project, the three source images and the crop for each. Page images are read from `assets/img/<project>/`; video frames and other screenshots from `tools/cover-src/`.

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

Two covers are not made from screenshots: `tree-creator` and `glsl-shaders` use new renders produced by running the project's own code (the L-system core; the shader files) outside its original application. `tools/cover-src/tree-plate/README.md` and `tools/cover-src/glsl-cow/README.md` say exactly how, and each project page says so too.

## Adding a project

1. Put images in `assets/img/<project>/`: a full-size WebP (long side up to 2000 px) and a `-thumb` version about 800 px wide.
2. Add each image to `tools/manifest.json` with its width and height (`w`, `h` for the full size, `tw`, `th` for the thumbnail). Copy the shape of an existing entry.
3. Add the project's three cover panels to `COVERS` in `tools/covers.py` and its preview to `PREVIEWS` in `tools/previews.py`, then run both.
4. Add an entry to `PROJECTS` in `tools/build.py` and rebuild. The card, the project page, the Previous / Next links and `sitemap.xml` are all written for you.

## Photography

`jichu.art/photography/` is a separate section with its own look (black ground, no page chrome around the pictures). It shares only the fonts and the favicon with the rest of the site, and `tools/build.py` builds it along with everything else.

**How the pages are laid out.** No photograph is ever cropped on a series page. Each series is a list of rows; a row is as wide as the screen unless that would make it taller than the screen, in which case it is as tall as the screen and centred. So a row of one landscape frame fills the height, and a row of two or three frames fills the width. On a phone held upright the same sequence runs one photograph per line. The rule is three lines of CSS (`.row` in `photo.css`); the generator only supplies each photograph's aspect ratio.

**Everything editable is in `tools/photography.py`:**

- `SERIES`: one entry per series, in the order they appear. `rows` is the sequence, for example `[[58], [57, 54], [61]]` is one frame, then a pair, then one frame. `cover` is the photograph on the index tile. `focus` (optional) says which part of the cover to keep where a tile has to crop it.
- `HOME_ROWS`: how the series tiles are paired on the index page.
- `SLIDES`: the opening slideshow. Each entry is a photograph for wide screens, one for upright phones, and the series it links to.
- `SUBJECTS`: the subject pages. A photograph can sit under several subjects and must sit under at least one; the rows on these pages are packed automatically.
- `PLACE`: where a single photograph was taken, when that is more exact than its series' `where`. Shown in the viewer's caption.
- `ALT`: one plain sentence per photograph. The build stops if one is missing.
- `ABOUT`: the text at the foot of the index page.

**Adding photographs.**

1. Pick an unused number for each and run `python3 tools/photos.py 401 path/to/a.jpg 402 path/to/b.jpg`. It writes the three sizes into `photography/img/` and records them in `tools/photos.json`. Nothing from the file's metadata is copied (no GPS, serial number or date); only focal length, aperture, shutter speed and ISO are kept for the caption. Each output file is then tagged with the author and a rights statement (XMP, invisible; `AUTHOR`, `RIGHTS` in `tools/photos.py`). Numbers listed in `UNTAGGED` are left without the tag: use it for pictures someone else took. `python3 tools/photos.py --stamp` tags every file again after a change, without touching the picture data.
2. Put the numbers into a series' `rows` (or add a new series and list it in `HOME_ROWS`), write their `ALT` lines, and rebuild.

Rows read best when the aspect ratios in a row add up to between 1.5 and 3.5: one landscape; a landscape and a portrait; two squares; three portraits. A portrait on its own leaves most of a wide screen empty.

## Media

- Images: `cwebp -q 88 in.png -o out.webp`, thumbnails at about 800 px wide and `-q 82`.
- Videos: `ffmpeg -i in.mp4 -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart out.mp4`
- Short looping clips (converted from GIFs): same command with `-an` instead of the audio options, plus a poster image taken from the first frame.
- Keep single files well under 50 MB; GitHub rejects files over 100 MB.

## Custom domain and HTTPS

The `CNAME` file holds the custom domain (`jichu.art`). DNS: `@` A records point at GitHub Pages, `www` is a CNAME to `jichumao.github.io`. HTTPS is enforced in Settings → Pages. GitHub issues the certificate and renews it on its own for as long as the DNS records keep pointing at GitHub.
