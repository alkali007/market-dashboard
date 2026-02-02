
import re
from thefuzz import fuzz

# Expanded dictionary with common variants from Phase 2.1
BRAND_DICTIONARY = {
    "wardah": ["wardah", "warda", "wardha"],
    "somethinc": ["somethinc", "something", "somethin"],
    "scarlett": ["scarlett", "scarlet", "scarlette"],
    "ms glow": ["ms glow", "msg low", "msglow", "ms-glow"],
    "avoskin": ["avoskin", "avo skin"],
    "emina": ["emina", "eminna"],
    "skintific": ["skintific", "skintifik", "skintifick"],
    "whitelab": ["whitelab", "white lab", "whitelabs"],
    "azarine": ["azarine", "azarin"],
    "npure": ["npure", "n pure", "n-pure"],
    "ponds": ["ponds", "pond's", "pond"],
    "garnier": ["garnier", "garner"],
    "nivea": ["nivea", "niveia"],
    "vaseline": ["vaseline", "vaselin"],
    "biore": ["biore", "bioré"],
    "hadalabo": ["hadalabo", "hada labo", "hada-labo"],
    "implora": ["implora", "impora"],
    "viva": ["viva"],
    "glad2glow": ["glad2glow", "glow&be", "glowbe", "glad to glow"],
    "purbasari": ["purbasari", "purba sari"],
    "hanasui": ["hanasui", "hana sui"],
    "omg": ["omg", "o.m.g"],
    "skin1004": ["skin1004", "skin 1004"],
    "pixy": ["pixy", "pixie"],
    "brasov": ["brasov"],
    "misonells": ["misonells"],
    "posh": ["posh"],
    "pinkflash": ["pinkflash", "pink flash"],
    "glowsophy": ["glowsophy"],
    "madame gie": ["madame gie", "madamegie", "mme gie"],
    "fyc": ["fyc", "f.y.c"],
    "sweety": ["sweety"],
    "facetology": ["facetology", "face tology"],
    "scora": ["scora", "scoora"],
    "nuface": ["nuface", "nu face"],
    "make over": ["make over", "makeover"],
    "dear me beauty": ["dear me beauty", "dear me"],
    "kahf": ["kahf"],
    "the originote": ["the originote", "originote"],
    "you": ["you"],
    "polynia": ["polynia"],
    "lumiwhite": ["lumiwhite", "lumi white"],
    "aftermyskin": ["aftermyskin"],
    "drkkot": ["drkkot"],
    "endzibeauty": ["endzibeauty"],
    "milanstory": ["milanstory"],
    "morris": ["morris"],
    "perfectwhite": ["perfectwhite"],
    "premiumplus": ["premiumplus"],
    "signaturebykamila": ["signaturebykamila"],
    "timephoria": ["timephoria"],
    "verile": ["verile"],
    "closeup": ["closeup"],
    "glamersbeauty": ["glamersbeauty"],
    "maryame": ["maryame"],
    "nutrishe": ["nutrishe"],
}

