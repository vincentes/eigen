import openai
import base64
import os
import json
from .cache import get_cache_key, get_cached_response, save_cached_response
from config import get_model_config, DEFAULT_MODEL
from .materials.static_map import execute_query_function

MODEL_CONFIG = {
    "gpt-4o": {
        "provider": "openai",
        "model_name": "gpt-4o",
        "max_tokens": 1000,
        "temperature": 0.1
    },
    "claude-4-sonnet": {
        "provider": "anthropic", 
        "model_name": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "temperature": 0.1
    }
}

DEFAULT_MODEL = "claude-4-sonnet"

def get_image_summary(image_data: bytes, use_cache: bool = True, model: str = None) -> str:
    """
    Get a comprehensive summary of what's in a plan image using GPT-4o.
    
    Args:
        image_data: Raw image bytes
        use_cache: Whether to use cached responses (default: True)
        model: Model to use (default: claude-4-sonnet)
        
    Returns:
        Summary description of the image content with query objects resolved
    """
    try:
        if model is None:
            model = DEFAULT_MODEL
            
        try:
            config = get_model_config(model)
        except ValueError as e:
            return f"Error: {e}"
        
        if config["provider"] == "openai":
            summary = _get_openai_summary(image_data, config, use_cache)
        elif config["provider"] == "anthropic":
            summary = _get_anthropic_summary(image_data, config, use_cache)
        else:
            return f"Error: Unknown provider '{config['provider']}'"
        
        # Always process query objects to resolve accessories
        summary = _process_query_objects(summary)
            
        return summary
            
    except Exception as e:
        return f"Error: {e}"


