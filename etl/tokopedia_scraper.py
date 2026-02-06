import os
import json
import asyncio
import random
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
COOKIES_PATH = os.path.join(DATA_DIR, "cookies_tokopedia.json")
RAW_OUTPUT_PATH = os.path.join(DATA_DIR, "raw", "tokopedia_raw.json")
GQL_URL = "https://gql.tokopedia.com/graphql/SearchProductV5Query"
BASE_URL = "https://www.tokopedia.com/"

def get_proxy_config():
    proxy_url = os.getenv("PROXY_URL")
    if not proxy_url:
        return None
    
    try:
        # Format: http://user:pass@host:port
        # Split into auth and server
        if "@" not in proxy_url:
             return {"server": proxy_url}
             
        scheme_rest = proxy_url.split("://")
        scheme = scheme_rest[0]
        rest = scheme_rest[1]
        
        auth_server = rest.split("@")
        auth = auth_server[0].split(":")
        server = auth_server[1]
        
        return {
            "server": f"{scheme}://{server}",
            "username": auth[0],
            "password": auth[1]
        }
    except Exception as e:
        print(f"Error parsing proxy: {e}")
        return None

os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)

# Captured query string
GQL_QUERY = """query SearchProductV5Query($params: String!) {
  searchProductV5(params: $params) {
    header {
      totalData
      responseCode
      keywordProcess
      keywordIntention
      componentID
      isQuerySafe
      additionalParams
      backendFilters
      meta {
        dynamicFields
        __typename
      }
      __typename
    }
    data {
      totalDataText
      banner {
        position
        text
        applink
        url
        imageURL
        componentID
        trackingOption
        __typename
      }
      redirection {
        url
        __typename
      }
      related {
        relatedKeyword
        position
        trackingOption
        otherRelated {
          keyword
          url
          applink
          componentID
          products {
            oldID: id
            id: id_str_auto_
            name
            url
            applink
            mediaURL {
              image
              __typename
            }
            shop {
              oldID: id
              id: id_str_auto_
              name
              city
              tier
              __typename
            }
            badge {
              oldID: id
              id: id_str_auto_
              title
              url
              __typename
            }
            price {
              text
              number
              __typename
            }
            freeShipping {
              url
              __typename
            }
            labelGroups {
              position
              title
              type
              url
              styles {
                key
                value
                __typename
              }
              __typename
            }
            rating
            wishlist
            ads {
              id
              productClickURL
              productViewURL
              productWishlistURL
              tag
              __typename
            }
            meta {
              oldWarehouseID: warehouseID
              warehouseID: warehouseID_str_auto_
              componentID
              __typename
            }
            __typename
          }
          __typename
        }
        __typename
      }
      suggestion {
        currentKeyword
        suggestion
        query
        text
        componentID
        trackingOption
        __typename
      }
      ticker {
        oldID: id
        id: id_str_auto_
        text
        query
        applink
        componentID
        trackingOption
        __typename
      }
      violation {
        headerText
        descriptionText
        imageURL
        ctaURL
        ctaApplink
        buttonText
        buttonType
        __typename
      }
      products {
        oldID: id
        id: id_str_auto_
        ttsProductID
        name
        url
        applink
        mediaURL {
          image
          image300
          videoCustom
          __typename
        }
        shop {
          oldID: id
          id: id_str_auto_
          ttsSellerID
          name
          url
          city
          tier
          __typename
        }
        stock {
          ttsSKUID
          __typename
        }
        badge {
          oldID: id
          id: id_str_auto_
          title
          url
          __typename
        }
        price {
          text
          number
          range
          original
          discountPercentage
          __typename
        }
        freeShipping {
          url
          __typename
        }
        labelGroups {
          position
          title
          type
          url
          styles {
            key
            value
            __typename
          }
          __typename
        }
        labelGroupsVariant {
          title
          type
          typeVariant
          hexColor
          __typename
        }
        category {
          oldID: id
          id: id_str_auto_
          name
          breadcrumb
          gaKey
          __typename
        }
        rating
        wishlist
        ads {
          id
          productClickURL
          productViewURL
          productWishlistURL
          tag
          __typename
        }
        meta {
          oldParentID: parentID
          parentID: parentID_str_auto_
          oldWarehouseID: warehouseID
          warehouseID: warehouseID_str_auto_
          isImageBlurred
          isPortrait
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}"""

