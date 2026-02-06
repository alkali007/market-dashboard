import asyncio
import os
import json
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
COOKIES_PATH = os.path.join(DATA_DIR, "cookies_blibli.json")

async def main():
    print(f"Launching Chrome for Blibli Cookie Extraction...")
    print("---------------------------------------------------------")
    print("1. Browser will open.")
    print("2. Navigate to https://www.blibli.com")
    print("3. Solve any CAPTCHAs manually.")
    print("4. Verify you can search for products.")
    print("5. Once done, CLOSE the browser window or Press Ctrl+C.")
    print("---------------------------------------------------------")

    async with async_playwright() as p:
        # Launch persistent context
        browser = await p.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(viewport={"width": 1366, "height": 768})
        page = await context.new_page()
        
        # Load existing if available (to resume session)
        if os.path.exists(COOKIES_PATH):
            try:
                with open(COOKIES_PATH, "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
                print("Loaded existing cookies.")
            except:
                pass

        await page.goto("https://www.blibli.com")
        
        try:
            while True:
                cookies = await context.cookies()
                with open(COOKIES_PATH, "w") as f:
                    json.dump(cookies, f, indent=4)
                print(f"Saved {len(cookies)} cookies...", end="\r")
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\nStopped by user.")
        except Exception as e:
            print(f"\nBrowser closed or error: {e}")
        finally:
            await browser.close()
            print(f"\n[SUCCESS] Final cookies saved to: {COOKIES_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
