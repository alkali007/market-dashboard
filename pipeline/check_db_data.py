import os
import psycopg2
from urllib.parse import urlparse, parse_qs, urlencode
from dotenv import load_dotenv

def get_db_connection():
    load_dotenv()
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

def check_data():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        print("Checking Brand Performance from DB:")
        cur.execute("SELECT brand, SUM(quantity_sold), SUM(revenue_proxy) FROM analytics_master GROUP BY brand ORDER BY SUM(revenue_proxy) DESC LIMIT 5;")
        for row in cur.fetchall():
            print(f"  Brand: {row[0]}, Units: {row[1]}, Revenue: {row[2]}")
            
        print("\nChecking Product Type Performance from DB:")
        cur.execute("SELECT product_type, SUM(quantity_sold), SUM(revenue_proxy) FROM analytics_master GROUP BY product_type ORDER BY SUM(revenue_proxy) DESC LIMIT 5;")
        for row in cur.fetchall():
            print(f"  Type: {row[0]}, Units: {row[1]}, Revenue: {row[2]}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_data()
