import os
import time
from tiktokshop_scraper import main as run_extract
from tiktokshop_transform import run_transform
from tiktokshop_load import run_load

def main():
    """
    Main Orchestrator for TikTok Shop ETL Process.
    """
    start_time = time.time()
    print("==========================================")
    print("STARTING TIKTOK SHOP ETL PROCESS")
    print("==========================================")

    # 1. EXTRACT
    print("\n[PHASE 1] EXTRACT: Running Scraper...")
    try:
        run_extract()
    except Exception as e:
        print(f"EXTRACT Phase Failed: {e}")
        return

    # 2. TRANSFORM
    print("\n[PHASE 2] TRANSFORM: Cleaning and Processing Data...")
    try:
        run_transform()
    except Exception as e:
        print(f"TRANSFORM Phase Failed: {e}")
        return

    # 3. LOAD
    print("\n[PHASE 3] LOAD: Importing to Database...")
    try:
        run_load()
    except Exception as e:
        print(f"LOAD Phase Failed: {e}")
        return

    total_time = time.time() - start_time
    print("\n==========================================")
    print(f"ETL PROCESS COMPLETED IN {total_time:.2f} SECONDS")
    print("==========================================")

if __name__ == "__main__":
    main()
