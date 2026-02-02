import os
import psycopg2
from dotenv import load_dotenv

def apply_schema():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(env_path)
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "YOUR-PASSWORD" in db_url:
        print("Error: DATABASE_URL not set or contains placeholder.")
        return

    schema_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'schema.sql')
    
    print(f"Applying schema from {schema_path}...")
    
    try:
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute(schema_sql)
        conn.commit()
        print("Schema applied successfully!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Failed to apply schema: {e}")

if __name__ == "__main__":
    apply_schema()
