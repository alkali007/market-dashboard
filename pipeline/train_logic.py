import pandas as pd
import os
import re

def train_from_labels():
    csv_path = r"c:\Users\Jan\Downloads\Dashboard_Market Research\market_dashboard\data\unknown_products_labeling.csv"
    extraction_path = r"c:\Users\Jan\Downloads\Dashboard_Market Research\market_dashboard\pipeline\src\extraction.py"
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    # Read CSV and handle potential empty values
    try:
        df = pd.read_csv(csv_path).fillna('')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    # Filter rows that have corrections
    labeled_brands = df[df['corrected_brand'] != '']
    labeled_types = df[df['corrected_product_type'] != '']
    
    print(f"Found {len(labeled_brands)} brand corrections and {len(labeled_types)} type corrections.")

    with open(extraction_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update BRAND_DICTIONARY
    brand_dict_match = re.search(r'BRAND_DICTIONARY = \{(.*?)\}', content, re.DOTALL)
    if brand_dict_match:
        current_dict_str = brand_dict_match.group(1)
        
        for _, row in labeled_brands.iterrows():
            brand = row['corrected_brand'].lower().strip()
            keywords = row.get('key_words_for_brands', '')
            
            if brand == 'unknown' or not brand: continue
            
            # Determine aliases
            aliases = [brand]
            if keywords:
                aliases.extend([k.strip().lower() for k in keywords.split(',') if k.strip()])
            aliases = sorted(list(set(aliases)))
            
            # Check if brand exists
            brand_pattern = rf'"{brand}": \[(.*?)\]'
            existing_match = re.search(brand_pattern, content)
            
            if existing_match:
                # Update aliases
                old_aliases_str = existing_match.group(1)
                old_aliases = [a.strip().strip('"').strip("'") for a in old_aliases_str.split(',') if a.strip()]
                combined = sorted(list(set(old_aliases + aliases)))
                new_aliases_str = ", ".join([f'"{a}"' for a in combined])
                content = content.replace(f'"{brand}": [{old_aliases_str}]', f'"{brand}": [{new_aliases_str}]')
            else:
                # Add new entry
                new_aliases_str = ", ".join([f'"{a}"' for a in aliases])
                new_entry = f'    "{brand}": [{new_aliases_str}],'
                # Insert inside the dict block
                current_dict_str = current_dict_str.rstrip() + "\n" + new_entry + "\n"
                # Refresh content for next brand
                content = re.sub(r'BRAND_DICTIONARY = \{.*?\}', f'BRAND_DICTIONARY = {{{current_dict_str}}}', content, flags=re.DOTALL)
                
        print("Updated Brand Dictionary.")

    # 2. Update PRODUCT_TYPES
    for _, row in labeled_types.iterrows():
        cat = row['corrected_product_type'].lower().strip()
        keywords_raw = row.get('key_words_for_product', '')
        
        if cat == 'unknown' or not cat: continue
        
        # Determine keywords
        keywords = []
        if keywords_raw:
            keywords = [k.strip().lower() for k in keywords_raw.split(',') if k.strip()]
        else:
            title = row['title_raw'].lower()
            words = [w for w in re.findall(r'\w+', title) if len(w) > 3]
            if words: keywords = [words[0]]

        # Check if category exists
        cat_pattern = rf'"{cat}": \{{.*?"keywords": \[(.*?)\]'
        cat_match = re.search(cat_pattern, content, re.DOTALL)
        
        if cat_match:
            old_keywords_str = cat_match.group(1)
            old_keywords = [k.strip().strip('"').strip("'") for k in old_keywords_str.split(',') if k.strip()]
            combined = sorted(list(set(old_keywords + keywords)))
            new_keywords_str = ", ".join([f'"{k}"' for k in combined])
            
            # Use string splice to avoid issues with overlap if multiple keywords added to same cat
            # We re-find every time because content changes
            curr_match = re.search(rf'"{cat}": \{{.*?"keywords": \[(.*?)\]', content, re.DOTALL)
            if curr_match:
                start, end = curr_match.span(1)
                content = content[:start] + new_keywords_str + content[end:]
        else:
            # Create NEW category
            new_keywords_str = ", ".join([f'"{k}"' for k in keywords])
            new_cat_block = f'    "{cat}": {{\n        "keywords": [{new_keywords_str}],\n        "priority": 2\n    }},'
            
            types_match = re.search(r'PRODUCT_TYPES = \{(.*?)\}', content, re.DOTALL)
            if types_match:
                inner_types = types_match.group(1)
                updated_inner = inner_types.rstrip() + "\n" + new_cat_block + "\n"
                content = content.replace(inner_types, updated_inner)
                print(f"Created new category: {cat}")

    with open(extraction_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Training complete. Run the pipeline to see improvements.")

if __name__ == "__main__":
    train_from_labels()
