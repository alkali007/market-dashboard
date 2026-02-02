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

def truncate():
    print("Truncating database...")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("TRUNCATE raw_products CASCADE;")
        conn.commit()
        print("Database truncated successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    truncate()
