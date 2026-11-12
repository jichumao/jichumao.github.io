import asyncio, sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox", "--allow-file-access-from-files"])
        for spec in sys.argv[1:]:
            path, out, w, h, scale = spec.split("|")
            ctx = await b.new_context(viewport={"width": int(w), "height": int(h)}, device_scale_factor=float(scale)); pg = await ctx.new_page()
            await pg.goto("file://" + path); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
            await pg.screenshot(path=out); await ctx.close()
        await b.close()
asyncio.run(main())