async def refresh_cookies(search_query): # Updated signature
    print("Launching browser to refresh cookies...") # Updated print statement
    
    proxy_config = get_proxy_config()
    
    async with async_playwright() as p:
        # Launch options - HEADLESS TRUE with Chrome channel
        browser = await p.chromium.launch(
            headless=True,  # Keep headless=True for Linux/server environment
            channel="chrome", # Use installed Chrome to bypass some fingerprinting
            proxy=proxy_config, # Added proxy config
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox", 
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
                # "--start-maximized" # Not supported in headless usually, but window-size helps
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            proxy=proxy_config,
            viewport={"width": 1920, "height": 1080},
            locale="id-ID",
            timezone_id="Asia/Jakarta",
            ignore_https_errors=True,
            permissions=["geolocation"]
        )
        
        # Enable stealth mode
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()

        # Check existing cookies if any (optional, usually we want fresh for a "refresh")
        
        # Capture Payload Logic
        payload_file = os.path.join(DATA_DIR, "tokopedia_payload_template.json")
        
        async def handle_request(request):
            if "graphql" in request.url and request.method == "POST":
                try:
                    pd = request.post_data_json
                    # pd could be list or dict
                    items = pd if isinstance(pd, list) else [pd]
                    for item in items:
                        if item.get("operationName") == "SearchProductV5Query":
                            with open(payload_file, "w") as f:
                                json.dump(items, f, indent=2) 
                            print("CAPTURED VALID GRAPHQL PAYLOAD!")
                except:
                    pass

        page.on("request", handle_request)

        try:
            print(f"Navigating to {BASE_URL}...")
            try:
                await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000) # Updated timeout
                await asyncio.sleep(5)
                # Take screenshot to document headless state
                await page.screenshot(path="headless_evidence.png")
                print("Screenshot saved to headless_evidence.png")
            except Exception as e:
                print(f"Homepage load warning: {e}")
                await page.screenshot(path="headless_error.png")

            print("Navigating to search page...")
            try:
                await page.goto(f"https://www.tokopedia.com/search?q={search_query}", wait_until="networkidle", timeout=30000) # Updated timeout and uses search_query
                await asyncio.sleep(5)
            except Exception:
                pass
            
            cookies = await context.cookies()
            if cookies:
                with open(COOKIES_PATH, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=4)
                print(f"Captured {len(cookies)} cookies.")
                return cookies
            else:
                print("No cookies were found.")
                return None
        finally:
            await browser.close()

