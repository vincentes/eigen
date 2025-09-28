import openai
import base64
import json
import os
from typing import List, Dict, Any
from .cache import get_cache_key, get_cached_response, save_cached_response


def extract_bom_with_context(image_data: bytes, summary: str = "") -> List[Dict[str, Any]]:
    """
    Extract BOM (Bill of Materials) data from an image using context from summary.
    
    Args:
        image_data: Raw image bytes
        summary: Summary of the image content for better context
        
    Returns:
        List of BOM tables found in the image
    """
    try:
        # Initialize OpenAI client with environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Error: API Key not configured")
            return []
            
        client = openai.OpenAI(api_key=api_key)
        
        # Encode image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Determine image format from the data
        image_format = "png"
        if image_data.startswith(b'\xff\xd8\xff'):
            image_format = "jpeg"
        elif image_data.startswith(b'\x89PNG'):
            image_format = "png"
        elif image_data.startswith(b'GIF'):
            image_format = "gif"
        elif image_data.startswith(b'BM'):
            image_format = "bmp"
        
        # Create context-aware prompt
        context_info = f"\n\nIMAGE CONTEXT:\n{summary}\n" if summary else ""
        
        prompt = f"""
        Analiza esta imagen y extrae todas las tablas de Lista de Materiales (BOM) que puedas encontrar.{context_info}
        
        Para cada tabla BOM, identifica:
        1. Encabezados/nombres de columnas
        2. Cada fila de datos con números de parte, cantidades, descripciones, etc.
        3. Cualquier metadato adicional como números de revisión, fechas, etc.
        
        Devuelve los datos en el siguiente formato JSON:
        {{
            "bom_tables": [
                {{
                    "table_id": 1,
                    "headers": ["Número de Parte", "Cantidad", "Descripción", "Material", "Notas"],
                    "items": [
                        {{
                            "part_number": "ABC-123",
                            "quantity": "2",
                            "description": "Soporte de Acero",
                            "material": "Acero",
                            "notes": "Anodizado"
                        }}
                    ],
                    "metadata": {{
                        "revision": "Rev A",
                        "date": "2024-01-15",
                        "project": "Nombre del Proyecto"
                    }}
                }}
            ]
        }}
        
        Si no se encuentran tablas BOM, devuelve: {{"bom_tables": []}}
        
        Usa el contexto proporcionado para mejorar la precisión de tu extracción.
        """
        
        # Check cache first
        cache_key = get_cache_key(prompt, image_data, "gpt-4o", "bom_extract")
        cached_response = get_cached_response(cache_key)
        if cached_response:
            # Parse cached JSON response
            try:
                start_idx = cached_response.find('{')
                end_idx = cached_response.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = cached_response[start_idx:end_idx]
                    result = json.loads(json_str)
                    bom_tables = result.get('bom_tables', [])
                    formatted_boms = []
                    for table in bom_tables:
                        formatted_bom = {
                            'table_id': table.get('table_id', 1),
                            'headers': table.get('headers', []),
                            'items': table.get('items', []),
                            'item_count': len(table.get('items', [])),
                            'metadata': table.get('metadata', {}),
                            'raw_text': []
                        }
                        formatted_boms.append(formatted_bom)
                    return formatted_boms
            except:
                pass  
        
        stream = client.chat.completions.create(
            model="gpt-4o",
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
            max_completion_tokens=4000,
            temperature=0.1,
            stream=True
        )
        
        response_text = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                response_text += content
        
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Convert to the expected format
                bom_tables = result.get('bom_tables', [])
                formatted_boms = []
                
                for table in bom_tables:
                    formatted_bom = {
                        'table_id': table.get('table_id', 1),
                        'headers': table.get('headers', []),
                        'items': table.get('items', []),
                        'item_count': len(table.get('items', [])),
                        'metadata': table.get('metadata', {}),
                        'raw_text': []  # Keep for compatibility
                    }
                    formatted_boms.append(formatted_bom)
                
                # Cache the response
                save_cached_response(cache_key, response_text)
                return formatted_boms
            else:
                return []
                
        except json.JSONDecodeError as e:
            return []
            
    except Exception as e:
        return []


def extract_bom_summary(bom_detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract a summary of BOM detection results.
    
    Args:
        bom_detections: List of BOM tables from detect_boms()
        
    Returns:
        Summary dictionary with counts and basic info
    """
    if not bom_detections:
        return {"total_tables": 0, "total_items": 0}
    
    total_items = sum(bom.get('item_count', 0) for bom in bom_detections)
    
    summary = {
        "total_tables": len(bom_detections),
        "total_items": total_items,
        "tables": []
    }
    
    for bom in bom_detections:
        table_summary = {
            "table_id": bom.get('table_id', 1),
            "item_count": bom.get('item_count', 0),
            "headers": bom.get('headers', [])
        }
        summary["tables"].append(table_summary)
    
    return summary
