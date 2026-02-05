import os
import subprocess
import sys

def run_shopee_load():
    """
    ETL LOAD: Triggers the internal database pipeline for Shopee data.
    """
    print("--- ETL LOAD (Shopee): Syncing with Database ---")
    
    project_root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    pipeline_path = os.path.join(project_root, "pipeline", "run_pipeline.py")
    data_path = os.path.normpath(os.path.join(project_root, "data", "skincare_shopee_data_cleaned.csv"))
    
    if not os.path.exists(pipeline_path):
        print(f"Error: Pipeline script not found at {pipeline_path}")
        return

    if not os.path.exists(data_path):
        print(f"Error: Shopee cleaned data not found at {data_path}")
        return

    try:
        # Pass the Shopee data path to run_pipeline.py
        result = subprocess.run([sys.executable, pipeline_path, data_path], check=True, capture_output=True, text=True)
        print(result.stdout)
        print("--- ETL LOAD (Shopee) Finished Successfully ---")
    except subprocess.CalledProcessError as e:
        print(f"ETL LOAD (Shopee) Failed!")
        print(f"Exit Code: {e.returncode}")
        print(f"Error Output: {e.stderr}")
        print(f"Standard Output: {e.stdout}")

if __name__ == "__main__":
    run_shopee_load()