def load_cookies():
    if os.path.exists(COOKIES_PATH):
        try:
            with open(COOKIES_PATH, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def get_unique_id(cookies):
    for cookie in cookies:
        if cookie['name'] == '_UUID_NONLOGIN':
            return cookie['value']
    return "375d353cd0827a0440c38c31b8646e14"

SEARCH_QUERIES = [ # Added SEARCH_QUERIES list
    "skincare",
    "serum wajah", 
    "toner wajah", 
    "moisturizer", 
    "sunscreen", 
    "pembersih wajah",
    "masker wajah"
]

async def fetch_page(request_context, page_number, unique_id, search_query): # Updated signature
    rows = 200
    start = rows * (page_number - 1)
    
    # Updated params with dynamic rows and start
    params = f"device=desktop&enter_method=normal_search&has_more=true&l_name=sre&navsource=&next_offset_organic={start}&next_offset_organic_ad={start}&ob=23&page={page_number}&q={search_query}&related=true&rows={rows}&safe_search=false&sc=&scheme=https&search_id=202602052325473FE94A002317B53B3POI&shipping=&show_adult=false&source=search&srp_component_id=02.01.00.00&srp_page_id=&srp_page_title=&st=product&start={start}&topads_bucket=true&unique_id={unique_id}&user_addressId=&user_cityId=176&user_districtId=2274&user_id=&user_lat=&user_long=&user_postCode=&user_warehouseId=&variants=&warehouses="
    
    # LIST Payload as captured
    payload = [{
        "operationName": "SearchProductV5Query",
        "variables": {"params": params},
        "query": GQL_QUERY
    }]
    
    try:
        print(f"Fetching Page {page_number} for query '{search_query}'...") # Updated print statement
        response = await request_context.post(
            GQL_URL,
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "x-source": "tokopedia-lite",
                "Referer": f"https://www.tokopedia.com/search?q={search_query}" # Updated Referer
            },
            timeout=20000 # Updated timeout
        )
        
        if response.status == 200:
            data = await response.json()
            
            # Normalize list vs dict response
            result_item = None
            if isinstance(data, list) and len(data) > 0:
                result_item = data[0]
            elif isinstance(data, dict):
                result_item = data
            
            if result_item:
                # Check for 'data' inside the result
                result_data = result_item.get('data')
                
                # Check for 'searchProductV5' structure
                if result_data and result_data.get('searchProductV5'):
                    search_product_v5 = result_data['searchProductV5']
                    
                    total_data = 0
                    if 'header' in search_product_v5 and 'totalData' in search_product_v5['header']:
                        total_data = search_product_v5['header']['totalData']

                    product_data = search_product_v5.get('data')
                    if product_data and product_data.get('products'):
                        products = product_data['products']
                        print(f"Page {page_number}: Success ({len(products)} products)")
                        return products, total_data
                    else:
                        print(f"Page {page_number}: Empty product list.")
                        return None, 0
                else:
                    # It might be an error structure e.g. {'errors': ...}
                    print(f"Page {page_number}: API Error or structure mismatch.")
                    return None, 0
            else:
                print(f"Page {page_number}: Unexpected JSON format.")
                return None, 0
        else:
            print(f"Page {page_number}: Failed with status {response.status}")
            return None, 0
    except Exception as e:
        print(f"Page {page_number}: Error: {e}")
        return None, 0

