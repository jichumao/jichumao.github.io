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
assets/js/clips.js            plays the short looping clips while they are on screen
assets/js/lightbox.js         full-size image viewer for galleries
assets/img/<project>/         images (WebP): name.webp is full size, name-thumb.webp is the thumbnail
assets/video/                 videos and clips (H.264 MP4, faststart) and their poster images
assets/fonts/                 Playfair Display and Open Sans (SIL Open Font License)
tools/build.py                generator for every HTML page; all the text lives in it
tools/manifest.json           image and clip dimensions the generator reads
```

## Editing

The pages are generated, so the text of the whole site sits in one file, `tools/build.py`:

- `PROJECTS`: one entry per project (title, categories, tech-stack tags, excerpt, links, content blocks). The order of the list is the order on the home page.
- `CATEGORIES`: the filter buttons on the home page.
- `ABOUT_INTRO`, `WORK`, `EDU`, `SKILLS`, `HOBBIES`: the about page.
- `EMAIL`, `SOCIAL`: contact links in the footer and on the about page.

After editing, rebuild from the repository root (Python 3, no packages needed):

```
python3 tools/build.py . tools/manifest.json
```

A quick text fix can also be made straight in the HTML. Make the same change in `tools/build.py`, otherwise the next rebuild overwrites it.

The stylesheet and scripts are linked as `site.css?v=4`, `hero.js?v=4`, and so on. After changing one of them, raise `ASSET_V` in `tools/build.py` and rebuild, so browsers fetch the new file instead of a cached one.

All links are relative, so the site works both at a domain root and under a sub-path.

## Adding a project

1. Put images in `assets/img/<project>/`: a full-size WebP (long side up to 2000 px) and a `-thumb` version about 800 px wide.
2. Add each image to `tools/manifest.json` with its width and height (`w`, `h` for the full size, `tw`, `th` for the thumbnail). Copy the shape of an existing entry.
3. Add an entry to `PROJECTS` in `tools/build.py`: `slug`, `img` (cover), `title`, `cats`, `tags`, `excerpt`, `links` and `blocks`.
4. Rebuild. The card, the project page, the Previous / Next links and `sitemap.xml` are all written for you.

## Media

- Images: `cwebp -q 88 in.png -o out.webp`, thumbnails at about 800 px wide and `-q 82`.
- Videos: `ffmpeg -i in.mp4 -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart out.mp4`
- Short looping clips (converted from GIFs): same command with `-an` instead of the audio options, plus a poster image taken from the first frame.
- Keep single files well under 50 MB; GitHub rejects files over 100 MB.

## Custom domain and HTTPS

The `CNAME` file holds the custom domain (`jichu.art`). DNS: `@` A records point at GitHub Pages, `www` is a CNAME to `jichumao.github.io`. HTTPS is enforced in Settings → Pages. GitHub issues the certificate and renews it on its own for as long as the DNS records keep pointing at GitHub.
