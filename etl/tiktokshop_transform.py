import os
import json
import pandas as pd
import re

def transform_item(item):
    """
    Transform raw scraped strings into clean data types
    matching beauty_data_cleaned.csv structure.
    """
    # 1. Clean Price Current
    price_curr = str(item.get('price_current', '0'))
    price_curr = int(re.sub(r'[^\d]', '', price_curr)) if price_curr != '0' and price_curr != 'N/A' else 0
    
    # 2. Clean Price Original
    price_orig = item.get('price_original')
    if price_orig and price_orig != 'N/A':
        price_orig = int(re.sub(r'[^\d]', '', str(price_orig)))
    else:
        price_orig = price_curr # fallback to current if no original

    # 3. Clean Discount
    disc = item.get('discount')
    if disc and disc != 'N/A':
        # Handles "64%" -> 64
        disc_val = re.sub(r'[^\d]', '', str(disc))
        disc = int(disc_val) if disc_val else 0
    else:
        disc = 0

    # 4. Clean Rating
    rating = item.get('rating', '0')
    try:
        rating = float(rating)
    except:
        rating = 0.0

    # 5. Clean Sold Quantity (Handles "2.2M", "10K", etc)
    sold = str(item.get('sold_quantity', '0')).lower()
    sold = sold.replace('sold', '').replace('terjual',').replace('+', '').replace(' ','').strip()
    
    sold_val = 0
    if 'm' in sold:
        num = re.findall(r'[\d\.]+', sold)
        if num: sold_val = int(float(num[0]) * 1000000)
    elif 'k' in sold:
        num = re.findall(r'[\d\.]+', sold)
        if num: sold_val = int(float(num[0]) * 1000)
    else:
        num = re.findall(r'[\d\.]+', sold)
        if num: sold_val = int(float(num[0]))
    
    return {
        "name": item.get('name', 'N/A'),
        "url": item.get('url', 'N/A'),
        "image": item.get('image', 'N/A'),
        "rating": rating,
        "sold_quantity": sold_val,
        "price_current": price_curr,
        "price_original": price_orig,
        "discount": disc
    }

def run_transform():
    """
    ETL TRANSFORM: Reads all raw JSON files and produces cleaned CSVs.
    """
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    raw_dir = os.path.join(project_root, "data", "raw")
    out_dir = os.path.join(project_root, "data")
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(raw_dir):
        print(f"No raw data found in {raw_dir}")
        return

    for filename in os.listdir(raw_dir):
        if filename.endswith("_raw.json"):
            category = filename.replace("_raw.json", "")
            raw_path = os.path.join(raw_dir, filename)
            
            print(f"[{category}] TRANSFORMing {raw_path}...")
            
            with open(raw_path, "r", encoding='utf-8') as f:
                raw_data = json.load(f)
            
            transformed_data = [transform_item(item) for item in raw_data]
            df = pd.DataFrame(transformed_data)
            
            # Save to CSV
            out_path = os.path.join(out_dir, f"{category}_data_cleaned.csv")
            df.to_csv(out_path, index=False)
            print(f"[{category}] TRANSFORM finished. Saved {len(df)} items to {out_path}")

if __name__ == "__main__":
    run_transform()
