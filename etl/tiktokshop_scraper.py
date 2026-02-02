import os
import json
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Global Configuration
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies_raw.json")
MAX_LOOPS = 5  # As requested in step 4
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# URLs provided in step 1
URLS = {
    "beauty": "https://shop-id.tokopedia.com/c/beauty-personal-care/601450"
}

def clean_price(text):
    """Helper to remove non-numeric chars for storage if needed"""
    return text.replace("Rp", "").replace(".", "").strip()

def setup_driver():
    options = uc.ChromeOptions()
    
    # Check for linux version to help uc match driver
    version_main = None
    if os.name != 'nt': # Linux/GHA
        try:
            import subprocess
            res = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
            version_str = res.stdout.strip()
            # "Google Chrome 114.0.5735.90" -> 114
            version_main = int(version_str.split(' ')[2].split('.')[0])
        except:
            pass

    # 1. Use the "New" Headless mode
    options.add_argument("--headless=new") 
    
    # 2. Force a standard Desktop Resolution
    options.add_argument("--window-size=1366,768")
    
    # 3. Force a Real User-Agent (Matching your manual payload)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36")
    
    # 4. Standard bypasses & Stealth
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--lang=en-US,en;q=0.9")
    
    # Initialize with detected version if on linux
    if version_main:
        print(f"Detected Chrome version: {version_main}")
        driver = uc.Chrome(options=options, version_main=version_main)
    else:
        driver = uc.Chrome(options=options)
    
    # 5. EXTRA SAFETY
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "platform": "Windows"
    })
    driver.set_window_size(1366, 768)

    return driver

def inject_cookies(driver):
    """
    Injects cookies from COOKIES_FILE.
    Supports standard and EditThisCookie formats.
    """
    if not os.path.exists(COOKIES_FILE):
        print(f"No {COOKIES_FILE} found, skipping cookie injection.")
        return

    try:
        with open(COOKIES_FILE, "r") as file:
            data = json.load(file)
            
        all_cookies = data['cookies'] if (isinstance(data, dict) and 'cookies' in data) else data
        
        # Domains to set context for
        domains = [".tokopedia.com", "shop-id.tokopedia.com"]
        
        for domain_root in domains:
            # Filter cookies for this specific domain
            filtered = [c for c in all_cookies if domain_root in c.get('domain', '')]
            if not filtered:
                continue
                
            # Load the domain context (without 404 to avoid bot flags)
            driver.get(f"https://{domain_root.lstrip('.')}/")
            time.sleep(2)
            
            for c in filtered:
                try:
                    # Clean cookie dict for Selenium compatibility
                    new_cookie = {
                        'name': c['name'],
                        'value': c['value'],
                        'domain': c.get('domain'),
                        'path': c.get('path', '/'),
                        'secure': c.get('secure', False),
                        'httpOnly': c.get('httpOnly', False)
                    }
                    
                    # Handle expiry (EditThisCookie uses expirationDate)
                    expiration = c.get('expirationDate', c.get('expiry', c.get('expires')))
                    if expiration:
                        new_cookie['expiry'] = int(float(expiration))
                    
                    # Handle sameSite casing (strict -> Strict)
                    ss = c.get('sameSite', '').lower()
                    if ss in ['strict', 'lax', 'none']:
                        new_cookie['sameSite'] = ss.capitalize()

                    driver.add_cookie(new_cookie)
                except Exception:
                    pass
            
    except Exception as e:
        print(f"Cookie injection warning: {e}")

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

def scroll_to_bottom_human(driver):
    """
    Scrolls down the page in random steps with variable pauses 
    to mimic human behavior and trigger lazy-loaded elements.
    """
    print("Starting human-like scroll...")
    
    # Get total page height
    total_height = driver.execute_script("return document.body.scrollHeight")
    current_position = 0
    
    while current_position < total_height:
        # 1. Randomize scroll step (between 300px and 700px)
        step = random.randint(300, 700)
        
        # 2. Calculate new position
        current_position += step
        
        # 3. Apply scroll command
        driver.execute_script(f"window.scrollTo(0, {current_position});")
        
        # 4. Random Wait (0.3s to 1.5s) - Mimics looking at products
        time.sleep(random.uniform(0.3, 0.8))
        
        # 5. Occasional "Scroll Up" (10% chance) - Mimics checking previous item
        if random.random() < 0.1:
            scroll_up = random.randint(100, 300)
            current_position -= scroll_up
            driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.5, 1.0))

        # 6. Update height (in case new content loaded dynamically)
        new_total_height = driver.execute_script("return document.body.scrollHeight")
        
        # If the page grew (infinite scroll), update our goal
        if new_total_height > total_height:
            total_height = new_total_height
        
        # If we reached the known bottom, break
        if current_position >= total_height:
            break

    # Final pause at the bottom to ensure last elements render
    time.sleep(1)
    print("Reached the bottom.")
    
