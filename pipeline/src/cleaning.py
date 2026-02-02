import re
import unicodedata
import pandas as pd

# Comprehensive noise token removal from Phase 1.1
NOISE_PATTERNS = [
    # Bracket-enclosed tags (most aggressive noise)
    r'\[.*?\]',  # [BPOM], [FLASH SALE], [Official], [Buy 2 Get 1], etc.
    r'\(.*?BPOM.*?\)',  # (BPOM), (️BPOM)
    r'\(.*?COD.*?\)',  # (COD READY)
    
    # Promotional phrases (case-insensitive)
    r'(?i)\b(ready\s*stock|beli\s*\d+\s*gratis\s*\d+|flash\s*sale|super\s*brand\s*day)\b',
    r'(?i)\b(exclusive|limited|special|terlaris|viral|best\s*seller|cod)\b',
    r'(?i)\b(original|authentic|preloved|new|bekas)\b',
    
    # Free gift indicators
    r'(?i)\b(free|gratis|bonus|include|termasuk)\b.*?(?=\||$)',
    
    # Emoji and special characters
    r'[️⭐✨🔥💯❤]',
    
    # Excessive punctuation
    r'[!]{2,}',  # Multiple exclamation marks
    r'[\-]{2,}',  # Multiple dashes
]

def remove_noise(title: str) -> str:
    """Remove promotional tags and noise while preserving semantic content."""
    if not isinstance(title, str): return ""
    cleaned = title
    for pattern in NOISE_PATTERNS:
        cleaned = re.sub(pattern, ' ', cleaned)
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def normalize_unicode(text: str) -> str:
    """Convert to NFC form, strip accents, handle special cases."""
    if not isinstance(text, str): return ""
    # Normalize to NFC (canonical composition)
    text = unicodedata.normalize('NFC', text)
    # Remove zero-width characters
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    return text

def smart_case_normalize(text: str) -> tuple:
    """Return both lowercase (for matching) and display-friendly (for storage)."""
    # For matching: lowercase
    match_text = text.lower()
    # For display: title case with brand-aware exceptions
    display_text = text.title()
    # Fix known brand casing issues
    display_text = re.sub(r'\bMs\s+Glow\b', 'MS Glow', display_text, flags=re.IGNORECASE)
    display_text = re.sub(r'\bGlad2glow\b', 'glad2glow', display_text, flags=re.IGNORECASE)
    return match_text, display_text

def normalize_data(df):
    print("Normalizing data...")
    # Apply enhanced cleaning
    df['name'] = df['name'].fillna("")
    df['title_cleaned_temp'] = df['name'].apply(normalize_unicode).apply(remove_noise)
    
    # We will split into match and display versions in extraction or just here
    # For now, let's keep title_cleaned as the display version
    match_and_display = df['title_cleaned_temp'].apply(smart_case_normalize)
    df['title_match'] = match_and_display.apply(lambda x: x[0])
    df['title_cleaned'] = match_and_display.apply(lambda x: x[1])
    
    # Clean numeric fields
    df['sold_quantity'] = pd.to_numeric(df['sold_quantity'], errors='coerce').fillna(0)
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0.0)
    
    return df
