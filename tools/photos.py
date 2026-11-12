"""Prepares photographs for the photography section.

    python3 tools/photos.py 401 ~/Pictures/DSC01234.jpg 402 ~/Pictures/DSC01240.jpg

For each pair (a number you choose, then the source file) it writes
photography/img/NNN-2400.webp, NNN-1400.webp and NNN-700.webp (long side in
pixels, never enlarged) and records the photograph in tools/photos.json.
Colours are converted to sRGB. Nothing from the file's metadata is copied
into the output, so GPS position, serial numbers and dates stay private;
only focal length, aperture, shutter speed and ISO are kept, as the caption
in the viewer.

Needs Pillow:  pip install pillow
"""
import io, json, os, sys
from PIL import Image, ImageCms, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "photography", "img")
DATA = os.path.join(ROOT, "tools", "photos.json")
QUALITY = {2400: 88, 1400: 86, 700: 82}


def to_srgb(im):
    icc = im.info.get("icc_profile")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            im = ImageCms.profileToProfile(im, src, ImageCms.createProfile("sRGB"), outputMode="RGB")
        except Exception:
            pass
    return im.convert("RGB")


def settings(im):
    ex = im.getexif()
    sub = ex.get_ifd(0x8769) if ex else {}
    focal, fnum, exp, iso = sub.get(0x920A), sub.get(0x829D), sub.get(0x829A), sub.get(0x8827)
    if not (focal and fnum and exp and iso):
        return ""
    num = lambda x: x[0] / x[1] if isinstance(x, tuple) else float(x)
    exp = num(exp)
    shutter = f"1/{round(1 / exp)} s" if 0 < exp < 1 else f"{exp:g} s"
    iso = iso[0] if isinstance(iso, tuple) else iso
    return f"{num(focal):.0f} mm, f/{num(fnum):g}, {shutter}, ISO {int(iso)}"


def add(n, path, photos):
    src = Image.open(path)
    caption = settings(src)
    im = to_srgb(ImageOps.exif_transpose(src))
    long = max(im.size)
    files = []
    for size in (700, 1400, 2400):
        if size == 1400 and long <= 1400:
            continue
        s = min(1, size / long)
        out = im if s == 1 else im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        out.save(os.path.join(IMG, f"{n:03d}-{size}.webp"), "WEBP", quality=QUALITY[size], method=6)
        files.append([size, out.width])
        big = out
    r, g, b = im.resize((1, 1), Image.BOX).getpixel((0, 0))
    photos[f"{n:03d}"] = {"w": big.width, "h": big.height, "files": files, "settings": caption,
                          "color": "#%02x%02x%02x" % (int(r * .55), int(g * .55), int(b * .55))}
    print(f"{n:03d}  {big.width}x{big.height}  {caption or 'no camera settings in the file'}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or len(args) % 2:
        sys.exit(__doc__)
    os.makedirs(IMG, exist_ok=True)
    photos = json.load(open(DATA, encoding="utf-8")) if os.path.exists(DATA) else {}
    for n, path in zip(args[::2], args[1::2]):
        add(int(n), os.path.expanduser(path), photos)
    with open(DATA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(photos, f, indent=1, sort_keys=True)
        f.write("\n")
