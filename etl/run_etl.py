import os
import time
import asyncio
from tiktokshop_scraper import main as run_tiktok_extract
from tiktokshop_transform import run_transform as run_tiktok_transform
from tiktokshop_load import run_load as run_tiktok_load
from shopee_scraper import main as run_shopee_extract
from shopee_transform import run_shopee_transform
from shopee_load import run_shopee_load
from tokopedia_scraper import run_scraper as run_tokopedia_extract
from tokopedia_transform import run_tokopedia_transform
from tokopedia_load import run_tokopedia_load
from r2_utils import upload_raw_to_r2

import sys

def main():
    """
    Main Orchestrator for Multi-Platform ETL Process.
    """
    start_time = time.time()
    
    target = sys.argv[1].lower() if len(sys.argv) > 1 else 'all'
    
    print("==========================================")
    print(f"STARTING {target.upper()} ETL PROCESS")
    print("==========================================")

    # 0. PRE-CLEANUP (Avoid Ghost Data)
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    raw_dir = os.path.join(project_root, "data", "raw")
    shopee_raw_dir = os.path.join(project_root, "shopee_data")
    tokopedia_raw_path = os.path.join(raw_dir, "tokopedia_raw.json")
    
    # --- TIKTOK SHOP WORKFLOW ---
    if target in ['tiktok', 'all']:
        print("\n[TIKTOK SHOP] Starting Workflow...")
        # Clean TikTok Raw
        if os.path.exists(raw_dir):
            print(f"Cleaning old TikTok raw data in {raw_dir}...")
            for f in os.listdir(raw_dir):
                if f.endswith(".json") and "tokopedia" not in f: # Protect Tokopedia file
                    os.remove(os.path.join(raw_dir, f))
        try:
            asyncio.run(run_tiktok_extract())
            
            # Upload to R2
            if os.path.exists(raw_dir):
                print(f"[TIKTOK SHOP] R2: Syncing raw data to Cloud Storage...")
                for f in os.listdir(raw_dir):
                    if f.endswith(".json") and "tokopedia" not in f:
                        upload_raw_to_r2("tiktok", os.path.join(raw_dir, f))
            
            run_tiktok_transform()
            run_tiktok_load()
        except Exception as e:
            print(f"TikTok Workflow failed: {e}")

    # --- SHOPEE WORKFLOW ---
    if target in ['shopee', 'all']:
        print("\n[SHOPEE] Starting Workflow...")
        # Clean Shopee Raw
        if os.path.exists(shopee_raw_dir):
            print(f"Cleaning old Shopee raw data in {shopee_raw_dir}...")
            for f in os.listdir(shopee_raw_dir):
                if f.startswith("response_") and f.endswith(".json"):
                    os.remove(os.path.join(shopee_raw_dir, f))
        try:
            asyncio.run(run_shopee_extract())
            
            # Upload to R2
            if os.path.exists(shopee_raw_dir):
                print(f"[SHOPEE] R2: Syncing raw data to Cloud Storage...")
                for f in os.listdir(shopee_raw_dir):
                    if f.startswith("response_") and f.endswith(".json"):
                        upload_raw_to_r2("shopee", os.path.join(shopee_raw_dir, f))
            
            run_shopee_transform()
            run_shopee_load()
        except Exception as e:
            print(f"Shopee Workflow failed: {e}")

    # --- TOKOPEDIA WORKFLOW ---
    if target in ['tokopedia', 'all']:
        print("\n[TOKOPEDIA] Starting Workflow...")
        # Note: We do NOT delete tokopedia_raw.json as requested, to allow appending.
        
        try:
            asyncio.run(run_tokopedia_extract())
            
            # Upload to R2
            if os.path.exists(tokopedia_raw_path):
                print(f"[TOKOPEDIA] R2: Syncing raw data to Cloud Storage...")
                upload_raw_to_r2("tokopedia", tokopedia_raw_path)
            
            run_tokopedia_transform()
            run_tokopedia_load()
        except Exception as e:
            print(f"Tokopedia Workflow failed: {e}")

    total_time = time.time() - start_time
    print("\n==========================================")
    print(f"ETL PROCESS ({target.upper()}) COMPLETED IN {total_time:.2f} SECONDS")
    print("==========================================")

if __name__ == "__main__":
    main()
