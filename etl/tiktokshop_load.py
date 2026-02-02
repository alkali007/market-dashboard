import os
import subprocess
import sys

def run_load():
    """
    ETL LOAD: Triggers the internal database pipeline to sync the cleaned CSVs.
    """
    print("--- ETL LOAD: Syncing with Database ---")
    
    # Path to the main pipeline script (now one level up from etl/)
    pipeline_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pipeline", "run_pipeline.py")
    
    if not os.path.exists(pipeline_path):
        print(f"Error: Pipeline script not found at {pipeline_path}")
        return

    try:
        # We use subprocess to run the pipeline to ensure it uses the correct environment/imports
        # Since run_pipeline.py expects to be run from its directory often, or handles its own path
        result = subprocess.run([sys.executable, pipeline_path], check=True, capture_output=True, text=True)
        print(result.stdout)
        print("--- ETL LOAD Finished Successfully ---")
    except subprocess.CalledProcessError as e:
        print(f"ETL LOAD Failed!")
        print(f"Exit Code: {e.returncode}")
        print(f"Error Output: {e.stderr}")
        print(f"Standard Output: {e.stdout}")

if __name__ == "__main__":
    run_load()
