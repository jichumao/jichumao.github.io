import asyncio, json, sys
from playwright.async_api import async_playwright
ARGS = ["--no-sandbox", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--enable-webgl"]
LOOKS = json.load(open(sys.argv[1])); OUT = sys.argv[2]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=ARGS)
        pg = await (await b.new_context(viewport={"width": 1300, "height": 1300}, device_scale_factor=2)).new_page()
        errs = []; pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None); pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("http://localhost:8770/index.html")
        for name, look in LOOKS.items():
            try:
                r = await pg.evaluate("o => window.render(o)", look)
                await pg.locator("#c").screenshot(path=f"{OUT}/{name}.png"); print(name, r)
            except Exception as e:
                print(name, "FAILED", str(e)[:400])
        print("errors", errs[:3]); await b.close()
asyncio.run(main())
