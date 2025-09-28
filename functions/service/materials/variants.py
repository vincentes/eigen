def variants(product):
    """Get variants for a specific product"""
    if 'variants' in product and product['variants']:
        return product['variants']
    return []

def variants_batch(products):
    """Get variants for an array of products"""
    results = []
    for product in products:
        if 'variants' in product and product['variants']:
            results.append(product['variants'])
    return results
