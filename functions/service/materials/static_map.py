import os
import json
from typing import List, Dict, Any, Optional

MATERIAL_COSTS = {
    # CODE 924840261660225
    "GALA 66": {
        "length_mm": 6800, # mm
        "length_cm": 680, # cm
        "finish": "painted",
        "color": "Dark gray microtextured C-3987",
        "units_per_package": 3.72561911,
        "weight_per_meter": 1.46900000,
        "thickness_mm": 1.60000,
        "price_per_unit": 91.52,
        "price_per_package": 182.52
    },
    # Standard GALA profile
    "GALA NORMAL": {
        "length_mm": 6800, # mm
        "length_cm": 680, # cm
        "finish": "anodized",
        "color": "Natural",
        "units_per_package": 3.72561911,
        "weight_per_meter": 1.35000000,
        "thickness_mm": 1.50000,
        "price_per_unit": 85.00,
        "price_per_package": 170.00
    }
}

class StaticAccessoryFilter:
    """Builder class for filtering accessories from static data and catalog"""
    
    def __init__(self):
        self.filtered_accessories = []
        self.current_category = None
        self._load_catalog_data()
    
    def _load_catalog_data(self):
        """Load catalog data from scraped files"""
        try:
            # Load main catalog
            current_dir = os.path.dirname(os.path.abspath(__file__))
            catalog_path = os.path.join(current_dir, '..', '..', 'scraped', 'catalog.json')
            
            if os.path.exists(catalog_path):
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    catalog_data = json.load(f)
                    self.catalog_products = catalog_data.get('products', [])
            else:
                self.catalog_products = []
            
            # Load accessories data
            accessories_path = os.path.join(current_dir, '..', '..', 'scraped', 'accesories', 'accesories.json')
            if os.path.exists(accessories_path):
                with open(accessories_path, 'r', encoding='utf-8') as f:
                    accessories_data = json.load(f)
                    self.accessories_products = accessories_data.get('hinge_products', [])
            else:
                self.accessories_products = []
            
            # Start with all products
            self.all_products = self.catalog_products + self.accessories_products
            self.filtered_accessories = self.all_products.copy()
            
        except Exception as e:
            print(f"Warning: Could not load catalog data: {e}")
            self.catalog_products = []
            self.accessories_products = []
            self.all_products = []
            self.filtered_accessories = []
    
    def windows(self) -> 'StaticAccessoryFilter':
        """Filter for window-related accessories"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories
            if any(keyword in p.get('name', '').lower() or 
                   keyword in p.get('description', '').lower() or 
                   keyword in p.get('ai_description', '').lower()
                   for keyword in ['window', 'ventana', 'corredera', 'sliding', 'guia', 'guide'])
        ]
        return self
    
    def doors(self) -> 'StaticAccessoryFilter':
        """Filter for door-related accessories"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if any(keyword in p.get('name', '').lower() or 
                   keyword in p.get('description', '').lower() or 
                   keyword in p.get('ai_description', '').lower()
                   for keyword in ['door', 'puerta', 'batiente', 'swing'])
        ]
        return self
    
    def accessories(self) -> 'StaticAccessoryFilter':
        """Filter for accessory products"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if (p.get('main_category') == 'Accesorios (Accessories)' or
                any(keyword in p.get('name', '').lower() or 
                    keyword in p.get('description', '').lower()
                    for keyword in ['accesorio', 'accessory', 'bisagra', 'hinge', 'manija', 'handle', 
                                   'cerradura', 'lock', 'picaporte', 'cierre']))
        ]
        return self
    
    def profiles(self) -> 'StaticAccessoryFilter':
        """Filter for profile products"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if p.get('main_category') == 'Perfiles (Profiles)'
        ]
        return self
    
    def gala(self) -> 'StaticAccessoryFilter':
        """Filter for GALA system accessories"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if 'gala' in p.get('name', '').lower() or 'gala' in p.get('description', '').lower()
        ]
        return self
    
    def probba(self) -> 'StaticAccessoryFilter':
        """Filter for PROBBA system accessories"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if 'probba' in p.get('name', '').lower() or 'probba' in p.get('description', '').lower()
        ]
        return self
    
    def metta(self) -> 'StaticAccessoryFilter':
        """Filter for METTA system accessories"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if 'metta' in p.get('name', '').lower() or 'metta' in p.get('description', '').lower()
        ]
        return self
    
    def suprema(self) -> 'StaticAccessoryFilter':
        """Filter for SUPREMA system accessories"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if 'suprema' in p.get('name', '').lower() or 'suprema' in p.get('description', '').lower()
        ]
        return self
    
    def anodizado(self) -> 'StaticAccessoryFilter':
        """Filter for anodized finish accessories"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if 'anodizado' in p.get('finish', '').lower() or 'anodized' in p.get('finish', '').lower()
        ]
        return self
    
    def pintado(self) -> 'StaticAccessoryFilter':
        """Filter for painted finish accessories"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if 'pintado' in p.get('finish', '').lower() or 'painted' in p.get('finish', '').lower()
        ]
        return self
    
    def anolok(self) -> 'StaticAccessoryFilter':
        """Filter for Anolok finish accessories"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if 'anolok' in p.get('finish', '').lower()
        ]
        return self
    
    def color(self, color_name: str) -> 'StaticAccessoryFilter':
        """Filter by specific color"""
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if color_name.lower() in p.get('color', '').lower()
        ]
        return self
    
    def price_range(self, min_price: float = None, max_price: float = None) -> 'StaticAccessoryFilter':
        """Filter by price range"""
        if min_price is not None:
            self.filtered_accessories = [
                p for p in self.filtered_accessories 
                if p.get('price') is not None and p.get('price') >= min_price
            ]
        if max_price is not None:
            self.filtered_accessories = [
                p for p in self.filtered_accessories 
                if p.get('price') is not None and p.get('price') <= max_price
            ]
        return self
    
    def search(self, search_term: str) -> 'StaticAccessoryFilter':
        """Search for accessories containing the search term"""
        search_term = search_term.lower()
        self.filtered_accessories = [
            p for p in self.filtered_accessories 
            if (search_term in p.get('name', '').lower() or 
                search_term in p.get('description', '').lower() or 
                search_term in p.get('ai_description', '').lower())
        ]
        return self
    
    def get(self) -> List[Dict[str, Any]]:
        """Get the filtered accessories"""
        return self.filtered_accessories
    
    def count(self) -> int:
        """Get the count of filtered accessories"""
        return len(self.filtered_accessories)
    
    def first(self) -> Optional[Dict[str, Any]]:
        """Get the first accessory"""
        return self.filtered_accessories[0] if self.filtered_accessories else None
    
    def last(self) -> Optional[Dict[str, Any]]:
        """Get the last accessory"""
        return self.filtered_accessories[-1] if self.filtered_accessories else None
    
    def reset(self) -> 'StaticAccessoryFilter':
        """Reset to all accessories"""
        self.filtered_accessories = self.all_products.copy()
        return self

def execute_query_function(fn_string: str) -> List[Dict[str, Any]]:
    """
    Execute a query function string and return the results.
    
    Args:
        fn_string: The function string (e.g., ".windows().accessories().get()")
        
    Returns:
        List of accessory products that match the query
    """
    try:
        # Create a new filter instance
        filter_instance = StaticAccessoryFilter()
        
        # Remove leading dot if present
        if fn_string.startswith('.'):
            fn_string = fn_string[1:]
        
        # Build the method chain
        methods = fn_string.split('.')
        current_filter = filter_instance
        
        for method in methods:
            if '(' in method:
                method_name = method.split('(')[0]
                # Extract parameters if any
                params_str = method[method.find('(')+1:method.rfind(')')]
                
                if method_name in ['color', 'search']:
                    # Methods that take string parameters
                    if params_str and params_str.strip('\'"'):
                        param = params_str.strip('\'"')
                        current_filter = getattr(current_filter, method_name)(param)
                    else:
                        current_filter = getattr(current_filter, method_name)('')
                elif method_name == 'price_range':
                    # Method that takes numeric parameters
                    if params_str:
                        # Parse parameters like min=1000, max=5000
                        params = {}
                        for param in params_str.split(','):
                            if '=' in param:
                                key, value = param.split('=', 1)
                                key = key.strip()
                                value = float(value.strip())
                                params[key] = value
                        current_filter = getattr(current_filter, method_name)(**params)
                    else:
                        current_filter = getattr(current_filter, method_name)()
                else:
                    # Methods with no parameters
                    current_filter = getattr(current_filter, method_name)()
            else:
                # Method without parentheses (shouldn't happen in proper syntax)
                current_filter = getattr(current_filter, method)()
        
        # If the last method was get(), return the result directly
        if isinstance(current_filter, list):
            return current_filter
        else:
            # If we ended with a filter object, call get() to return results
            return current_filter.get()
            
    except Exception as e:
        print(f"Error executing query function '{fn_string}': {e}")
        return []

def get_material_cost(profile: str) -> dict:
    """
    Get material costs for a given profile.
    
    Args:
        profile: The profile type (e.g., "GALA 66", "GALA NORMAL", "PROBBA")
        
    Returns:
        Dictionary with cost breakdown per cm, or None if profile not found
    """
    return MATERIAL_COSTS.get(profile)

def get_static_accessories() -> StaticAccessoryFilter:
    """
    Get a new StaticAccessoryFilter instance for chaining queries.
    
    Returns:
        StaticAccessoryFilter instance for building queries
    """
    return StaticAccessoryFilter()
