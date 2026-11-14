"""Prepares photographs for the photography section.

    python3 tools/photos.py 401 ~/Pictures/DSC01234.jpg 402 ~/Pictures/DSC01240.jpg

For each pair (a number you choose, then the source file) it writes
photography/img/NNN-2400.webp, NNN-1400.webp and NNN-700.webp (long side in
pixels, never enlarged) and records the photograph in tools/photos.json.
Colours are converted to sRGB. Nothing from the file's metadata is copied
into the output, so GPS position, serial numbers and dates stay private;
only focal length, aperture, shutter speed and ISO are kept, as the caption
in the viewer. Each output file is then tagged with the author and a rights
statement (XMP, invisible, see STAMP below).

    python3 tools/photos.py --stamp     tags every file in photography/img again
                                        (safe to repeat; the picture data is not touched)

    python3 tools/photos.py --project virtual-subway 391:interior 398:side
                                        reuses published photographs as the images of a project page:
                                        writes assets/img/<project>/<name>.webp and -thumb.webp
                                        and records them in tools/manifest.json

Needs Pillow:  pip install pillow
"""
import hashlib, glob, io, json, os, shutil, struct, sys
from PIL import Image, ImageCms, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "photography", "img")
DATA = os.path.join(ROOT, "tools", "photos.json")
QUALITY = {2400: 82, 1400: 80, 700: 78}

# What is written into every published file. Search engines and photo software read these fields.
AUTHOR = "Jichu Mao"
RIGHTS = "© Jichu Mao. All rights reserved."
STATEMENT = "https://jichu.art/photography/"
# Photograph numbers that must not carry the author tag (pictures someone else took, for example).
UNTAGGED = set()
STAMP = f'''<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/"
    xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
    xmpRights:Marked="True"
    xmpRights:WebStatement="{STATEMENT}"
    photoshop:Credit="{AUTHOR}">
   <dc:creator><rdf:Seq><rdf:li>{AUTHOR}</rdf:li></rdf:Seq></dc:creator>
   <dc:rights><rdf:Alt><rdf:li xml:lang="x-default">{RIGHTS}</rdf:li></rdf:Alt></dc:rights>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>'''.encode("utf-8")


def chunk(tag, data):
    return tag + struct.pack("<I", len(data)) + data + (b"\0" if len(data) % 2 else b"")


def stamp(path):
    """Adds the STAMP packet to a WebP file by rewriting its container only; the compressed picture is copied as is."""
    raw = open(path, "rb").read()
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WEBP", path
    parts, i = [], 12
    while i + 8 <= len(raw):
        tag, size = raw[i:i + 4], struct.unpack("<I", raw[i + 4:i + 8])[0]
        parts.append((tag, raw[i + 8:i + 8 + size])); i += 8 + size + size % 2
    parts = [(t, d) for t, d in parts if t != b"XMP "]
    if parts[0][0] == b"VP8X":
        head = bytearray(parts[0][1]); head[0] |= 0x04; parts[0] = (b"VP8X", bytes(head))
    else:
        w, h = Image.open(path).size
        alpha = 0x10 if parts[0][0] == b"VP8L" and Image.open(path).mode == "RGBA" else 0
        head = bytes([0x04 | alpha, 0, 0, 0]) + struct.pack("<I", w - 1)[:3] + struct.pack("<I", h - 1)[:3]
        parts.insert(0, (b"VP8X", head))
    body = b"WEBP" + b"".join(chunk(t, d) for t, d in parts) + chunk(b"XMP ", STAMP)
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", len(body)) + body)


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
        if n not in UNTAGGED:
            stamp(os.path.join(IMG, f"{n:03d}-{size}.webp"))
        files.append([size, out.width])
        big = out
    r, g, b = im.resize((1, 1), Image.BOX).getpixel((0, 0))
    # v: a short hash of the largest file. The pages add it to this photograph's URLs (…-2400.webp?v=…), so a photograph
    # exported again under the same number is fetched anew instead of being served from the CDN's 30-day image cache.
    v = hashlib.sha1(open(os.path.join(IMG, f"{n:03d}-{max(w for w, _ in files)}.webp"), "rb").read()).hexdigest()[:8]
    photos[f"{n:03d}"] = {"w": big.width, "h": big.height, "files": files, "settings": caption, "v": v,
                          "color": "#%02x%02x%02x" % (int(r * .55), int(g * .55), int(b * .55))}
    print(f"{n:03d}  {big.width}x{big.height}  {caption or 'no camera settings in the file'}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--stamp"]:
        files = [f for f in sorted(glob.glob(os.path.join(IMG, "*.webp"))) if int(os.path.basename(f)[:3]) not in UNTAGGED]
        for f in files:
            stamp(f)
        sys.exit(f"tagged {len(files)} files")
    if args[:1] == ["--project"]:
        # Reuse published photographs as images of a project page on the main site:
        #   python3 tools/photos.py --project virtual-subway 391:interior 398:side …
        # Copies the largest file as assets/img/<project>/<name>.webp, writes an 800px -thumb, and records both in tools/manifest.json.
        proj, pairs = args[1], [a.split(":") for a in args[2:]]
        manp = os.path.join(ROOT, "tools", "manifest.json")
        man = json.load(open(manp, encoding="utf-8"))
        photos = json.load(open(DATA, encoding="utf-8"))
        dst = os.path.join(ROOT, "assets", "img", proj)
        os.makedirs(dst, exist_ok=True)
        for n, name in pairs:
            n = int(n)
            big = max(size for size, _ in photos[f"{n:03d}"]["files"])
            full = os.path.join(dst, name + ".webp")
            shutil.copyfile(os.path.join(IMG, f"{n:03d}-{big}.webp"), full)
            im = Image.open(full).convert("RGB")
            th = im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS)
            th.save(os.path.join(dst, name + "-thumb.webp"), "WEBP", quality=80, method=6)
            if n not in UNTAGGED:
                stamp(os.path.join(dst, name + "-thumb.webp"))
            man[f"{proj}/{name}"] = {"w": im.width, "h": im.height, "tw": th.width, "th": th.height, "alpha": False}
            print(f"{proj}/{name}  {im.width}x{im.height}")
        with open(manp, "w", encoding="utf-8") as f:
            json.dump(man, f, indent=1, sort_keys=True)
        sys.exit(0)
    if not args or len(args) % 2:
        sys.exit(__doc__)
    os.makedirs(IMG, exist_ok=True)
    photos = json.load(open(DATA, encoding="utf-8")) if os.path.exists(DATA) else {}
    for n, path in zip(args[::2], args[1::2]):
        add(int(n), os.path.expanduser(path), photos)
    with open(DATA, "w", encoding="utf-8", newline="\n") as f:
        json.dump(photos, f, indent=1, sort_keys=True)
        f.write("\n")