def _get_openai_summary(image_data: bytes, config: dict, use_cache: bool) -> str:
    """Get summary using OpenAI models"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return "Error: OpenAI API key not configured"
            
        client = openai.OpenAI(api_key=api_key)
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        image_format = "jpeg"
        
        # Create summary prompt
        prompt = _get_analysis_prompt()
        
        # Check cache first (if enabled)
        if use_cache:
            cache_key = get_cache_key(prompt, image_data, config["model_name"], "img_summary")
            cached_response = get_cached_response(cache_key)
            if cached_response:
                return cached_response
        
        stream = client.chat.completions.create(
            model=config["model_name"],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{image_format};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_completion_tokens=config["max_tokens"],
            temperature=config["temperature"],
            stream=True
        )
        
        summary = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                summary += content

        # Save to cache (if enabled)
        if use_cache:
            cache_key = get_cache_key(prompt, image_data, config["model_name"], "img_summary")
            save_cached_response(cache_key, summary)
        return summary
        
    except Exception as e:
        return f"Error: {e}"


def _get_anthropic_summary(image_data: bytes, config: dict, use_cache: bool) -> str:
    """Get summary using Anthropic Claude models"""
    try:
        import anthropic
        
        # Initialize Anthropic client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return "Error: Anthropic API key not configured"
            
        client = anthropic.Anthropic(api_key=api_key)
        
        # Create summary prompt
        prompt = _get_analysis_prompt()
        
        # Check cache first (if enabled)
        if use_cache:
            cache_key = get_cache_key(prompt, image_data, config["model_name"], "img_summary")
            cached_response = get_cached_response(cache_key)
            if cached_response:
                return cached_response
        
        # Send message to Claude with streaming
        stream = client.messages.create(
            model=config["model_name"],
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64.b64encode(image_data).decode('utf-8')
                            }
                        }
                    ]
                }
            ],
            stream=True
        )
        
        summary = ""
        for chunk in stream:
            if chunk.type == "content_block_delta":
                if chunk.delta.type == "text_delta":
                    content = chunk.delta.text
                    print(content, end="", flush=True)
                    summary += content

        # Save to cache (if enabled)
        if use_cache:
            cache_key = get_cache_key(prompt, image_data, config["model_name"], "img_summary")
            save_cached_response(cache_key, summary)
        return summary
        
    except Exception as e:
        return f"Error: {e}"


def _get_analysis_prompt() -> str:
    """Get the analysis prompt for door/architectural drawings"""
    return """
    Analyze this image and provide the following response, and nothing else (adapt according to the image). 
    Do not guess profiles,  door types, or finishes.
    Any properties can be NOT_FOUND if not present in the image. 
    Width must be a sum of all the widths of the components in the specific door|window.
    Height must be a sum of all the heights of the components in the specific door|window.
    Typically, plans have lines that represent separate components, and must be summed up.
    Each door or window can have different heights and widths.

    Catalog Filtering (for query fns)
    Filtering: .windows(), .doors(), .accessories(), .profiles(), .gala(), .probba(), .metta(), .suprema(), .anodizado(), .pintado(), .anolok(), .color('name'), .price_range(min=1000, max=5000), .search('term')
    Actions: .get(), .count(), .first(), .last(), .show(), .reset()
    Usage: Chain methods like .windows().accessories().gala().count() - each method returns a new filter object for continued chaining, ending with an action method to get results.

    Provide:

    Profile = "GALA 66", "PROBBA", "GALA NORMAL"
    DoorType = "sliding|swing"
    Finish = "ANOLOK BLANCO"

    {
        "doors": [
            // The following is just an example, however, the structure (properties and data types) is the same for all doors.
            {
                type: DoorType,
                width: string,
                height: string,
                frame: Profile (e.g. "GALA 66"),
                preframe: Profile (e.g. "GALA 66"),
                panel: {
                   profile: Profile (e.g. "GALA 66"),
                   details: string (e.g. "BASTIDOR TABILLAS DE ALUMINIO". This details are for the panel mentioned in the image.)
                },
                finish: Finish (e.g. "ANOLOK BLANCO"),
                accesories: [
                    {
                        type: "handle|lock|hinge",
                        item: string (e.g. "BISAGRAS (GALA 66)"),
                        quantity: number (e.g 4)
                    },
                    {
                        type: "handle|lock|hinge",
                        item: string (e.g. "PICAPORTE MANIJA C/ CERRADURA SEGURIDAD/LLAVE"),
                        quantity: number (e.g 1)
                    },
                    {
                        type: "handle|lock|hinge",
                        item: string (e.g. "CIERRE CON BRAZO HIDRAULICO"),
                        quantity: number (e.g 1)
                    }
                ]
            },
            // Can be multiple doors
        ], 
        "windows": [
            // (Similar to door)
        ]
    }
    
    Do not wrap the response in ```json or ```.
    """

    # // OMITTED: We are not gonna use query fns for now.
    # // ...
    # // If a plan for a window says something along the lines of "CORREDERA CON TODOS LOS ACCESORIO DE ACUERDO AL TIPO"
    # // Or does not specify accessories, include in accessories array:
    # {
    #     type: "query"
    #     fn: ".windows().accessories()"
    # }


def _process_query_objects(summary: str) -> str:
    """
    Process query objects with 'fn' properties in the summary and resolve them with actual accessories.
    
    Args:
        summary: The raw summary string from the AI model
        
    Returns:
        Summary string with query objects resolved to actual accessory data
    """
    try:
        # Try to parse the summary as JSON
        try:
            data = json.loads(summary)
        except json.JSONDecodeError:
            # If not valid JSON, return as-is
            return summary
        
        # Process doors
        if 'doors' in data and isinstance(data['doors'], list):
            for door in data['doors']:
                if isinstance(door, dict) and 'accesories' in door:
                    door['accesories'] = _resolve_accessory_queries(door['accesories'])
        
        # Process windows
        if 'windows' in data and isinstance(data['windows'], list):
            for window in data['windows']:
                if isinstance(window, dict) and 'accesories' in window:
                    window['accesories'] = _resolve_accessory_queries(window['accesories'])
        
        # Return the processed JSON as a string
        return json.dumps(data, indent=2)
        
    except Exception as e:
        print(f"Error processing query objects: {e}")
        return summary


def _resolve_accessory_queries(accessories: list) -> list:
    """
    Resolve query objects in accessories list.
    
    Args:
        accessories: List of accessory objects that may contain query objects
        
    Returns:
        List with query objects resolved to actual accessory data
    """
    if not isinstance(accessories, list):
        return accessories
    
    resolved_accessories = []
    
    for accessory in accessories:
        if isinstance(accessory, dict):
            # Check if this is a query object
            if accessory.get('type') == 'query' and 'fn' in accessory:
                # Execute the query function
                query_results = execute_query_function(accessory['fn'])
                
                # Convert query results to accessory format
                for result in query_results:
                    resolved_accessory = {
                        'type': _determine_accessory_type(result),
                        'item': result.get('name', result.get('description', 'Unknown item')),
                        'quantity': 1,  # Default quantity
                        'price': result.get('price'),
                        'sku': result.get('sku'),
                        'details': result.get('ai_description', result.get('description', ''))
                    }
                    resolved_accessories.append(resolved_accessory)
            else:
                # Regular accessory object, keep as-is
                resolved_accessories.append(accessory)
        else:
            # Not a dict, keep as-is
            resolved_accessories.append(accessory)
    
    return resolved_accessories


def _determine_accessory_type(product: dict) -> str:
    """
    Determine the accessory type based on product name/description.
    
    Args:
        product: Product dictionary
        
    Returns:
        Accessory type: "handle", "lock", "hinge", or "other"
    """
    name = product.get('name', '').lower()
    description = product.get('description', '').lower()
    text = f"{name} {description}"
    
    if any(keyword in text for keyword in ['bisagra', 'hinge', 'gozne']):
        return 'hinge'
    elif any(keyword in text for keyword in ['manija', 'handle', 'tirador', 'picaporte']):
        return 'handle'
    elif any(keyword in text for keyword in ['cerradura', 'lock', 'llave', 'seguridad']):
        return 'lock'
    else:
        return 'other'
