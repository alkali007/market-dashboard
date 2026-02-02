import os
import json
import time
import random
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

# Global Configuration
MAX_LOOPS = 5
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# URLs provided in step 1
URLS = {
    "beauty": "https://shop-id.tokopedia.com/c/beauty-personal-care/601450"
}

def clean_price(text):
    """Helper to remove non-numeric chars for storage if needed"""
    return text.replace("Rp", "").replace(".", "").strip()

def save_raw_data(category_name, new_data):
    """
    ETL EXTRACT: Saves raw scraped data to JSON.
    """
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    save_dir = os.path.join(project_root, "data", "raw")
    os.makedirs(save_dir, exist_ok=True)
    filename = os.path.join(save_dir, f"{category_name}_raw.json")
    
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)
    
    print(f"[{category_name}] EXTRACT: Saved {len(new_data)} raw items to {filename}")

async def scroll_to_bottom_human(page):
    """
    Scrolls down the page in random steps with variable pauses 
    to mimic human behavior and trigger lazy-loaded elements.
    """
    print("Starting human-like scroll...")
    
    # Get total page height
    total_height = await page.evaluate("document.body.scrollHeight")
    current_position = 0
    
    while current_position < total_height:
        # 1. Randomize scroll step (between 300px and 700px)
        step = random.randint(300, 700)
        
        # 2. Calculate new position
        current_position += step
        
        # 3. Apply scroll command
        await page.evaluate(f"window.scrollTo(0, {current_position});")
        
        # 4. Random Wait (0.5s to 1.2s) - Mimics looking at products
        await asyncio.sleep(random.uniform(0.5, 1.2))
        
        # 5. Occasional "Scroll Up" (10% chance) - Mimics checking previous item
        if random.random() < 0.1:
            scroll_up = random.randint(100, 300)
            current_position -= scroll_up
            await page.evaluate(f"window.scrollTo(0, {current_position});")
            await asyncio.sleep(random.uniform(0.5, 1.0))

        # 6. Update height (in case new content loaded dynamically)
        new_total_height = await page.evaluate("document.body.scrollHeight")
        
        # If the page grew (infinite scroll), update our goal
        if new_total_height > total_height:
            total_height = new_total_height
        
        # If we reached the known bottom, break
        if current_position >= total_height:
            break

    # Final pause at the bottom to ensure last elements render
    await asyncio.sleep(1)
    print("Reached the bottom.")

