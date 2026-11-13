# Brand icons

Empty on purpose. While it is empty, links to GitHub, YouTube, LinkedIn and Bilibili show plain line icons.

To show a service's own icon, download its official SVG from the service's brand page and save it here, unchanged, under one of these names:

| File | Used for links to | Official source |
| --- | --- | --- |
| `github.svg` | github.com | https://github.com/logos |
| `youtube.svg` | youtube.com | https://www.youtube.com/howyoutubeworks/resources/brand-resources/ |
| `linkedin.svg` | linkedin.com | https://brand.linkedin.com/downloads |
| `bilibili.svg` | bilibili.com | Bilibili's own brand materials |

Then rebuild: `python3 tools/build.py . tools/manifest.json`. The file is shown as it is, 18 px high, so pick the version meant for dark backgrounds (the page is black). Each brand has its own rules of use; read them on the pages above before publishing.