async def run_scraper():
    proxy_config = get_proxy_config()
    
    # Configuration for Mass Scraping
    TARGET_TOTAL = 6000 # This is the INCREMENT to add
    ROWS_PER_PAGE = 200
    BATCH_SIZE = 30 # Concurrent requests per session
    
    # Global containers
    all_products = []
    max_total_data = 0
    
    # Check for existing data to append
    if os.path.exists(RAW_OUTPUT_PATH):
        try:
            with open(RAW_OUTPUT_PATH, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, dict):
                    all_products = existing_data.get('products', [])
                    max_total_data = existing_data.get('total_data', 0)
            print(f"Loaded {len(all_products)} existing products from {RAW_OUTPUT_PATH}")
        except Exception as e:
            print(f"Error loading existing data: {e}")

    # Calculate final target logic
    initial_count = len(all_products)
    final_target_count = initial_count + TARGET_TOTAL
    print(f"Targeting {final_target_count} total products (Adding {TARGET_TOTAL} new products)...")

    # Calculate starting page based on existing products
    current_page = (len(all_products) // ROWS_PER_PAGE) + 1
    print(f"Resuming from Page {current_page}...")
    
    # Pick randomized query
    current_search_query = random.choice(SEARCH_QUERIES) # Added random query selection
    print(f"Selected Search Query: {current_search_query}")

    async with async_playwright() as p:
        # 1. First, check if we have valid cookies
        cookies = load_cookies()
        valid_cookies = False
        
        # Logic:
        # Phase A: Attempt to use existing cookies without proxy
        # Phase B: If that fails or no cookies, use Proxy to get new cookies
        
        target_proxy = None # Default to No Proxy
        
        if cookies:
            print("Cookies found. Verifying without proxy...")
            # Let's use `p.request.new_context` directly for verification.
            
            req_verify = await p.request.new_context(
                base_url=BASE_URL,
                storage_state={"cookies": cookies},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            
            unique_id_temp = get_unique_id(cookies)
            test_res, _ = await fetch_page(req_verify, 1, unique_id_temp, current_search_query) # Updated call
            await req_verify.dispose()
            
            if test_res: # If products were returned, cookies are likely valid
                print("Cookies are VALID. Using Direct Connection (No Proxy).")
                valid_cookies = True
                target_proxy = None
            else:
                print("Cookies Invalid/Expired. Switching to Proxy for Refresh...")
                target_proxy = proxy_config
        else:
            print("No cookies found. Using Proxy for initial session...")
            target_proxy = proxy_config
            
        # 2. Refresh if needed (With Proxy)
        if not valid_cookies:
            # Refresh Cookie Logic needs a Browser (Headless=True, Channel=Chrome) using Proxy
            cookies = await refresh_cookies(current_search_query) # Updated call
            if not cookies:
                print("Could not obtain session. Exiting.")
                return
            # After refresh, we can decide if we want to continue using proxy or not.
            # User said: "If it exist, don't use proxy".
            # So after we get cookies, run the scraper WITHOUT proxy?
            # I will assume: Use proxy to GET cookies, then use Direct connection to SCRAPE.
            print("Session Refreshed. Switching to Direct Connection for Scraping...")
            target_proxy = None
        
        # Get unique_id from the (potentially new) cookies
        unique_id = get_unique_id(cookies)

        # 3. Request Context for Scraping (Direct or Proxy based on target_proxy)
        print(f"Initializing Scraping Context (Proxy: {'YES' if target_proxy else 'NO'})...")
        request_context = await p.request.new_context(
            base_url=BASE_URL,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            extra_http_headers={"Origin": "https://www.tokopedia.com"},
            storage_state={"cookies": cookies} if cookies else None,
            proxy=target_proxy
        )
        print(f"Initial Session Unique ID: {unique_id}")

        while len(all_products) < final_target_count:
            print(f"\n--- Starting Batch for Pages {current_page} to {current_page + BATCH_SIZE - 1} ---")
            print(f"Progress: {len(all_products)} / {final_target_count} products collected.")
            
            # The request_context and unique_id are now established once before the loop.
            # If the user wants to rotate unique_id/cookies per batch, this loop structure needs further modification.
            # But based on the provided snippet, the context is created once.

            # 2. Prepare Batch Tasks
            tasks = []
            for i in range(BATCH_SIZE):
                absolute_page = current_page + i
                # Loop back to 1 every 30 pages (User specified max page is 30)
                effective_page = ((absolute_page - 1) % 30) + 1
                
                tasks.append(fetch_page(request_context, effective_page, unique_id, current_search_query)) # Updated call
            
            # 5. Execute Batch # Corrected comment from 3 to 5
            print(f"Executing {len(tasks)} concurrent requests...")
            results = await asyncio.gather(*tasks)
            
            # 4. Process Results
            batch_products = []
            for res in results:
                if res and res[0]:
                    prods, total = res
                    batch_products.extend(prods)
                    if total > max_total_data:
                        max_total_data = total
            
            # 5. Cleanup Context
            await request_context.dispose()
            
            if not batch_products:
                print("Warning: No products found in this batch.")
                # Optional: break if we consistently get no data, but let's continue for now
                
            all_products.extend(batch_products)
            current_page += BATCH_SIZE
            
            # 6. Incremental Save
            print(f"Batch complete. Found {len(batch_products)} products.")
            output_data = {
                "total_data": max_total_data,
                "products_count": len(all_products),
                "products": all_products
            }
            try:
                with open(RAW_OUTPUT_PATH, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=4, ensure_ascii=False)
                print(f"Saved {len(all_products)} products to disk.")
            except Exception as e:
                print(f"Error saving to file: {e}")

            # 7. Rate Limit / Cool down
            if len(all_products) < TARGET_TOTAL:
                print("Cooling down for 5 seconds...")
                await asyncio.sleep(60)
            else:
                print("Target reached!")

if __name__ == "__main__":
    asyncio.run(run_scraper())