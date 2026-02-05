import os
import sys
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import ingestion, cleaning, extraction, loader

def main():
    # Load .env
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    # 1. Ingest
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
        print(f"Using provided data path: {data_path}")
    else:
        # Default path
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'beauty_data_cleaned.csv')
        print(f"Using default data path: {data_path}")
        
    df = ingestion.ingest_data(data_path)
    
    if df is None:
        print("Pipeline aborted.")
        return

    # 2. Clean
    df = cleaning.normalize_data(df)
    
    # 3. Extract/Enrich
    df = extraction.enrich_data(df)
    
    # 4. Load
    try:
        loader.load_data(df, df) # We pass df twice because in this flow they are the same object with added columns
    except Exception as e:
        print(f"Pipeline Failed at Load Step: {e}")
        return

    print("Pipeline Finished Successfully.")

if __name__ == "__main__":
    main()
