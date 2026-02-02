import os
import psycopg2
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

db_url = os.getenv("DATABASE_URL")

print(f"Testing connection to: {db_url}")

try:
    conn = psycopg2.connect(db_url)
    print("Successfully connected to the database!")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(f"Database version: {cur.fetchone()}")
    cur.close()
    conn.close()
except Exception as e:
    print("Failed to connect!")
    print(e)
