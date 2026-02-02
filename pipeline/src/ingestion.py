import pandas as pd
import hashlib
import uuid

REQUIRED_COLUMNS = ['name', 'url', 'image', 'rating', 'sold_quantity', 'price_current', 'price_original', 'discount']

def generate_content_hash(row):
    # Create a stable unique string based on Identity (Name + URL)
    # This ensures that even if price or sales change, the ID stays the same.
    content = f"{row['name']}{row['url']}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def ingest_data(file_path):
    print(f"Loading data from {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

    # Validate columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        print(f"Missing columns: {missing}")
        return None

    # Add system IDs and Hashes
    df['content_hash'] = df.apply(generate_content_hash, axis=1)
    
    # Simple deduplication based on hash
    original_count = len(df)
    df = df.drop_duplicates(subset=['content_hash'])
    print(f"Ingested {len(df)} records (dropped {original_count - len(df)} duplicates)")
    
    return df
