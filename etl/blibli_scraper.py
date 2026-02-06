import asyncio
import os
import json
import random
import urllib.parse
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- CONFIGURATION ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
COOKIES_PATH = os.path.join(DATA_DIR, "cookies_blibli.json")
RAW_OUTPUT_PATH = os.path.join(DATA_DIR, "raw", "blibli_raw.json")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
CONCURRENCY_LIMIT = 3
sem = asyncio.Semaphore(CONCURRENCY_LIMIT)

KEYWORDS = ["skincare", "moisturizer", "sunscreen", "serum wajah"]

async def fetch_page(context, keyword, page_num, user_id):
    """Fetch using Page Navigation + Network Interception (Bypassing API 403)."""
    async with sem:
        page = await context.new_page()
        # Apply Stealth to the visual page
        await Stealth().apply_stealth_async(page)
        
        items = []
        
        # Calculate 'start' parameter based on user observation
        # Page 1 -> 0
        # Page 2 -> 36 (Outlier)
        # Page 3 -> 80 (Standard 40/page)
        # Page 20 -> 760 ((20-1)*40)
        
        if page_num == 1:
            start_index = 0
        elif page_num == 2:
            start_index = 36
        else:
            start_index = (page_num - 1) * 40
            
        async def handle_response(response):
            nonlocal items
            # Intercept the Backend Search API
            if "/backend/search/products" in response.url and response.status == 200:
                try:
                    data = await response.json()
                    new_items = data.get("data", {}).get("products", [])
                    if new_items:
                        items = new_items
                        print(f"Page {page_num} (start={start_index}): Intercepted {len(new_items)} items.")
                except:
                    pass

        page.on("response", handle_response)
        
        # Frontend URL (The visual page the user sees)
        encoded_kw = urllib.parse.quote(keyword)
        # Explicitly pass 'start' to ensure frontend loads the correct chunk
        frontend_url = f"https://www.blibli.com/cari/{encoded_kw}?page={page_num}&start={start_index}&sort=0"
        
        try:
            # Navigation & Retry Logic
            for attempt in range(2):
                if attempt == 0:
                    print(f"Page {page_num}: Navigating to {frontend_url}...")
                    await page.goto(frontend_url, wait_until="domcontentloaded", timeout=60000)
                else:
                    print(f"Page {page_num}: Retrying with reload...")
                    await page.reload(wait_until="domcontentloaded")
                
                # Initial stability wait (Give page time to execute JS)
                await asyncio.sleep(5)

                # HANDLE POPUP: "Nanti saja"
                try:
                    popup_btn = page.get_by_text("Nanti saja", exact=False)
                    if await popup_btn.count() > 0 and await popup_btn.is_visible():
                        print(f"Page {page_num}: Closing popup...")
                        await popup_btn.first.click()
                        await asyncio.sleep(2)
                except:
                    pass
                
                # Wait for interception or simple timeout
                retry_scroll = 0
                max_scrolls = 8
                while not items and retry_scroll < max_scrolls:
                    # Gentle scroll
                    await page.mouse.wheel(0, 150) 
                    await asyncio.sleep(3) # Wait longer between scrolls
                    retry_scroll += 1
                
                if items:
                    break # Success!
            
            # Debug Screenshot if capture failed
            if not items:
                print(f"Page {page_num}: No items intercepted. Taking debug screenshot...")
                screenshot_dir = os.path.join(DATA_DIR, "screenshots")
                os.makedirs(screenshot_dir, exist_ok=True)
                screenshot_path = os.path.join(screenshot_dir, f"blibli_fail_page_{page_num}.png")
                await page.screenshot(path=screenshot_path)
                print(f"Page {page_num}: Saved screenshot to {screenshot_path}")
                
            return items
            
        except Exception as e:
            print(f"Page {page_num}: Error - {e}")
            return []
        finally:
            await page.close()

async def run_scraper():
    keyword = random.choice(KEYWORDS)
    print(f"Target selected: {keyword.upper()}")
    num_pages = 10
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, # Headless is fine if cookies are good
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent=USER_AGENT, 
            viewport={"width": 1366, "height": 768}
        )
        
        user_id = "unknown"
        
        # Load Cookies
        if os.path.exists(COOKIES_PATH):
            try:
                with open(COOKIES_PATH, "r") as f:
                    cookies = json.load(f)
                    await context.add_cookies(cookies)
                    
                    # Extract User ID from cookies (__bwa_user_id)
                    for c in cookies:
                        if c['name'] == '__bwa_user_id':
                            user_id = c['value']
                            break
                            
                print(f"Loaded cookies from {COOKIES_PATH}")
                print(f"Using extracted User ID: {user_id}")
            except Exception as e:
                print(f"Cookie load error: {e}")
        else:
            print("WARNING: No cookies found! Captcha is likely.")

        print(f"Starting API scrape for {keyword}...")
        tasks = [fetch_page(context, keyword, i, user_id) for i in range(1, num_pages + 1)]
        results = await asyncio.gather(*tasks)
        
        all_items = []
        for res in results:
            if res: all_items.extend(res)
            
        # Save
        os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)
        with open(RAW_OUTPUT_PATH, "w", encoding='utf-8') as f:
            json.dump({"items": all_items, "total": len(all_items)}, f, indent=4, ensure_ascii=False)
            
        print(f"[SUCCESS] Saved {len(all_items)} items to {RAW_OUTPUT_PATH}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