def scrape_worker(category_name, url):
    """
    This function runs in a separate thread.
    It handles the full lifecycle for ONE category:
    Open -> Loop 5 times -> (Expand View More -> Scrape) -> Save JSON
    """
    
    print(f"{category_name} Starting worker...")
    driver = setup_driver()
    inject_cookies(driver)
    
    all_collected_data = []
    driver.get(url)
    time.sleep(5) # Initial load wait
    driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{category_name}_initial_load.png"))
    
    try:
        # Step 4: Loop 5 times
        for loop_index in range(1, MAX_LOOPS + 1):
            print(f"[{category_name}] Iteration {loop_index}/{MAX_LOOPS} - Navigating...")

            if loop_index > 1:
                driver.refresh()
                time.sleep(5)
            
            # Step 2: Click "View More" until "No more products"
            click_count = 0
            while True:
                try:
                    # 1. Check for "No more products" text to stop
                    # specific span with 40% opacity as per your HTML
                    scroll_to_bottom_human(driver)
                    no_more = driver.find_elements(By.XPATH, "//span[contains(text(), 'No more products')]")
                    if no_more:
                        print(f"[{category_name}] Reached 'No more products'.")
                        break

                    # 2. Find the button by TEXT "View more"
                    # We use normalize-space() to ignore extra whitespace/newlines
                    view_more_xpath = "//button[normalize-space()='View more']"
                    buttons = driver.find_elements(By.XPATH, view_more_xpath)
                    
                    if buttons:
                        btn = buttons[0]
                        
                        # Scroll to button to avoid "ElementClickInterceptedException"
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(1) # Small pause for scroll animation
                        
                        # Click via JS is often more robust for these infinite load buttons
                        driver.execute_script("arguments[0].click();", btn)
                        
                        click_count += 1
                        
                        # Wait for content to load
                        time.sleep(3) 
                        
                        if click_count % 5 == 0:
                            print(f"[{category_name}] Expanded {click_count} times...")
                            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{category_name}_expanded_{click_count}.png"))
                    else:
                        # If we don't see "View more", check "No more products" one last time
                        if driver.find_elements(By.XPATH, "//span[contains(text(), 'No more products')]"):
                            print(f"[{category_name}] End of list detected.")
                            break
                        
                        # If neither is found, we might be stuck or page is loading slowly
                        print(f"[{category_name}] 'View more' button disappeared. Stopping.")
                        break
                        
                except Exception as e:
                    print(f"[{category_name}] Expansion interrupt: {e}")
                    break

            # Step 3: Collect Data (Using BeautifulSoup for speed)
            print(f"[{category_name}] Parsing page content...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Selector: class="w-full cursor-pointer"
            product_cards = soup.select("div.w-full.cursor-pointer")
            
            iteration_products = []
            
            for card in product_cards:
                try:
                    # 1. Image
                    img_tag = card.select_one("div.relative img")
                    img_link = img_tag.get('src', '') if img_tag else "N/A"

                    # 2. Title and Link
                    # Anchor inside the card
                    link_tag = card.select_one("a[href]")
                    product_link = link_tag.get('href', '') if link_tag else "N/A"
                    if product_link and not product_link.startswith('http'):
                        product_link = "https://shop-id.tokopedia.com" + product_link
                        
                    # Title is in h3 inside the link
                    title_tag = card.select_one("h3")
                    product_name = title_tag.get_text(strip=True) if title_tag else "N/A"

                    # 3. Rating (span class P3-Semibold)
                    # Use class substring matching because of tailwind utility classes
                    rating_tag = card.select_one("span.P3-Semibold")
                    rating = rating_tag.get_text(strip=True) if rating_tag else "0"

                    # 4. Sold (span class P3-Regular containing 'sold')
                    # We look for a P3-Regular that might contain "sold" or "terjual"
                    sold = "0"
                    p3_regular_tags = card.select("span.P3-Regular")
                    for p in p3_regular_tags:
                        txt = p.get_text(strip=True).lower()
                        if "sold" in txt or "terjual" in txt:
                            sold = txt
                            break

                    # 5. Price Logic
                    price_final = "0"
                    price_original = None
                    discount = None

                    # Check for discount percentage tag (H2-Regular text-color-UITextPrimary)
                    disc_tag = card.select_one("span.H2-Regular.text-color-UITextPrimary")
                    
                    # The main price is usually in H2-Semibold
                    price_tag = card.select_one("span.H2-Semibold.text-color-UIText1")
                    
                    if price_tag:
                        price_final = price_tag.get_text(strip=True)

                    if disc_tag:
                        discount = disc_tag.get_text(strip=True)
                        # Old price is usually line-through
                        old_price_tag = card.select_one("span.line-through")
                        if old_price_tag:
                            price_original = old_price_tag.get_text(strip=True)

                    item_data = {
                        #"loop_iteration": loop_index,
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
                    
                except Exception as parse_err:
                    continue # Skip bad card
            
            # After finishing a loop or at the end of the worker:
            save_raw_data(category_name, iteration_products)
            
            # Refresh happen automatically at start of next loop via driver.get()
            
    except Exception as e:
        print(f"[{category_name}] Critical Error: {e}")
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{category_name}_error.png"))
        
    finally:
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, f"{category_name}_final.png"))
        fresh_cookies = driver.get_cookies()
        print(f"Captured {len(fresh_cookies)} fresh cookies.")

        #6. Save to File
        with open("cookies_raw.json", "w") as f:
            json.dump(fresh_cookies, f, indent=4)
            
        driver.quit()
        
    return f"Finished {category_name}"

def main():
    # The loop to call the function
    for category, link in URLS.items():
    	print(f"Starting scrape for: {category}")
    	scrape_worker(category, link)

if __name__ == "__main__":
    start_time = time.time()
    main()
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")
