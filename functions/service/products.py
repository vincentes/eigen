import json
import os
from typing import List, Dict, Any, Optional

class ProductFilter:
    """Builder class for filtering products from the catalog"""
    
    def __init__(self, catalog_data: Dict[str, Any]):
        self.catalog_data = catalog_data
        self.products = catalog_data.get('products', [])
        self.filtered_products = self.products.copy()
        self.current_category = None
        self.current_system = None
    
    def windows(self) -> 'ProductFilter':
        """Filter for window-related products"""
        self.filtered_products = [
            p for p in self.filtered_products
            if any(keyword in p.get('name', '').lower() or 
                   keyword in p.get('description', '').lower() or 
                   keyword in p.get('ai_description', '').lower()
                   for keyword in ['window', 'ventana', 'corredera', 'sliding', 'guia', 'guide'])
        ]
        return self
    
    def doors(self) -> 'ProductFilter':
        """Filter for door-related products"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if any(keyword in p.get('name', '').lower() or 
                   keyword in p.get('description', '').lower() or 
                   keyword in p.get('ai_description', '').lower()
                   for keyword in ['door', 'puerta', 'batiente', 'swing'])
        ]
        return self
    
    def accessories(self) -> 'ProductFilter':
        """Filter for accessory products"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if p.get('main_category') == 'Accesorios (Accessories)'
        ]
        return self
    
    def profiles(self) -> 'ProductFilter':
        """Filter for profile products"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if p.get('main_category') == 'Perfiles (Profiles)'
        ]
        return self
    
    def gala(self) -> 'ProductFilter':
        """Filter for GALA system products"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if 'gala' in p.get('name', '').lower() or 
               'gala' in p.get('description', '').lower() or
               'gala' in p.get('ai_description', '').lower()
        ]
        return self
    
    def probba(self) -> 'ProductFilter':
        """Filter for PROBBA system products"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if 'probba' in p.get('name', '').lower() or 
               'probba' in p.get('description', '').lower() or
               'probba' in p.get('ai_description', '').lower()
        ]
        return self
    
    def metta(self) -> 'ProductFilter':
        """Filter for METTA system products"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if 'metta' in p.get('name', '').lower() or 
               'metta' in p.get('description', '').lower() or
               'metta' in p.get('ai_description', '').lower()
        ]
        return self
    
    def suprema(self) -> 'ProductFilter':
        """Filter for SUPREMA system products"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if 'suprema' in p.get('name', '').lower() or 
               'suprema' in p.get('description', '').lower() or
               'suprema' in p.get('ai_description', '').lower()
        ]
        return self
    
    def anodizado(self) -> 'ProductFilter':
        """Filter for anodized finish products"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if 'anodizado' in p.get('finish', '').lower()
        ]
        return self
    
    def pintado(self) -> 'ProductFilter':
        """Filter for painted finish products"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if 'pintado' in p.get('finish', '').lower()
        ]
        return self
    
    def anolok(self) -> 'ProductFilter':
        """Filter for Anolok finish products"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if 'anolok' in p.get('finish', '').lower()
        ]
        return self
    
    def color(self, color_name: str) -> 'ProductFilter':
        """Filter by specific color"""
        self.filtered_products = [
            p for p in self.filtered_products 
            if color_name.lower() in p.get('color', '').lower()
        ]
        return self
    
    def price_range(self, min_price: float = None, max_price: float = None) -> 'ProductFilter':
        """Filter by price range"""
        if min_price is not None:
            self.filtered_products = [
                p for p in self.filtered_products 
                if p.get('price') is not None and p.get('price') >= min_price
            ]
        if max_price is not None:
            self.filtered_products = [
                p for p in self.filtered_products 
                if p.get('price') is not None and p.get('price') <= max_price
            ]
        return self
    
    def search(self, search_term: str) -> 'ProductFilter':
        """Search for products containing the search term"""
        search_term = search_term.lower()
        self.filtered_products = [
            p for p in self.filtered_products 
            if (search_term in p.get('name', '').lower() or 
                search_term in p.get('description', '').lower() or 
                search_term in p.get('ai_description', '').lower())
        ]
        return self
    
    def get(self) -> List[Dict[str, Any]]:
        """Get the filtered products"""
        return self.filtered_products
    
    def count(self) -> int:
        """Get the count of filtered products"""
        return len(self.filtered_products)
    
    def first(self) -> Optional[Dict[str, Any]]:
        """Get the first filtered product"""
        return self.filtered_products[0] if self.filtered_products else None
    
    def last(self) -> Optional[Dict[str, Any]]:
        """Get the last filtered product"""
        return self.filtered_products[-1] if self.filtered_products else None
    
    def reset(self) -> 'ProductFilter':
        """Reset filters and return all products"""
        self.filtered_products = self.products.copy()
        return self

class ProductCatalog:
    """Main catalog class with builder methods"""
    
    def __init__(self, catalog_path: str = None):
        if catalog_path is None:
            # Default path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            catalog_path = os.path.join(current_dir, '..', 'scraped', 'catalog.json')
        
        with open(catalog_path, 'r', encoding='utf-8') as f:
            self.catalog_data = json.load(f)
    
    def all(self) -> ProductFilter:
        """Get all products"""
        return ProductFilter(self.catalog_data)
    
    def windows(self) -> ProductFilter:
        """Get window-related products"""
        return ProductFilter(self.catalog_data).windows()
    
    def doors(self) -> ProductFilter:
        """Get door-related products"""
        return ProductFilter(self.catalog_data).doors()
    
    def accessories(self) -> ProductFilter:
        """Get accessory products"""
        return ProductFilter(self.catalog_data).accessories()
    
    def profiles(self) -> ProductFilter:
        """Get profile products"""
        return ProductFilter(self.catalog_data).profiles()

# Convenience function to create a catalog instance
def catalog(catalog_path: str = None) -> ProductCatalog:
    """Create a ProductCatalog instance"""
    return ProductCatalog(catalog_path)