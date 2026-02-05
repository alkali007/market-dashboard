import os
import json
import pandas as pd
import re

def transform_shopee_item(item_data):
    """
    Transform raw Shopee API item data into clean format.
    """
    item = item_data.get('item_basic', {})
    
    # 1. Name
    name = item.get('name', 'N/A')
    
    # 2. URL
    shopid = item.get('shopid')
    itemid = item.get('itemid')
    url = f"https://shopee.co.id/product/{shopid}/{itemid}" if shopid and itemid else 'N/A'
    
    # 3. Image
    image_id = item.get('image', '')
    image_url = f"https://down-id.img.susercontent.com/file/{image_id}" if image_id else 'N/A'
    
    # 4. Rating
    rating = item.get('item_rating', {}).get('rating_star', 0.0)
    
    # 5. Sold Quantity
    sold_val = item.get('historical_sold', 0)
    
    # 6. Prices (Shopee prices are usually multiplied by 100,000)
    price_curr_raw = item.get('price', 0)
    price_curr = int(price_curr_raw / 100000)
    
    price_orig_raw = item.get('price_before_discount')
    if price_orig_raw and price_orig_raw > 0:
        price_orig = int(price_orig_raw / 100000)
    else:
        price_orig = price_curr
        
    # 7. Discount
    disc_str = item.get('discount', '0') # e.g. "-78%"
    if disc_str and '%' in disc_str:
        disc_val = re.sub(r'[^\d]', '', disc_str)
        discount = int(disc_val) if disc_val else 0
    else:
        discount = 0
    
    return {
        "name": name,
        "url": url,
        "image": image_url,
        "rating": rating,
        "sold_quantity": sold_val,
        "price_current": price_curr,
        "price_original": price_orig,
        "discount": discount,
        "source": "shopee"
    }

def run_shopee_transform():
    """
    ETL TRANSFORM: Reads Shopee JSON files and produces cleaned CSVs.
    """
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    shopee_dir = os.path.join(project_root, "shopee_data")
    out_dir = os.path.join(project_root, "data")
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.exists(shopee_dir):
        print(f"Shopee data directory {shopee_dir} does not exist.")
        return

    all_transformed = []
    
    # Iterate through all response_*.json files
    for filename in os.listdir(shopee_dir):
        if filename.startswith("response_") and filename.endswith(".json"):
            file_path = os.path.join(shopee_dir, filename)
            print(f"[Shopee] TRANSFORMing {file_path}...")
            
            try:
                with open(file_path, "r", encoding='utf-8') as f:
                    data = json.load(f)
                
                items = data.get('items', [])
                if items:
                    for item in items:
                        # Some items might be ads or different structures
                        if isinstance(item, dict) and 'item_basic' in item:
                            all_transformed.append(transform_shopee_item(item))
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    if all_transformed:
        df = pd.DataFrame(all_transformed)
        # Drop duplicates based on URL
        df = df.drop_duplicates(subset=['url'])
        
        # Save to CSV
        out_path = os.path.join(out_dir, "skincare_shopee_data_cleaned.csv")
        df.to_csv(out_path, index=False)
        print(f"[Shopee] TRANSFORM finished. Saved {len(df)} items to {out_path}")
    else:
        print("No Shopee data found to transform.")

if __name__ == "__main__":
    run_shopee_transform()
