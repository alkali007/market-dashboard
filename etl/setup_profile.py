import asyncio
import os
from playwright.async_api import async_playwright

# Define the persistent profile path
PROFILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")

async def setup_profile():
    print(f"Launching Chrome with persistent profile at: {PROFILE_PATH}")
    print("---------------------------------------------------------")
    print("INSTRUCTIONS:")
    print("1. The browser will open.")
    print("2. Log in to your GOOGLE ACCOUNT (gmail.com). This provides ReCAPTCHA trust.")
    print("3. Log in to LAZADA (lazada.co.id).")
    print("4. Solve any CAPTCHAs you see manually.")
    print("5. Once you are fully logged in and can browse Lazada freely, CLOSE the browser manually.")
    print("---------------------------------------------------------")
    
    async with async_playwright() as p:
        # Launch persistent context
        # We use a distinct user data dir to store cookies/sessions/auth tokens
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=False,
            channel="chrome", # Use real Chrome
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1366, "height": 768}
        )
        
        page = await context.new_page()
        await page.goto("https://accounts.google.com")
        
        # Keep script running until user closes browser
        try:
            # Wait indefinitely until the browser context is closed by the user
            await page.wait_for_timeout(9999999) 
        except Exception:
            print("Browser closed. Profile setup complete.")

if __name__ == "__main__":
    asyncio.run(setup_profile())
