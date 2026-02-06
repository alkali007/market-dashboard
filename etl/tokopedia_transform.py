import os
import json
import pandas as pd
import re

def transform_tokopedia_item(item_data):
    """
    Transform raw Tokopedia API item data into clean format.
    MATCHING SHOPEE SCHEMA:
    name, url, image, rating, sold_quantity, price_current, price_original, discount, source
    """
    
    # 1. Name
    name = item_data.get('name', 'N/A')
    
    # 2. URL
    url = item_data.get('url', 'N/A')
    
    # 3. Image
    media = item_data.get('mediaURL', {})
    image_url = media.get('image', 'N/A')
    
    # 4. Rating
    try:
        rating = float(item_data.get('rating', 0.0))
    except (ValueError, TypeError):
        rating = 0.0
    
    # 5. Sold Quantity
    # Logic: "6 terjual", "100+ terjual", "1 rb+ terjual"
    label_groups = item_data.get('labelGroups', [])
    sold_str = "0"
    for label in label_groups:
        if label.get('position') == 'ri_product_credibility':
            title = label.get('title', '')
            if 'terjual' in title.lower():
                sold_str = title
                break
    
    # Clean sold string (e.g., "10 rb+ terjual" -> 10000)
    sold_clean = sold_str.lower().replace('terjual', '').replace('+', '').replace(',', '.').strip()
    multiplier = 1
    if 'rb' in sold_clean:
        multiplier = 1000
        sold_clean = sold_clean.replace('rb', '').strip()
    elif 'jt' in sold_clean:
        multiplier = 1000000
        sold_clean = sold_clean.replace('jt', '').strip()
        
    try:
        sold_val = int(float(sold_clean) * multiplier)
    except (ValueError, TypeError):
        sold_val = 0

    # 6. Prices
    price_dict = item_data.get('price', {})
    price_curr = int(price_dict.get('number', 0))
    
    original_price_str = price_dict.get('original', '')
    if original_price_str:
        # e.g., "Rp100.000" -> 100000
        clean_orig = re.sub(r'[^\d]', '', original_price_str)
        price_orig = int(clean_orig) if clean_orig else price_curr
    else:
        price_orig = price_curr

    # 7. Discount
    discount = int(price_dict.get('discountPercentage', 0))

    return {
        "name": name,
        "url": url,
        "image": image_url,
        "rating": rating,
        "sold_quantity": sold_val,
        "price_current": price_curr,
        "price_original": price_orig,
        "discount": discount,
        "source": "tokopedia"
    }

def run_tokopedia_transform():
    """
    ETL TRANSFORM: Reads Tokopedia JSON file and produces cleaned CSV.
    """
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    raw_path = os.path.join(project_root, "data", "raw", "tokopedia_raw.json")
    out_dir = os.path.join(project_root, "data")
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(raw_path):
        print(f"Tokopedia raw data {raw_path} does not exist.")
        return

    print(f"[Tokopedia] TRANSFORMing {raw_path}...")
    all_transformed = []
    
    try:
        with open(raw_path, "r", encoding='utf-8') as f:
            data = json.load(f)
            
        products = []
        if isinstance(data, dict):
            products = data.get("products", [])
        elif isinstance(data, list):
            products = data
            
        print(f"Found {len(products)} products to transform...")
        
        for item in products:
            if isinstance(item, dict):
                all_transformed.append(transform_tokopedia_item(item))
                
    except Exception as e:
        print(f"Error processing Tokopedia raw data: {e}")

    if all_transformed:
        df = pd.DataFrame(all_transformed)
        # Drop duplicates based on URL
        df = df.drop_duplicates(subset=['url'])
        
        # Save to CSV
        out_path = os.path.join(out_dir, "skincare_tokopedia_data_cleaned.csv")
        df.to_csv(out_path, index=False)
        print(f"[Tokopedia] TRANSFORM finished. Saved {len(df)} items to {out_path}")
    else:
        print("No Tokopedia data found to transform.")

if __name__ == "__main__":
    run_tokopedia_transform()
