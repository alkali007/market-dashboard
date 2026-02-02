import pandas as pd
import hashlib
import uuid

REQUIRED_COLUMNS = ['name', 'url', 'image', 'rating', 'sold_quantity', 'price_current', 'price_original', 'discount']

from urllib.parse import urlparse, urlunparse, parse_qsl

def generate_content_hash(row):
    """
    Create a stable unique string based on Identity (Name + Cleaned URL).
    Ensures that even if price or sales change, the ID stays the same.
    Strips tracking params to prevent duplicates from different sessions.
    """
    url = str(row['url'])
    parsed = urlparse(url)
    # Remove common tracking parameters
    tracking_params = {'tm', 'spm', 'region', 'source', 'click_id', '_', 'token'}
    query_params = parse_qsl(parsed.query)
    filtered_query = [(k, v) for k, v in query_params if k.lower() not in tracking_params]
    
    # Reconstruct cleaned URL
    cleaned_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        '', # We often strip query entirely if we want maximum dedupe, but let's keep non-tracking ones
        parsed.fragment
    ))
    
    # If there were valid non-tracking params, we could re-add them, 
    # but for Shop IDs, the path usually contains the product ID.
    # Let's keep it simple: Name + Base URL path
    content = f"{row['name']}{cleaned_url}"
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
