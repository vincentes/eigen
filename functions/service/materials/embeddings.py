import json
import pandas as pd
import pickle
import os
from tqdm import tqdm
from ..embeddings import get_embedding

def products():
    # Define cache file path
    cache_file = 'cache/product_embeddings.pkl'
    
    # Check if cached embeddings exist
    if os.path.exists(cache_file):
        print("[embeddings] Loading cached product embeddings...")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    print("[embeddings] No cache found. Generating embeddings...")
    
    with open('scraped/catalog.json', 'r') as f:
        data = json.load(f)

    products_data = data['products']
    results = []
    
    # Add progress bar for embedding generation
    for product in tqdm(products_data, desc="Generating embeddings", unit="product"):
        text_parts = []
        for key, value in product.items():
            if value is not None and value != '' and key not in ['variants']:
                if isinstance(value, (str, int, float)):
                    text_parts.append(str(value))
                elif isinstance(value, list):
                    text_parts.extend([str(item) for item in value if item is not None])
        text = ' '.join(text_parts)
        embedding = get_embedding(text)
        results.append({'product': product, 'embedding': embedding})

    df = pd.DataFrame(results)
    
    # Save to cache
    os.makedirs('cache', exist_ok=True)
    print(f"[embeddings] Saving {len(df)} embeddings to cache...")
    with open(cache_file, 'wb') as f:
        pickle.dump(df, f)
    
    print("[embeddings] Embeddings cached successfully!")
    return df
