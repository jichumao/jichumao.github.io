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
assets/js/previews.js         plays a card's preview while it is hovered (or, on touch screens, in the middle of the screen)
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
| `blocks` | text blocks (`p`, `html`, `ul`, `h3`, `features`) fill the left column, media blocks (`h2`, `label`, `steps`, `video`, `embed`, `table`, `gallery`, `gallery-wide`) the right |

`features` is a list of `(icon, name, detail)` rows; the icon names are the keys of `ICONS`. `steps` is a numbered sequence of `(name, detail)`, for things that really happen in order. Images whose name starts with `chart-` are shown inverted so that light spreadsheet charts match the dark page.

After editing, rebuild from the repository root (Python 3, no packages needed):

```
python3 tools/build.py . tools/manifest.json
```

A quick text fix can also be made straight in the HTML. Make the same change in `tools/build.py`, otherwise the next rebuild overwrites it.

The stylesheet and scripts are linked as `site.css?v=6`, `hero.js?v=6`, and so on. After changing one of them, raise `ASSET_V` in `tools/build.py` and rebuild, so browsers fetch the new file instead of a cached one.

All links are relative, so the site works both at a domain root and under a sub-path.

## Covers

Every project uses the same cover layout, 1500 x 1000 px: a square main panel on the left and two square tiles on the right, with no text in the image. `tools/covers.py` lists, per project, the three source images and the crop for each. Page images are read from `assets/img/<project>/`; video frames and other screenshots from `tools/cover-src/`.

```
python3 tools/covers.py . tools/manifest.json                 # all covers
python3 tools/covers.py . tools/manifest.json cuda-path-tracer # one project
python3 tools/build.py . tools/manifest.json
```

The script needs Pillow and NumPy (`pip install pillow numpy`). For each project it writes `cover.webp`, `cover-thumb.webp` (cards), `cover-mini.webp` (Previous / Next links) and `glow.webp` (the blurred colour behind the page header).

### Previews

Each card also has `assets/video/preview-<project>.mp4`: a silent 600 x 600 loop of a few seconds that covers the main panel while the card is hovered. `tools/previews.py` cuts it from the project's video, or cross-fades a few of its renders when there is no video. It needs ffmpeg and Pillow.

```
python3 tools/previews.py .                    # all previews
python3 tools/previews.py . cuda-path-tracer   # one project
```

## Adding a project

1. Put images in `assets/img/<project>/`: a full-size WebP (long side up to 2000 px) and a `-thumb` version about 800 px wide.
2. Add each image to `tools/manifest.json` with its width and height (`w`, `h` for the full size, `tw`, `th` for the thumbnail). Copy the shape of an existing entry.
3. Add the project's three cover panels to `COVERS` in `tools/covers.py` and its preview to `PREVIEWS` in `tools/previews.py`, then run both.
4. Add an entry to `PROJECTS` in `tools/build.py` and rebuild. The card, the project page, the Previous / Next links and `sitemap.xml` are all written for you.

## Media

- Images: `cwebp -q 88 in.png -o out.webp`, thumbnails at about 800 px wide and `-q 82`.
- Videos: `ffmpeg -i in.mp4 -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart out.mp4`
- Short looping clips (converted from GIFs): same command with `-an` instead of the audio options, plus a poster image taken from the first frame.
- Keep single files well under 50 MB; GitHub rejects files over 100 MB.

## Custom domain and HTTPS

The `CNAME` file holds the custom domain (`jichu.art`). DNS: `@` A records point at GitHub Pages, `www` is a CNAME to `jichumao.github.io`. HTTPS is enforced in Settings → Pages. GitHub issues the certificate and renews it on its own for as long as the DNS records keep pointing at GitHub.
