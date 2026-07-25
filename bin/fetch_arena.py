import asyncio
import os
import sys

# Ensure Playwright is available in the local virtual environment
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("FATAL: Playwright is not installed in the current environment.")
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

async def main():
    """
    Spawns a headless Chromium instance to navigate to LMArena and extract
    the fully rendered DOM. This allows us to inspect the highly obfuscated
    Gradio UI structure to locate the exact XPaths for the Domain/Variant/Category dropdowns.
    """
    url = "https://arena.ai/leaderboard"
    out_dir = "tmp"
    out_file = os.path.join(out_dir, "arena_dom.html")

    os.makedirs(out_dir, exist_ok=True)

    print(f"Launching headless Chromium to fetch {url}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # We use networkidle to ensure all Gradio React components and API calls finish rendering
            await page.goto(url, wait_until="networkidle", timeout=60000)
            print("Page successfully loaded and settled.")

            # Extract the raw, fully hydrated HTML string
            content = await page.content()

            with open(out_file, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"\nSUCCESS: Fully rendered DOM saved to {out_file}")
            print("You can now grep this file to identify the specific class names and nested divs used for the Category filters.")

        except Exception as e:
            print(f"ERROR: Failed to load or extract DOM: {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
