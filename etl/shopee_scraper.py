import asyncio
import time
import json
import os
import random
from playwright.async_api import async_playwright, Playwright, Page
from playwright_stealth import Stealth
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Global Configuration
ETL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(ETL_DIR, "..")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SCREENSHOT_DIR = os.path.join(DATA_DIR, "screenshots")
COOKIES_PATH = os.path.join(DATA_DIR, "cookies_shopee.json")
PLAYWRIGHT_SESSION_PATH = os.path.join(DATA_DIR, "shopee_playwright.json")
SHOPEE_DATA_DIR = os.path.join(PROJECT_ROOT, "shopee_data")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(SHOPEE_DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)

URLS = {
    "skincare": "https://shopee.co.id/search?keyword=skincare"
}

def cookies_repair():
    # Load the raw export from the extension if it exists
    raw_cookie_file = COOKIES_PATH
    if not os.path.exists(raw_cookie_file):
        print(f"⚠️ No raw {COOKIES_PATH} found for repair.")
        return

    with open(raw_cookie_file, "r") as f:
        extension_cookies = json.load(f)

    # Convert to Playwright format
    formatted_cookies = []
    for c in extension_cookies:
        # EditThisCookie might use slightly different keys, standardizing them:
        cookie = {
            "name": c.get("name"),
            "value": c.get("value"),
            "domain": c.get("domain"),
            "path": c.get("path", "/"),
            "expires": c.get("expirationDate"),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
            "sameSite": c.get("sameSite", "Lax")
        }
        # Remove None values (like expirationDate if session cookie)
        cookie = {k: v for k, v in cookie.items() if v is not None}
        formatted_cookies.append(cookie)

    # Playwright Structure
    final_data = {
        "cookies": formatted_cookies,
        "origins": [] # LocalStorage is hard to export via extension, usually Cookies are enough
    }

    with open(PLAYWRIGHT_SESSION_PATH, "w") as f:
        json.dump(final_data, f, indent=4)

    print(f"[SUCCESS] Converted to '{PLAYWRIGHT_SESSION_PATH}'")

    file_path = PLAYWRIGHT_SESSION_PATH

    if not os.path.exists(file_path):
        print(f"[ERROR]: {file_path} not found.")
        return

    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        fixed_count = 0

        # Iterate through cookies and fix 'sameSite'
        if "cookies" in data:
            for cookie in data["cookies"]:
                original_value = cookie.get("sameSite")

                # 1. Fix common Extension export values
                if original_value == "no_restriction":
                    cookie["sameSite"] = "None"
                    fixed_count += 1
                elif original_value == "unspecified":
                    cookie["sameSite"] = "Lax"
                    fixed_count += 1

                # 2. Fix Case Sensitivity (lax -> Lax)
                elif original_value and original_value.lower() == "lax":
                    cookie["sameSite"] = "Lax"
                    fixed_count += 1
                elif original_value and original_value.lower() == "strict":
                    cookie["sameSite"] = "Strict"
                    fixed_count += 1
                elif original_value and original_value.lower() == "none":
                    cookie["sameSite"] = "None"
                    fixed_count += 1

                # 3. If missing or invalid, default to 'Lax'
                elif original_value not in ["Strict", "Lax", "None"]:
                    cookie["sameSite"] = "Lax"
                    fixed_count += 1

                # 4. Ensure 'secure' is True if sameSite is None (Browser requirement)
                if cookie["sameSite"] == "None":
                    cookie["secure"] = True

        # Save the fixed file
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

        print(f"[SUCCESS] Repair Complete! Fixed {fixed_count} cookies.")
        print(f"[INFO] Saved updated file to: {file_path}")
        print("[INFO] You can now run your main script.")

    except Exception as e:
        print(f"[ERROR] Failed to repair JSON: {e}")

async def scroll_to_bottom_human(page):
    """
    Scrolls down the page in random steps with variable pauses 
    to mimic human behavior and trigger lazy-loaded elements.
    """
    print("Starting human-like scroll...")
    try:
        total_height = await page.evaluate("document.body.scrollHeight")
        current_position = 0
        
        while current_position < total_height:
            step = random.randint(300, 700)
            current_position += step
            
            # Use try/except inside the loop for context destruction
            try:
                await page.evaluate(f"window.scrollTo(0, {current_position});")
                await asyncio.sleep(random.uniform(0.5, 1.2))
                
                if random.random() < 0.1:
                    scroll_up = random.randint(100, 300)
                    current_position -= scroll_up
                    await page.evaluate(f"window.scrollTo(0, {current_position});")
                    await asyncio.sleep(random.uniform(0.5, 1.0))

                new_total_height = await page.evaluate("document.body.scrollHeight")
                if new_total_height > total_height:
                    total_height = new_total_height
                if current_position >= total_height:
                    break
            except Exception as e:
                if "context was destroyed" in str(e).lower():
                    print("⚠️ Context destroyed during scroll (possibly a redirect). Waiting...")
                    await asyncio.sleep(5)
                    return # Exit scroll early to allow caller to handle state
                raise e
    except Exception as e:
        print(f"⚠️ Scroll behavior interrupted: {e}")
    
    print("Reached the bottom.")

