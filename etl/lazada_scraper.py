import os
import json
import asyncio
import random
import time
import urllib.parse
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETL_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
COOKIES_PATH = os.path.join(ETL_DIR, "cookies_lazada.json")
RAW_OUTPUT_PATH = os.path.join(DATA_DIR, "raw", "lazada_raw.json")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
CONCURRENCY_LIMIT = 3 
sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

# --- UTILS ---
async def human_jitter(page, duration: int):
    """Micro mouse movements to simulate human presence."""
    steps = int(duration / 0.5)
    for _ in range(steps):
        try:
            x, y = random.randint(-10, 10), random.randint(-10, 10)
            viewport = page.viewport_size
            if viewport:
                center_x, center_y = viewport['width'] / 2, viewport['height'] / 2
                await page.mouse.move(center_x + x, center_y + y)
            await asyncio.sleep(0.5)
        except:
            break

async def apply_high_stealth(page):
    """Apply TikTok-style high-level stealth including CDP client hints."""
    await Stealth().apply_stealth_async(page)
    client = await page.context.new_cdp_session(page)
    await client.send('Network.setUserAgentOverride', {
        "userAgent": USER_AGENT,
        "platform": "Windows",
        "userAgentMetadata": {
            "brands": [
                {"brand": "Not(A:Brand", "version": "8"},
                {"brand": "Chromium", "version": "144"},
                {"brand": "Google Chrome", "version": "144"}
            ],
            "fullVersionList": [
                {"brand": "Not(A:Brand", "version": "8.0.0.0"},
                {"brand": "Chromium", "version": "144.0.0.0"},
                {"brand": "Google Chrome", "version": "144.0.0.0"}
            ],
            "platform": "Windows",
            "platformVersion": "10.0.0",
            "architecture": "x86",
            "model": "",
            "mobile": False
        }
    })

# --- CORE LOGIC ---
async def fetch_page(browser_context, keyword, page_num):
    """Fetch a single page with catalog -> tag fallback logic."""
    async with sem:
        page = await browser_context.new_page()
        await apply_high_stealth(page)
        
        items = []
        async def handle_response(response):
            nonlocal items
            if "ajax=true" in response.url:
                try:
                    if response.status == 200:
                        data = await response.json()
                        new_items = data.get("mods", {}).get("listItems", [])
                        if new_items:
                            items = new_items
                            print(f"Page {page_num}: Intercepted {len(new_items)} items.")
                except:
                    pass

        page.on("response", handle_response)
        
        # Prepare URLs
        encoded_q = urllib.parse.quote(keyword)
        spm = "a2o4j.homepage.search.d_go"
        catalog_url = f"https://www.lazada.co.id/catalog/?page={page_num}&q={encoded_q}&spm={spm}"
        tag_url = f"https://www.lazada.co.id/tag/{encoded_q}/?page={page_num}&q={encoded_q}&spm={spm}&catalog_redirect_tag=true"
        
        try:
            print(f"Page {page_num}: Accessing Catalog...")
            # SLOWER: Simulate real human reading/browsing time before clicking next page
            await asyncio.sleep(random.uniform(10, 20))
            
            # 1. Try Catalog (Lazada might auto-redirect or serve search results)
            await page.goto(catalog_url, wait_until="domcontentloaded", timeout=60000)
            await human_jitter(page, random.randint(8, 15))
            
            # 2. If no items intercepted, try Tag explicitly
            if not items:
                print(f"Page {page_num}: Empty on Catalog, trying Tag variant...")
                await asyncio.sleep(random.uniform(5, 8)) # Wait before redirecting
                await page.goto(tag_url, wait_until="domcontentloaded", timeout=60000)
                await human_jitter(page, random.randint(8, 12))
            
            # 3. Last ditch effort: Scroll to trigger lazy-load API
            if not items:
                print(f"Page {page_num}: Still empty, scrolling to trigger lazy API...")
                await page.evaluate("window.scrollTo(0, 800);")
                await asyncio.sleep(random.uniform(5, 10))
            
            return items
        except Exception as e:
            print(f"Page {page_num}: Failed -> {e}")
            return []
        finally:
            await page.close()

# --- TARGETING ---
KEYWORDS = [
    "skincare", "moisturizer", "sunscreen", "serum wajah", 
    "facial wash", "toner wajah", "eye cream", "masker wajah"
]

# --- CONFIGURATION ---
PROFILE_PATH = os.path.join(ETL_DIR, "chrome_profile")

async def run_scraper():
    keyword = random.choice(KEYWORDS)
    print(f"Target selected: {keyword.upper()}")
    num_pages = 10 
    
    async with async_playwright() as p:
        print(f"Launching scraper with persistent profile: {PROFILE_PATH}")
        
        # Launch persistent context (No browser.close() - context close handles it)
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_PATH,
            headless=True, # Must be False to use the profile effectively usually, or True if profile is very strong
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1366, "height": 768}
        )
        
        # Note: Persistence handles cookies automatically, no need to manual load/save unless backup needed.
        
        # 2. CONCURRENT SCRAPING
        print(f"Starting controlled scrape (Concurrency: {CONCURRENCY_LIMIT})...")
        tasks = [fetch_page(context, keyword, i) for i in range(1, num_pages + 1)]
        results = await asyncio.gather(*tasks)
        
        all_items = []
        for items in results:
            if items: all_items.extend(items)
            
        # 3. SAVE RESULTS
        os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)
        with open(RAW_OUTPUT_PATH, "w", encoding='utf-8') as f:
            json.dump({"items": all_items, "total": len(all_items)}, f, indent=4, ensure_ascii=False)
            
        print(f"\n[SUCCESS] Captured total {len(all_items)} products.")
        print(f"File: {RAW_OUTPUT_PATH}")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
