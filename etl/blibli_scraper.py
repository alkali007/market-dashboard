import asyncio
import os
import json
import random
import urllib.parse
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETL_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
COOKIES_PATH = os.path.join(ETL_DIR, "cookies_blibli.json")
RAW_OUTPUT_PATH = os.path.join(DATA_DIR, "raw", "blibli_raw.json")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# Example Keywords
KEYWORDS = [
    "skincare", 
    "moisturizer", 
    "sunscreen", 
    "serum wajah"
]

async def run_scraper():
    keyword = random.choice(KEYWORDS)
    print(f"Target selected: {keyword.upper()}")
    
    async with async_playwright() as p:
        # Launch browser (Headful for debugging/initial setup)
        browser = await p.chromium.launch(
            headless=False,
            channel="chrome", # Use real Chrome for better stealth
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        context = await browser.new_context(
            user_agent=USER_AGENT, 
            viewport={"width": 1366, "height": 768}
        )
        
        page = await context.new_page()
        
        # Apply Stealth
        await Stealth().apply_stealth_async(page)
        
        try:
            print("Navigating to Blibli.com...")
            await page.goto("https://www.blibli.com", wait_until="domcontentloaded", timeout=60000)
            
            # Wait for random time
            await asyncio.sleep(random.uniform(3, 7))
            
            # Search Navigation
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://www.blibli.com/cari/{encoded_keyword}"
            
            print(f"Navigating to search results: {search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(5, 10))
            
            # TODO: Implement specific data extraction logic here
            # For now, just screenshot to verify
            screenshot_path = os.path.join(DATA_DIR, "screenshots", "blibli_test.png")
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")
            
            # Save Cookies (if needed for future runs)
            cookies = await context.cookies()
            with open(COOKIES_PATH, "w") as f:
                json.dump(cookies, f, indent=4)
            print("Cookies saved.")

        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
