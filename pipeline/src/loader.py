import os
import csv
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode
import psycopg2
from psycopg2.extras import execute_values

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    
    if db_url and '?' in db_url:
        parsed = urlparse(db_url)
        query_params = parse_qs(parsed.query)
        unsupported = ['statement_cache_mode', 'default_query_exec_mode']
        for param in unsupported:
            query_params.pop(param, None)
        new_query = urlencode(query_params, doseq=True)
        db_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if new_query:
            db_url += f"?{new_query}"
    
    return psycopg2.connect(db_url)

def export_unknown_products(df_raw, df_enriched, output_dir="../../data"):
    unknown_rows = []
    
    # Since df_enriched has all data, we filter for unknown
    for idx, row in df_enriched.iterrows():
        brand = row.get('brand', 'unknown')
        product_type = row.get('product_type', 'unknown')
        
        if brand == 'unknown' or product_type == 'unknown':
            unknown_rows.append({
                'content_hash': row['content_hash'],
                'title_raw': row.get('name', row.get('title_raw', '')),
                'current_brand': brand,
                'current_product_type': product_type,
                'corrected_brand': '',
                'corrected_product_type': ''
            })
    
    if unknown_rows:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.normpath(os.path.join(script_dir, output_dir, "unknown_products_labeling.csv"))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        fieldnames = [
            'content_hash', 'title_raw', 
            'current_brand', 'current_product_type',
            'corrected_brand', 'corrected_product_type',
            'key_words_for_brands', 'key_words_for_product'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unknown_rows)
        
        print(f"Exported {len(unknown_rows)} unknown products to {output_path}")
        return len(unknown_rows)
    return 0

def load_data(df_raw, df_enriched):
    """
    Load extracted data into Supabase.
    Ensures that NO 'unknown' brands or types are added to the database.
    """
    print("Loading data into Database...")
    
    # Export unknown products for manual labeling
    export_unknown_products(df_raw, df_enriched)
    
    # FILTER: Only keep high-confidence/known items
    # Since in run_pipeline both are the same DF, we just filter it
    df_final = df_enriched[
        (df_enriched['brand'] != 'unknown') & 
        (df_enriched['product_type'] != 'unknown')
    ].copy()
    
    print(f"Finalizing {len(df_final)} records for database insertion...")

    if len(df_final) == 0:
        print("No valid records (known brand/type) to load. Database remains untouched.")
        return

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Insert Raw Products (Filtered)
        raw_rows = []
        for idx, row in df_final.iterrows():
            discount_val = float(row['discount'])
            if discount_val > 1.0:
                discount_val = discount_val / 100.0
            
            raw_rows.append((
                row['content_hash'],
                row['name'],
                row['sold_quantity'],
                row['price_current'],
                row['price_original'],
                discount_val,
                row['rating'],
                row.get('url', ''),
                row.get('image', '')
            ))
            
        insert_raw_query = """
            INSERT INTO raw_products (content_hash, title_raw, quantity_sold, price_current, price_original, discount, rating, url, image_url)
            VALUES %s
            ON CONFLICT (content_hash) DO UPDATE SET
                quantity_sold = EXCLUDED.quantity_sold,
                price_current = EXCLUDED.price_current,
                price_original = EXCLUDED.price_original,
                discount = EXCLUDED.discount,
                rating = EXCLUDED.rating,
                image_url = EXCLUDED.image_url,
                updated_at = NOW()
            RETURNING id, content_hash;
        """
        
        execute_values(cur, insert_raw_query, raw_rows)
        
        # Mapping for enriched link
        cur.execute("SELECT content_hash, id FROM raw_products WHERE content_hash IN %s", (tuple(df_final['content_hash']),))
        mapping = dict(cur.fetchall())
        
        # 2. Insert Enriched Products
        enriched_rows = []
        for idx, row in df_final.iterrows():
            raw_id = mapping.get(row['content_hash'])
            if raw_id:
                effective = float(row['price_current'])
                brand_conf = row.get('brand_confidence', 0.0)
                type_conf = row.get('product_type_confidence', 0.0)
                overall_conf = (brand_conf * 0.6) + (type_conf * 0.4)
                
                enriched_rows.append((
                    str(raw_id),
                    row['title_cleaned'],
                    row['brand'],
                    row['product_type'],
                    effective,
                    brand_conf,
                    type_conf,
                    overall_conf
                ))
        
        insert_enriched_query = """
            INSERT INTO enriched_products (raw_product_id, title_cleaned, brand, product_type, price_effective, brand_confidence, product_type_confidence, enrichment_confidence)
            VALUES %s
            ON CONFLICT (raw_product_id) DO UPDATE SET
                title_cleaned = EXCLUDED.title_cleaned,
                brand = EXCLUDED.brand,
                product_type = EXCLUDED.product_type,
                enriched_at = NOW();
        """
        
        if enriched_rows:
            execute_values(cur, insert_enriched_query, enriched_rows)
            
        conn.commit()
        print("Database update successful.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error loading data: {e}")
        raise
    finally:
        cur.close()
        conn.close()
