"""Prints the résumé page (resume/index.html, written by tools/build.py) to the PDF the site links to.

    python3 tools/build.py . tools/manifest.json
    python3 tools/resume.py .

Needs Chrome, Chromium or Edge installed; it is run without a window. The same PDF can be made
by hand: open resume/index.html in a browser, print, choose "Save as PDF", US Letter, no headers
and footers, and save it as assets/Jichu-Mao-Resume.pdf.

To use a résumé you wrote yourself, just replace assets/Jichu-Mao-Resume.pdf and do not run this.
"""
import os, pathlib, shutil, subprocess, sys, tempfile

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
OUT = os.path.join(ROOT, "assets", "Jichu-Mao-Resume.pdf")
NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge", "chrome"]
PLACES = [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
          r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]

browser = next((shutil.which(n) for n in NAMES if shutil.which(n)), None) or next((p for p in PLACES if os.path.exists(p)), None)
if not browser:
    sys.exit("No Chrome, Chromium or Edge found. Print resume/index.html to PDF by hand instead (see the top of this file).")
page = pathlib.Path(ROOT, "resume", "index.html").as_uri()
with tempfile.TemporaryDirectory() as profile:
    subprocess.run([browser, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={profile}", "--no-pdf-header-footer",
                    "--virtual-time-budget=4000", f"--print-to-pdf={OUT}", page], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("wrote", os.path.relpath(OUT, ROOT), round(os.path.getsize(OUT) / 1024), "KB")