# Response handler for intersected APIs

async def handle_response(response):
    # Shopee Product API usually contains "api/v4/item/get" or "get_item_detail"
    target_keywords = ["api/v4/item/get", "get_item_detail", "get_pc", "api/v4/search/search_items", "api/v4/search/search_user"]

    if any(keyword in response.url for keyword in target_keywords):
        print(f"\n[+] API Intercepted: {response.url}")

        try:
            if response.status == 200:
                json_data = await response.json()
                timestamp = int(time.time() * 1000)
                filename = os.path.join(SHOPEE_DATA_DIR, f"response_{timestamp}.json")

                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4, ensure_ascii=False)

                print(f"   ✅ Saved JSON to {filename}")
            else:
                print(f"   ❌ Response status: {response.status}")
        except Exception:
            pass

async def human_jitter(page: Page, duration: int):
    """
    Performs micro mouse movements to simulate human presence during waits.
    """
    steps = int(duration / 0.5)
    for _ in range(steps):
        try:
            # Get random small movement
            x, y = random.randint(-10, 10), random.randint(-10, 10)
            # Use mouse.move with relative coordinates or just move slightly
            # Since we don't know exact mouse pos, we move to a random near point
            # or just jitter around current screen center
            viewport = page.viewport_size
            if viewport:
                center_x, center_y = viewport['width'] / 2, viewport['height'] / 2
                await page.mouse.move(center_x + x, center_y + y)
            await asyncio.sleep(0.5)
        except:
            break