# Enhanced taxonomy with priority weighting
PRODUCT_TYPES = {
    "body_care": {
        "keywords": ["beli", "body", "body lotion", "body serum", "body wash", "deodoran", "hand body", "lulur", "sabun", "scrub", "soap"],
        "priority": 3
    },
    "pampers": {
        "keywords": ["jumbo"],
        "priority": 2
    },
    "pasta gigi": {
        "keywords": ["pasta gigi", "pascagigi", "pepsodent", "closeup"],
        "priority": 0
    },
    "serum": {
        "keywords": ["ampoule", "blood", "brightening", "essence", "hadiah", "halal", "maryame", "niacinamide", "peeling", "peeling solution", "sabun", "serum", "signature", "spesial", "whitening"],
        "priority": 1
    },
    "toner": {
        "keywords": ["toner", "fresh", "face mist", "air mawar", "micellar water"],
        "priority": 1
    },
    "moisturizer": {
        "keywords": ["moisturizer", "day cream", "night cream", "gel", "cream", "pelembab", "moisturizing", "medikon", "tasya"],
        "priority": 2
    },
    "sunscreen": {
        "keywords": ["sunscreen", "uv", "sunblock", "spf", "pa+++", "sun protect"],
        "priority": 1
    },
    "cleanser": {
        "keywords": ["cleanser", "facial wash", "face wash", "sabun muka", "micellar", "facial foam", "cleansing", "facial"],
        "priority": 1
    },
    "mask": {
        "keywords": ["mask", "sheet mask", "clay mask", "peel off", "masker"],
        "priority": 1
    },
    "lip_products": {
        "keywords": ["lip", "matte", "tint", "lipstick", "lip cream", "lip gloss", "lip stain", "lip balm", "stick", "timephoria"],
        "priority": 1
    },
    "perfume": {
        "keywords": ["parfum", "body mist", "fragrance", "eau de parfum", "cologne", "perfume", "morris"],
        "priority": 1
    },
    "hair_care": {
        "keywords": ["rambut", "hair", "shampoo", "conditioner", "hair serum", "hair mask"],
        "priority": 2
    },
    "makeup": {
        "keywords": ["blush", "bulu mata palsu", "compact", "cushion", "eyeliner", "eyeshadow", "foundation", "implora", "langsung", "mascara", "powder"],
        "priority": 1
    },
    "tools": {
        "keywords": ["alat", "applicator", "brush", "kuas", "sarung tangan", "sisir", "tools"],
        "priority": 3
    },
    "nails": {
        "keywords": ["nail", "kuku", "nail polish", "kutek"],
        "priority": 1
    },
}

# Blocklist for non-skincare product indicators
NON_SKINCARE_KEYWORDS = [
    "popok", "diaper", "pampers",
    "softlens", "contact lens",
    "sikat gigi", "toothbrush", "pasta gigi",
    "hair dryer", "pengering rambut", "catok",
    "tato", "tattoo",
]

def is_non_skincare(title_lower: str) -> bool:
    """Return True if title likely describes a non-skincare product."""
    for keyword in NON_SKINCARE_KEYWORDS:
        if keyword in title_lower:
            return True
    return False

def extract_brand(title_lower: str, threshold: float = 85.0) -> tuple:
    """Hybrid Layer 1: Dictionary + Fuzzy match."""
    # 1. Exact alias match
    for canonical, aliases in BRAND_DICTIONARY.items():
        for alias in aliases:
            if alias in title_lower:
                return canonical, 0.95, "dictionary_exact"
    
    # 2. Fuzzy match on tokens
    tokens = title_lower.split()
    for canonical, aliases in BRAND_DICTIONARY.items():
        for alias in aliases:
            for token in tokens:
                ratio = fuzz.ratio(alias, token)
                if ratio >= threshold:
                    return canonical, ratio / 100.0, "dictionary_fuzzy"
                    
    return "unknown", 0.0, "none"

def extract_product_type(title_lower: str) -> tuple:
    """Rule-based keyword matching with priority weighting."""
    matches = []
    for category, config in PRODUCT_TYPES.items():
        for keyword in config["keywords"]:
            if keyword in title_lower:
                matches.append({
                    "category": category,
                    "priority": config["priority"],
                    "keyword": keyword
                })
    
    if not matches:
        return "unknown", 0.0, "none"
        
    # Sort by priority then keyword length
    matches.sort(key=lambda x: (x["priority"], -len(x["keyword"])))
    best_match = matches[0]
    confidence = 0.90 if best_match["priority"] == 1 else 0.75
    
    return best_match["category"], confidence, "keyword_rule"

def enrich_data(df):
    print("Enriching data (Brand & Product Type)...")
    
    brands = []
    types = []
    b_confs = []
    t_confs = []
    
    for idx, row in df.iterrows():
        title = row['title_match']
        
        # Override for specific non-skincare items if needed, 
        # or just let extract_product_type handle high priority categories
        
        b, b_conf, _ = extract_brand(title)
        t, t_conf, _ = extract_product_type(title)
        
        # If it's a known non-skincare type, we keep the classification 
        # but the loader will still decide whether to skip it or not 
        # (currently it skips 'unknown' based on the logic we just wrote)
        
        brands.append(b)
        types.append(t)
        b_confs.append(b_conf)
        t_confs.append(t_conf)
        
    df['brand'] = brands
    df['product_type'] = types
    df['brand_confidence'] = b_confs
    df['product_type_confidence'] = t_confs
    
    return df
