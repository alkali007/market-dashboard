import asyncio
import os
import json
from playwright.async_api import async_playwright

# --- CONFIGURATION ---
ETL_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_PATH = os.path.join(ETL_DIR, "chrome_profile")
COOKIES_OUTPUT_PATH = os.path.join(ETL_DIR, "cookies_lazada.json")

async def main():
    print(f"Launching Chrome Profile from: {PROFILE_PATH}")
    print("---------------------------------------------------------")
    print("INSTRUCTIONS:")
    print("1. Browser will open with your profile.")
    print("2. Navigate to lazada.co.id.")
    print("3. Check if you are logged in. If banned, try to resolve it or login to a new account.")
    print("4. Once the session is VALID, simply CLOSE the browser window.")
    print("---------------------------------------------------------")

    async with async_playwright() as p:
        # Launch persistent context
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1366, "height": 768}
        )
        
        page = await context.new_page()
        await page.goto("https://www.lazada.co.id")
        
        # Wait until browser is closed
        try:
            # Monitor for close event implicitly by waiting indefinitely
            # When user closes browser, this context manager exits or throws
            while context.pages:
                await asyncio.sleep(1)
        except Exception:
            pass
        
        print("\nBrowser closed. Extracting cookies...")
        
        # Extract cookies from the now-closed context (might fail if fully detached)
        # Actually in Playwright persistent context, we should grab cookies BEFORE it fully dies or rely on context not being fully destroyed yet?
        # Better approach: We grab cookies right before exit or rely on the user to press Enter in terminal?
        pass

    # Alternative: Re-launch briefly or grab during the session loop?
    # Let's try a safer pattern: infinite loop that saves cookies every 5 seconds until exit.
    
async def robust_main():
    print(f"Launching Chrome Profile from: {PROFILE_PATH}")
    print("... Saving cookies to 'cookies_lazada.json' every 5 seconds ...")
    print("Press Ctrl+C in terminal to stop when you are done.")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1366, "height": 768}
        )
        
        if not context.pages:
            await context.new_page()
            
        try:
            while True:
                cookies = await context.cookies()
                with open(COOKIES_OUTPUT_PATH, "w") as f:
                    json.dump(cookies, f, indent=4)
                print(f"Saved {len(cookies)} cookies...", end="\r")
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            print("\nStopped by user.")
        except Exception as e:
            print(f"\nBrowser closed or error: {e}")
        finally:
            await context.close()
            print(f"\n[SUCCESS] Final cookies saved to: {COOKIES_OUTPUT_PATH}")

if __name__ == "__main__":
    asyncio.run(robust_main())