async def scrape_worker(category_name, url, proxy_config=None):
    """
    Handles the full lifecycle for ONE category using Playwright:
    Open -> Loop 5 times -> (Expand View More -> Scrape) -> Save JSON
    """
    
    print(f"{category_name} Starting worker with Playwright...")
    
    async with async_playwright() as p:
        # Launcher options
        launch_options = {
            "headless": True,
            "args": ["--disable-blink-features=AutomationControlled"]
        }
        
        if proxy_config:
            launch_options["proxy"] = proxy_config

        browser = await p.chromium.launch(**launch_options)
        
        # Context options for better fingerprint
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
            locale="en-US",
            timezone_id="Asia/Jakarta"
        )
        
        # Apply Stealth
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Additional CDP Metadata (Client Hints)
        client = await page.context.new_cdp_session(page)
        await client.send('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
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

        try:
            # Neutral navigation - Using domcontentloaded to be faster/more resilient
            await page.goto("https://shop-id.tokopedia.com/", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(random.uniform(2, 4))
            
            # Navigate to target
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(random.uniform(5, 8))
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{category_name}_initial_load.png"))
            
            for loop_index in range(1, MAX_LOOPS + 1):
                print(f"[{category_name}] Iteration {loop_index}/{MAX_LOOPS}...")

                if loop_index > 1:
                    await page.reload(wait_until="networkidle")
                    await asyncio.sleep(random.uniform(5, 8))
                
                click_count = 0
                while True:
                    try:
                        await scroll_to_bottom_human(page)
                        
                        # Check for "No more products"
                        no_more_elements = await page.query_selector_all("//span[contains(text(), 'No more products')]")
                        if no_more_elements:
                            print(f"[{category_name}] Reached 'No more products'.")
                            break

                        # Find "View more" button
                        view_more_button = page.get_by_role("button", name="View more").first
                        if await view_more_button.is_visible():
                            await view_more_button.scroll_into_view_if_needed()
                            await asyncio.sleep(random.uniform(0.5, 1.5))
                            await view_more_button.click()
                            
                            click_count += 1
                            await asyncio.sleep(random.uniform(3, 5))
                            
                            if click_count % 5 == 0:
                                print(f"[{category_name}] Expanded {click_count} times...")
                                await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{category_name}_expanded_{click_count}.png"))
                        else:
                            # Re-check for "No more products"
                            no_more_elements = await page.query_selector_all("//span[contains(text(), 'No more products')]")
                            if no_more_elements:
                                break
                            print(f"[{category_name}] 'View more' button not found/visible. Stopping.")
                            break
                    except Exception as e:
                        print(f"[{category_name}] Expansion interrupt: {e}")
                        break

                # Collect Data
                print(f"[{category_name}] Parsing page content...")
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                product_cards = soup.select("div.w-full.cursor-pointer")
                
                iteration_products = []
                for card in product_cards:
                    try:
                        img_tag = card.select_one("div.relative img")
                        img_link = img_tag.get('src', '') if img_tag else "N/A"

                        link_tag = card.select_one("a[href]")
                        product_link = link_tag.get('href', '') if link_tag else "N/A"
                        if product_link and not product_link.startswith('http'):
                            product_link = "https://shop-id.tokopedia.com" + product_link
                            
                        title_tag = card.select_one("h3")
                        product_name = title_tag.get_text(strip=True) if title_tag else "N/A"

                        rating_tag = card.select_one("span.P3-Semibold")
                        rating = rating_tag.get_text(strip=True) if rating_tag else "0"

                        sold = "0"
                        p3_regular_tags = card.select("span.P3-Regular")
                        for p in p3_regular_tags:
                            txt = p.get_text(strip=True).lower()
                            if "sold" in txt or "terjual" in txt:
                                sold = txt
                                break

                        price_final = "0"
                        price_original = None
                        discount = None

                        disc_tag = card.select_one("span.H2-Regular.text-color-UITextPrimary")
                        price_tag = card.select_one("span.H2-Semibold.text-color-UIText1")
                        
                        if price_tag:
                            price_final = price_tag.get_text(strip=True)

                        if disc_tag:
                            discount = disc_tag.get_text(strip=True)
                            old_price_tag = card.select_one("span.line-through")
                            if old_price_tag:
                                price_original = old_price_tag.get_text(strip=True)

                        item_data = {
                            "name": product_name,
                            "url": product_link,
                            "image": img_link,
                            "rating": rating,
                            "sold_quantity": sold,
                            "price_current": price_final,
                            "price_original": price_original,
                            "discount": discount
                        }
                        iteration_products.append(item_data)
                    except Exception:
                        continue
                
                save_raw_data(category_name, iteration_products)

        except Exception as e:
            print(f"[{category_name}] Critical Error: {e}")
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{category_name}_error.png"))
            raise e # Propagate error
            
        finally:
            await page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{category_name}_final.png"))
            await browser.close()

async def main():
    # Proxy Setup
    proxy_url = os.getenv("PROXY_URL")
    proxy_config = None
    if proxy_url and "@" in proxy_url:
        print("Configuring residential proxy for Playwright...")
        try:
            parts = proxy_url.replace("http://", "").replace("https://", "").split("@")
            auth = parts[0].split(":")
            server_part = parts[1]
            proxy_config = {
                "server": f"http://{server_part}",
                "username": auth[0],
                "password": auth[1]
            }
        except Exception as e:
            print(f"Failed to parse Proxy URL: {e}")

    for category, link in URLS.items():
        print(f"Starting Playwright scrape for: {category}")
        await scrape_worker(category, link, proxy_config)

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")
