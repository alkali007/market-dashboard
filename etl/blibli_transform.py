import json
import pandas as pd
import os
import sys

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_FILE = os.path.join(DATA_DIR, "raw", "blibli_raw.json")
PROCESSED_FILE = os.path.join(DATA_DIR, "processed", "blibli_cleaned.csv")

def clean_price(price_data):
    """Extract numeric price from price object."""
    if isinstance(price_data, dict):
        # Prefer salePrice or minPrice
        return price_data.get("salePrice") or price_data.get("minPrice") or 0
    return 0

def transform_data():
    if not os.path.exists(RAW_FILE):
        print(f"Raw file not found: {RAW_FILE}")
        return

    try:
        with open(RAW_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        items = data.get("items", [])
        print(f"Loaded {len(items)} items from {RAW_FILE}")
        
        extracted = []
        for item in items:
            try:
                # Handle DOM fallback items differently if needed, but assuming standard format first
                # Check if it's a DOM scraped item (has formattedId starting with dom_scrape_)
                is_dom_item = str(item.get("formattedId", "")).startswith("dom_scrape_")
                
                if is_dom_item:
                    # Logic for DOM scraped items
                    price_raw = item.get("price", "0")
                    # Clean "Rp31.800" or "31.800"
                    price = float(str(price_raw).replace("Rp", "").replace(".", "").replace(",", "").strip())
                    
                    extracted.append({
                        "name": item.get("name"),
                        "price": price,
                        "original_price": price, # Placeholder
                        "discount": 0,
                        "location": "Unknown", # DOM scrape might miss this
                        "rating": 0,
                        "sold": 0,
                        "shop_name": "Unknown",
                        "url": item.get("url"),
                        "image_url": item.get("image"),
                        "source": "blibli"
                    })
                else:
                    # Logic for API items (Standard)
                    price = float(clean_price(item.get("price", {})))
                    list_price = float(item.get("price", {}).get("listPrice", price))
                    
                    # URL construction
                    url_suffix = item.get("url", "")
                    full_url = f"https://www.blibli.com{url_suffix}" if url_suffix.startswith("/") else url_suffix
                    if not full_url.startswith("http"):
                        full_url = f"https://www.blibli.com/{url_suffix}"

                    # Image
                    images = item.get("images", [])
                    image_url = images[0] if images else ""

                    extracted.append({
                        "name": item.get("name"),
                        "price_current": price,
                        "price_original": list_price,
                        "discount": item.get("price", {}).get("discount", 0),
                        "location": item.get("location", ""),
                        "rating": float(item.get("review", {}).get("rating", 0)),
                        "sold_quantity": int(item.get("soldCountTotal", 0)),
                        "shop_name": item.get("merchantName", ""),
                        "url": full_url,
                        "image": image_url,
                        "source": "blibli"
                    })

            except Exception as e:
                # print(f"Skipping item due to error: {e}")
                continue

        df = pd.DataFrame(extracted)
        
        # Ensure numeric columns
        df['price_current'] = pd.to_numeric(df['price_current'], errors='coerce').fillna(0)
        df['price_original'] = pd.to_numeric(df['price_original'], errors='coerce').fillna(0)
        df['discount'] = pd.to_numeric(df['discount'], errors='coerce').fillna(0)
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
        df['sold_quantity'] = pd.to_numeric(df['sold_quantity'], errors='coerce').fillna(0)

        # Save
        os.makedirs(os.path.dirname(PROCESSED_FILE), exist_ok=True)
        df.to_csv(PROCESSED_FILE, index=False)
        print(f"[SUCCESS] Transformed {len(df)} items. Saved to {PROCESSED_FILE}")

    except Exception as e:
        print(f"Transform failed: {e}")

if __name__ == "__main__":
    transform_data()
