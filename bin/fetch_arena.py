import asyncio
import os
import sys
import re
import json

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("FATAL: Playwright is not installed in the current environment.")
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

async def main():
    """
    Spawns a headless Chromium instance to navigate to LMArena and extract
    the fully rendered DOM. It parses the script tags to locate the embedded
    Gradio state JSON, dumping the raw data for triplet extraction.
    """
    url = "https://arena.ai/leaderboard"

    print(f"Launching headless Chromium to fetch {url}...", file=sys.stderr)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # We use networkidle to ensure all Gradio React components and API calls finish rendering
            await page.goto(url, wait_until="networkidle", timeout=60000)
            print("Page successfully loaded and settled.", file=sys.stderr)

            content = await page.content()

            # Parse all <script> tags for the Gradio data payload
            script_pattern = re.compile(r'<script[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)
            scripts = script_pattern.findall(content)

            found_data = False
            for s in scripts:
                # Target the specific Gradio state push array
                m = re.match(r'^\s*self\.__f\.push\((?P<json>.*)\)\s*$', s, re.DOTALL)
                if m:
                    try:
                        j = json.loads(m.group('json'))
                        # Output the clean JSON to stdout for piping/saving
                        json.dump(j, sys.stdout, indent=2, sort_keys=True)
                        print("\n", file=sys.stdout)
                        found_data = True
                    except json.JSONDecodeError as e:
                        print(f"Warning: Regex matched but JSON parsing failed: {e}", file=sys.stderr)

            if not found_data:
                print("WARNING: Could not find any script tags matching 'self.__f.push(...)'. The page structure may have changed.", file=sys.stderr)

        except Exception as e:
            print(f"ERROR: Failed to load or extract DOM: {e}", file=sys.stderr)

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
