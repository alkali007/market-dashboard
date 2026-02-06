import os
import json
import asyncio
from playwright.async_api import async_playwright
import random
import time
import urllib.parse

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETL_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
COOKIES_PATH = os.path.join(ETL_DIR, "cookies_lazada.json")
RAW_OUTPUT_PATH = os.path.join(DATA_DIR, "raw", "lazada_raw.json")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

async def capture_cookies():
    """Initial landing to capture cookies."""
    url = "https://www.lazada.co.id"
    os.makedirs(DATA_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        # Launching with headless=False to allow manual verification if needed, 
        # but setting it to True for automation once verified.
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        page = await context.new_page()
        
        print(f"Navigating to {url} to capture cookies...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(5) # Wait for anti-bot JS to settle
            
            cookies = await context.cookies()
            with open(COOKIES_PATH, "w") as f:
                json.dump(cookies, f, indent=4)
            print(f"[SUCCESS] Cookies captured and saved to {COOKIES_PATH}")
            return cookies
        except Exception as e:
            print(f"[ERROR] Failed to capture cookies: {e}")
            return None
        finally:
            await browser.close()

async def fetch_page(context, keyword, page_num):
    """Fetch a single page using direct request."""
    # Base URL can be /catalog/ or /tag/ depending on Lazada's preference
    # We use /catalog/ as the primary entry point
    url = f"https://www.lazada.co.id/catalog/"
    
    params = {
        "_keyori": "ss",
        "ajax": "true",
        "catalog_redirect_tag": "true",
        "from": "search_history",
        "page": str(page_num),
        "q": keyword,
        "spm": "a2o4j.homepage.search.2.57991e98tK06F3"
    }
    
    headers = {
        "referer": "https://www.lazada.co.id/",
        "x-requested-with": "XMLHttpRequest"
    }

    try:
        # Use context.request for direct API call
        print(f"Fetching page {page_num}...")
        response = await context.request.get(url, params=params, headers=headers)
        
        # If redirect happens or it fails, try the /tag/ variant
        if response.status != 200:
            tag_url = f"https://www.lazada.co.id/tag/{urllib.parse.quote(keyword)}/"
            print(f"Page {page_num} failed with {response.status}, trying tag URL: {tag_url}")
            response = await context.request.get(tag_url, params=params, headers=headers)

        if response.status == 200:
            data = await response.json()
            # Lazada items are usually in mods -> listItems
            items = data.get("mods", {}).get("listItems", [])
            print(f"Page {page_num}: Found {len(items)} items.")
            return items
        else:
            print(f"Page {page_num}: Failed with status {response.status}")
            return []
    except Exception as e:
        print(f"Page {page_num}: Error - {e}")
        return []

async def run_scraper():
    # 1. Capture cookies first
    cookies = await capture_cookies()
    if not cookies:
        if os.path.exists(COOKIES_PATH):
            with open(COOKIES_PATH, "r") as f:
                cookies = json.load(f)
        else:
            print("No cookies available. Exiting.")
            return

    keyword = "skincare"
    num_pages = 30 # User requested 30 concurrent
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=USER_AGENT)
        await context.add_cookies(cookies)
        
        print(f"Starting concurrent scrape of {num_pages} pages for '{keyword}'...")
        tasks = [fetch_page(context, keyword, i) for i in range(1, num_pages + 1)]
        results = await asyncio.gather(*tasks)
        
        all_items = []
        for items in results:
            all_items.extend(items)
            
        # 5. Save Results
        os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)
        with open(RAW_OUTPUT_PATH, "w", encoding='utf-8') as f:
            json.dump({"items": all_items, "total": len(all_items)}, f, indent=4, ensure_ascii=False)
            
        print(f"\n[SUCCESS] Captured total {len(all_items)} unique items from Lazada.")
        print(f"File saved to: {RAW_OUTPUT_PATH}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
