import os
import time
import asyncio
from tiktokshop_scraper import main as run_extract
from tiktokshop_transform import run_transform
from tiktokshop_load import run_load
from r2_utils import upload_raw_to_r2

def main():
    """
    Main Orchestrator for TikTok Shop ETL Process.
    """
    start_time = time.time()
    print("==========================================")
    print("STARTING TIKTOK SHOP ETL PROCESS")
    print("==========================================")

    # 0. PRE-CLEANUP (Avoid Ghost Data)
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    raw_dir = os.path.join(project_root, "data", "raw")
    if os.path.exists(raw_dir):
        import shutil
        print(f"Cleaning old raw data in {raw_dir}...")
        for f in os.listdir(raw_dir):
            os.remove(os.path.join(raw_dir, f))

    # 1. EXTRACT
    print("\n[PHASE 1] EXTRACT: Running Scraper...")
    try:
        asyncio.run(run_extract())
    except Exception as e:
        print(f"EXTRACT Phase encountered an error: {e}")
        # Check if we at least got some data
        raw_files = [f for f in os.listdir(raw_dir) if f.endswith("_raw.json")]
        if not raw_files:
            print("No raw data extracted. Stopping pipeline.")
            return
        print(f"Extraction had issues, but {len(raw_files)} raw files found. Continuing...")

    # 1.5. CLOUD BACKUP (Optional Phase)
    print("\n[PHASE 1.5] BACKUP: Uploading Raw Data to R2...")
    try:
        raw_files = [f for f in os.listdir(raw_dir) if f.endswith("_raw.json")]
        for filename in raw_files:
            category = filename.replace("_raw.json", "")
            file_path = os.path.join(raw_dir, filename)
            upload_raw_to_r2(category, file_path)
    except Exception as e:
        print(f"BACKUP Phase skipped or encountered error: {e}")
        # We don't return here because backup is auxiliary, not critical for the next steps

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
