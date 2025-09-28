#!/usr/bin/env python3
"""
Test script to verify the query integration works correctly.
"""

import json
from functions.service.materials.static_map import execute_query_function, get_static_accessories
from functions.service.image import _process_query_objects, _resolve_accessory_queries

def test_query_execution():
    """Test basic query execution"""
    print("Testing query execution...")
    
    # Test basic accessories query
    result = execute_query_function(".accessories().get()")
    print(f"Accessories found: {len(result)}")
    
    if result:
        print(f"First accessory: {result[0].get('name', 'Unknown')}")
    
    # Test windows + accessories query
    result = execute_query_function(".windows().accessories().get()")
    print(f"Window accessories found: {len(result)}")
    
    # Test doors + accessories query  
    result = execute_query_function(".doors().accessories().get()")
    print(f"Door accessories found: {len(result)}")
    
    return True

def test_query_object_processing():
    """Test processing of query objects in JSON"""
    print("\nTesting query object processing...")
    
    # Sample JSON with query objects
    sample_json = {
        "doors": [
            {
                "type": "swing",
                "width": "800mm",
                "height": "2000mm",
                "frame": "GALA 66",
                "accesories": [
                    {
                        "type": "handle",
                        "item": "MANIJA STANDARD",
                        "quantity": 1
                    },
                    {
                        "type": "query",
                        "fn": ".doors().accessories().gala().first()"
                    }
                ]
            }
        ],
        "windows": [
            {
                "type": "sliding", 
                "accesories": [
                    {
                        "type": "query",
                        "fn": ".windows().accessories().get()"
                    }
                ]
            }
        ]
    }
    
    json_str = json.dumps(sample_json)
    processed = _process_query_objects(json_str)
    
    try:
        processed_data = json.loads(processed)
        
        # Check if query objects were resolved
        door_accessories = processed_data.get('doors', [{}])[0].get('accesories', [])
        window_accessories = processed_data.get('windows', [{}])[0].get('accesories', [])
        
        print(f"Door accessories after processing: {len(door_accessories)}")
        print(f"Window accessories after processing: {len(window_accessories)}")
        
        # Print some details
        for i, acc in enumerate(door_accessories[:3]):  # First 3
            print(f"  Door accessory {i+1}: {acc.get('item', 'Unknown')}")
            
        for i, acc in enumerate(window_accessories[:3]):  # First 3  
            print(f"  Window accessory {i+1}: {acc.get('item', 'Unknown')}")
            
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error: Processed result is not valid JSON: {e}")
        print(f"Processed result: {processed[:200]}...")
        return False

def test_static_filter():
    """Test the StaticAccessoryFilter directly"""
    print("\nTesting StaticAccessoryFilter...")
    
    filter_instance = get_static_accessories()
    
    # Test method chaining
    result = filter_instance.accessories().count()
    print(f"Total accessories: {result}")
    
    # Test specific queries
    gala_accessories = filter_instance.reset().gala().accessories().count()
    print(f"GALA accessories: {gala_accessories}")
    
    window_accessories = filter_instance.reset().windows().accessories().count()
    print(f"Window accessories: {window_accessories}")
    
    return True

if __name__ == "__main__":
    print("=== Testing Query Integration ===")
    
    try:
        success = True
        success &= test_static_filter()
        success &= test_query_execution()
        success &= test_query_object_processing()
        
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Some tests failed!")
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
