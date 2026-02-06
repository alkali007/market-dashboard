import os
import json
import pandas as pd
import re

def transform_lazada_item(item):
    """
    Transform raw Lazada item data into clean format.
    """
    # 1. Name
    name = item.get('name', 'N/A')
    
    # 2. URL
    url = item.get('itemUrl', 'N/A')
    if url.startswith('//'):
        url = 'https:' + url
    
    # 3. Image
    image_url = item.get('image', 'N/A')
    
    # 4. Rating
    rating_raw = item.get('ratingScore', 0)
    try:
        rating = float(rating_raw) if rating_raw else 0.0
    except (ValueError, TypeError):
        rating = 0.0
    
    # 5. Sold Quantity
    # Format: "42.2K Terjual"
    sold_str = item.get('itemSoldCntShow', '0')
    sold_val = 0
    if sold_str:
        # Extract numbers and multipliers
        match = re.search(r'([\d\.]+)\s*([KkMm])?\s*Terjual', sold_str)
        if match:
            val = float(match.group(1))
            multiplier = match.group(2)
            if multiplier and multiplier.upper() == 'K':
                val *= 1000
            elif multiplier and multiplier.upper() == 'M':
                val *= 1000000
            sold_val = int(val)
            
    # 6. Prices
    price_curr_raw = item.get('price', 0)
    try:
        price_curr = int(float(price_curr_raw))
    except (ValueError, TypeError):
        price_curr = 0
        
    price_orig_raw = item.get('originalPrice', 0)
    try:
        price_orig = int(float(price_orig_raw)) if price_orig_raw else price_curr
    except (ValueError, TypeError):
        price_orig = price_curr
        
    # 7. Discount
    # Format: "61% Off"
    disc_str = item.get('discount', '0')
    discount = 0
    if disc_str and '%' in disc_str:
        disc_match = re.search(r'(\d+)', disc_str)
        if disc_match:
            discount = int(disc_match.group(1))
    
    return {
        "name": name,
        "url": url,
        "image": image_url,
        "rating": rating,
        "sold_quantity": sold_val,
        "price_current": price_curr,
        "price_original": price_orig,
        "discount": discount,
        "source": "lazada"
    }

def run_lazada_transform():
    """
    ETL TRANSFORM: Reads Lazada JSON and produces cleaned CSV.
    """
    project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    raw_path = os.path.join(project_root, "data", "raw", "lazada_raw.json")
    out_dir = os.path.join(project_root, "data")
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(raw_path):
        print(f"Lazada raw data not found at {raw_path}")
        return

    print(f"[Lazada] TRANSFORMing {raw_path}...")
    try:
        with open(raw_path, "r", encoding='utf-8') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        all_transformed = []
        
        for item in items:
            all_transformed.append(transform_lazada_item(item))
            
        if all_transformed:
            df = pd.DataFrame(all_transformed)
            # Drop duplicates based on URL
            df = df.drop_duplicates(subset=['url'])
            
            # Save to CSV
            out_path = os.path.join(out_dir, "skincare_lazada_data_cleaned.csv")
            df.to_csv(out_path, index=False)
            print(f"[Lazada] TRANSFORM finished. Saved {len(df)} items to {out_path}")
        else:
            print("No items found in Lazada raw data.")
            
    except Exception as e:
        print(f"Error processing Lazada data: {e}")

if __name__ == "__main__":
    run_lazada_transform()
