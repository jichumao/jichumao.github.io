# jichu.art

Static rebuild of the portfolio site that used to run on WordPress. Plain HTML, CSS and one small script: no build step, no framework. GitHub Pages serves the files as they are.

## Layout

```
index.html                    home page (hero, works grid, about)
about/index.html              about page
works/<project>/index.html    one page per project
index.php/<old-slug>/         redirects from the old WordPress URLs
404.html
assets/css/site.css           all styles
assets/js/hero.js             home hero: WebGL shader that makes the artwork drift (falls back to the plain image)
assets/js/lightbox.js         full-size image viewer for galleries
assets/img/<project>/         images (WebP): name.webp is full size, name-thumb.webp is the thumbnail
assets/video/                 videos (H.264 MP4, faststart) and their poster images
assets/fonts/                 Playfair Display and Open Sans (SIL Open Font License)
```

## Editing

- Text: edit the HTML file of the page directly.
- The header, navigation and footer are repeated in every page. If you change one, change it in all of them (search for `site-header` / `site-footer`).
- All links are relative, so the site works both at a domain root and under a sub-path.

## Adding a project

1. Copy an existing folder under `works/` and rename it.
2. Put images in `assets/img/<project>/`: a full-size WebP (long side up to 2000 px) and a `-thumb` version about 800 px wide.
3. Add a card for it to the works grid in `index.html`, and fix the Previous / Next links of its neighbours.
4. Add the new URL to `sitemap.xml`.

## Media

- Images: `cwebp -q 88 in.png -o out.webp`, thumbnails at about 800 px wide and `-q 82`.
- Videos: `ffmpeg -i in.mp4 -c:v libx264 -crf 23 -preset medium -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart out.mp4`
- Keep single files well under 50 MB; GitHub rejects files over 100 MB.

## Custom domain

The `CNAME` file holds the custom domain (`jichu.art`). DNS: `@` A records point at GitHub Pages, `www` is a CNAME to `jichumao.github.io`. HTTPS is enforced in Settings → Pages.