async def scrape_worker(category_name, url, proxy_config=None):
    """
    Handles the full lifecycle for Shopee using advanced stealth:
    Direct/Cookies -> Human Behavior -> Intercept API
    """
    print(f"[{category_name}] Starting worker (Proxy: {'Yes' if proxy_config else 'No'})...")
    
    async with async_playwright() as p:
        # Launcher options
        launch_options = {
            "headless": False,
            "args": ["--disable-blink-features=AutomationControlled"]
        }
        
        if proxy_config:
            launch_options["proxy"] = proxy_config

        browser = await p.chromium.launch(**launch_options)
        
        context_options = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.6 Safari/537.36",
            "viewport": {"width": 1366, "height": 768},
            "locale": "id-ID",
            "timezone_id": "Asia/Jakarta",
            "ignore_https_errors": True
        }

        context = await browser.new_context(**context_options)
        
        # Load cookies
        possible_cookie_paths = [PLAYWRIGHT_SESSION_PATH, COOKIES_PATH]
        loaded_success = False
        
        for p_path in possible_cookie_paths:
            if os.path.exists(p_path):
                try:
                    with open(p_path, 'r') as f:
                        cookies_data = json.load(f)
                        # Handle both raw list and {'cookies': [...]} format
                        if isinstance(cookies_data, dict) and 'cookies' in cookies_data:
                            await context.add_cookies(cookies_data['cookies'])
                        else:
                            await context.add_cookies(cookies_data)
                    print(f"[{category_name}] Cookies loaded successfully from {os.path.basename(p_path)}.")
                    loaded_success = True
                    break
                except Exception as e:
                    print(f"[{category_name}] Failed to load cookies from {p_path}: {e}")
        
        if not loaded_success:
            print(f"[{category_name}] No valid cookies found to load.")

        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        # Advanced CDP Metadata (Client Hints)
        client = await page.context.new_cdp_session(page)
        await client.send('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7632.6 Safari/537.36",
            "platform": "Windows",
            "userAgentMetadata": {
                "brands": [
                    {"brand": "Not(A:Brand", "version": "8"}, {"brand": "Chromium", "version": "145"}, {"brand": "Google Chrome", "version": "145"}
                ],
                "fullVersionList": [
                    {"brand": "Not(A:Brand", "version": "8.0.0.0"}, {"brand": "Chromium", "version": "145.0.0.0"}, {"brand": "Google Chrome", "version": "145.0.0.0"}
                ],
                "platform": "Windows", "platformVersion": "10.0.0", "architecture": "x86", "model": "", "mobile": False
            }
        })

        # Deep Stealth Overrides
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // Mock realistic hardware concurrency
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
            // Mock realistic device memory
            Object.defineProperty(navigator, 'deviceMemory', { get: () => 16 });
            
            // Mask WebGL
            const getParameter = HTMLCanvasElement.prototype.getContext('2d').constructor.prototype.getParameter;
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type, attributes) {
                const context = originalGetContext.apply(this, arguments);
                if (type === 'webgl' || type === 'experimental-webgl' || type === 'webgl2') {
                    const getParameterProxy = context.getParameter;
                    context.getParameter = function(parameter) {
                        if (parameter === 37445) return 'Intel Inc.';
                        if (parameter === 37446) return 'Intel(R) Iris(R) Xe Graphics (0x9A49)';
                        return getParameterProxy.apply(this, arguments);
                    };
                }
                return context;
            };

            // Mock realistic plugins
            const mockPlugins = [
                { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Chromium PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'Microsoft Edge PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'PDF Viewer', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                { name: 'WebKit built-in PDF', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }
            ];
            Object.defineProperty(navigator, 'plugins', { get: () => mockPlugins });
            Object.defineProperty(navigator, 'languages', { get: () => ['id-ID', 'id', 'en-US', 'en'] });
        """)

        # Shared semaphore to limit concurrency
        CONCURRENCY_LIMIT = 3
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        async def process_page(p_num):
            async with semaphore:
                # Staggered start to avoid simultaneous bursts (Rate Limiting)
                stagger_delay = random.uniform(5, 15)
                print(f"[{category_name}] Page {p_num}: Staggering start for {stagger_delay:.2f}s...")
                await asyncio.sleep(stagger_delay)

                page = await context.new_page()
                try:
                    await Stealth().apply_stealth_async(page)
                    
                    # Apply stealth overrides to each new page
                    await page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        Object.defineProperty(navigator, 'languages', { get: () => ['id-ID', 'id', 'en-US', 'en'] });
                    """)

                    page.on("response", handle_response)
                    
                    print(f"[{category_name}] Page {p_num}: Navigating to target...")
                    page_url = f"{url}&page={p_num}"
                    
                    # Use a realistic timeout and wait for domcontentloaded
                    await page.goto(page_url, wait_until="domcontentloaded", timeout=90000)
                    
                    # Randomized wait for stability (Bot Detection Avoidance)
                    wait_time = random.uniform(20, 40)
                    print(f"[{category_name}] Page {p_num}: Waiting {wait_time:.2f}s for stability...")
                    await human_jitter(page, int(wait_time))
                    
                    await scroll_to_bottom_human(page)
                    print(f"[{category_name}] Page {p_num}: Finished scraping.")
                    
                except Exception as e:
                    print(f"[{category_name}] Page {p_num} Failed: {e}")
                finally:
                    await page.close()

        try:
            # 1. Warm-up / Initial Check
            first_page = await context.new_page()
            await Stealth().apply_stealth_async(first_page)
            first_page.on("response", handle_response)
            
            print(f"[{category_name}] Performing initial warm-up navigation...")
            await first_page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await human_jitter(first_page, 20)
            
            # Check for initial block
            content = await first_page.content()
            block_indicators = ["Terjadi Kesalahan", "Something went wrong", "System busy", "Silakan coba lagi"]
            if any(ind in content for ind in block_indicators):
                print(f"[{category_name}] INITIAL BLOCK DETECTED. Aborting concurrent phase.")
                await first_page.close()
                return False
            
            await first_page.screenshot(path=os.path.join(SCREENSHOT_DIR, f"{category_name}_shopee_initial.png"))
            await scroll_to_bottom_human(first_page)
            await first_page.close()

            # 2. Concurrent Scraping for remaining pages
            print(f"[{category_name}] Starting concurrent scrape for pages 1-14 (Concurrency: {CONCURRENCY_LIMIT})...")
            tasks = [process_page(i) for i in range(1, 15)]
            await asyncio.gather(*tasks)

            return True
        except Exception as e:
            print(f"[{category_name}] Worker Failed: {e}")
            return False
        finally:
            try:
                cookies = await context.cookies()
                with open(COOKIES_PATH, 'w') as f:
                    json.dump(cookies, f, indent=4)
                print(f"[{category_name}] Cookies saved successfully.")
            except Exception as e:
                print(f"[{category_name}] Failed to save cookies: {e}")
            await browser.close()

async def main():
    cookies_repair()
    proxy_url = os.getenv("PROXY_URL")
    if proxy_url:
        proxy_url = proxy_url.strip('"').strip("'")
    
    proxy_config = None
    if proxy_url and "@" in proxy_url:
        try:
            # Handle http:// or https:// and split by @
            clean_url = proxy_url.replace("http://", "").replace("https://", "")
            parts = clean_url.split("@")
            auth = parts[0].split(":")
            server = parts[1]
            proxy_config = {
                "server": f"http://{server}",
                "username": auth[0],
                "password": auth[1]
            }
            print(f"[INFO] Proxy configured: {server}")
        except Exception as e:
            print(f"[ERROR] Failed to parse Proxy URL: {e}")

    success_found = False
    for category, link in URLS.items():
        print(f"--- Processing Shopee Category: {category} ---")
        category_success = False
        if os.path.exists(COOKIES_PATH):
            print(f"[{category}] Step 1: Attempting with cookies (Direct)...")
            category_success = await scrape_worker(category, link, proxy_config=None)
        
        if not category_success and proxy_config:
            print(f"[{category}] Step 2: Falling back to PROXY...")
            category_success = await scrape_worker(category, link, proxy_config=proxy_config)

        if category_success: success_found = True
    
    if not success_found: raise Exception("All scraping strategies failed.")

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")
