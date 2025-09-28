import json
import csv
import os
from datetime import datetime
from .materials.static_map import get_material_cost
import math


def calculate_door_cost(door_data: dict) -> dict:
    """
    Calculate material cost for a single door based on its dimensions and specifications.
    
    Args:
        door_data: Dictionary containing door specifications (width, height, frame, preframe, panel, finish, accessories)
        
    Returns:
        Dictionary with cost breakdown for the door
    """
    try:
        # Extract dimensions (convert from string to float)
        width_cm = float(door_data.get('width', 0))
        height_cm = float(door_data.get('height', 0))
        
        # Get profile for cost lookup
        profile = door_data.get('frame', 'NOT_FOUND')
        if profile == 'NOT_FOUND':
            return {"error": "Profile not found", "total_cost": 0.0}
        
        # Get material costs for this profile
        material_costs = get_material_cost(profile)
        if not material_costs:
            return {"error": f"No cost data found for profile: {profile}", "total_cost": 0.0}
        
        # Marco
        frame_perimeter_cm = 2 * (width_cm + height_cm)
        # Premarco
        preframe_perimeter_cm = 2 * (width_cm + height_cm)
        # Contramarco
        contramarco_perimeter_cm = 2 * (width_cm + height_cm)

        # Calculate perimeter (frame + preframe)
        perimeter_cm = frame_perimeter_cm + preframe_perimeter_cm + contramarco_perimeter_cm
        
        # Calculate frame cost only
        aluminium_bars_needed = math.ceil(perimeter_cm / material_costs.get('length_cm', 0))
        aluminium_bars_cost = aluminium_bars_needed *  material_costs.get('price_per_unit', 0)
        total_cost = aluminium_bars_cost

        # Hinge cost
        
        
        return {
            "door_specs": {
                "width_cm": width_cm,
                "height_cm": height_cm,
                "profile": profile
            },
            "cost_breakdown": {
                "aluminium_bars_needed": aluminium_bars_needed,
                "aluminium_bars_cost": round(aluminium_bars_cost, 2)
            },
            "total_cost": round(total_cost, 2),
            "perimeter_cm": round(perimeter_cm, 2)
        }
        
    except (ValueError, TypeError) as e:
        return {"error": f"Invalid dimension data: {str(e)}", "total_cost": 0.0}
    except Exception as e:
        return {"error": f"Calculation error: {str(e)}", "total_cost": 0.0}

def calculate_window_cost(window_data: dict) -> dict:
    """
    Calculate material cost for a single window based on its dimensions and specifications.
    
    Args:
        window_data: Dictionary containing window specifications (width, height, frame, preframe, panel, finish, accessories)
        
    Returns:
        Dictionary with cost breakdown for the window
    """
    try:
        # Extract dimensions (convert from string to float)
        width_cm = float(window_data.get('width', 0))
        height_cm = float(window_data.get('height', 0))
        
        # Get profile for cost lookup
        profile = window_data.get('frame', 'NOT_FOUND')
        if profile == 'NOT_FOUND':
            return {"error": "Profile not found", "total_cost": 0.0}
        
        # Get material costs for this profile
        material_costs = get_material_cost(profile)
        if not material_costs:
            return {"error": f"No cost data found for profile: {profile}", "total_cost": 0.0}
        
        # Marco
        frame_perimeter_cm = 2 * (width_cm + height_cm)
        # Premarco
        preframe_perimeter_cm = 2 * (width_cm + height_cm)
        # Contramarco
        contramarco_perimeter_cm = 2 * (width_cm + height_cm)

        # Calculate perimeter (frame + preframe)
        perimeter_cm = frame_perimeter_cm + preframe_perimeter_cm + contramarco_perimeter_cm
        
        # Calculate frame cost only
        aluminium_bars_needed = math.ceil(perimeter_cm / material_costs.get('length_cm', 0))
        aluminium_bars_cost = aluminium_bars_needed * material_costs.get('price_per_unit', 0)
        total_cost = aluminium_bars_cost
        
        return {
            "window_specs": {
                "width_cm": width_cm,
                "height_cm": height_cm,
                "profile": profile
            },
            "cost_breakdown": {
                "aluminium_bars_needed": aluminium_bars_needed,
                "aluminium_bars_cost": round(aluminium_bars_cost, 2)
            },
            "total_cost": round(total_cost, 2),
            "perimeter_cm": round(perimeter_cm, 2)
        }
        
    except (ValueError, TypeError) as e:
        return {"error": f"Invalid dimension data: {str(e)}", "total_cost": 0.0}
    except Exception as e:
        return {"error": f"Calculation error: {str(e)}", "total_cost": 0.0}

def calculate_plan_cost(plan_json: str) -> dict:
    """
    Calculate total material cost for a complete plan (multiple doors/windows).
    
    Args:
        plan_json: JSON string containing the plan data (as returned by image analysis)
        
    Returns:
        Dictionary with total cost breakdown
    """
    try:
        # Parse JSON
        if isinstance(plan_json, str):
            plan_data = json.loads(plan_json)
        else:
            plan_data = plan_json
        
        total_cost = 0.0
        door_costs = []
        window_costs = []
        
        # Process doors
        doors = plan_data.get('doors', [])
        for i, door in enumerate(doors):
            door_cost = calculate_door_cost(door)
            door_cost['door_index'] = i
            door_costs.append(door_cost)
            if 'total_cost' in door_cost:
                total_cost += door_cost['total_cost']
        
        # Process windows
        windows = plan_data.get('windows', [])
        for i, window in enumerate(windows):
            window_cost = calculate_window_cost(window)
            window_cost['window_index'] = i
            window_costs.append(window_cost)
            if 'total_cost' in window_cost:
                total_cost += window_cost['total_cost']
        
        return {
            "plan_summary": {
                "total_doors": len(doors),
                "total_windows": len(windows),
                "total_cost": round(total_cost, 2)
            },
            "door_costs": door_costs,
            "window_costs": window_costs
        }
        
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "total_cost": 0.0}
    except Exception as e:
        return {"error": f"Plan calculation error: {str(e)}", "total_cost": 0.0}

def calculate_cost_from_image_analysis(image_analysis_result: str) -> dict:
    """
    Calculate cost directly from image analysis result.
    
    Args:
        image_analysis_result: Raw string output from image analysis
        
    Returns:
        Dictionary with cost breakdown
    """
    try:
        # Try to extract JSON from the analysis result
        # Look for JSON-like content between curly braces
        start_idx = image_analysis_result.find('{')
        end_idx = image_analysis_result.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            return {"error": "No JSON found in analysis result", "total_cost": 0.0}
        
        json_str = image_analysis_result[start_idx:end_idx + 1]
        return calculate_plan_cost(json_str)
        
    except Exception as e:
        return {"error": f"Image analysis processing error: {str(e)}", "total_cost": 0.0}

def export_cost_breakdown_to_csv(cost_result: dict, output_path: str = None) -> str:
    """
    Export cost breakdown to CSV file.
    
    Args:
        cost_result: Dictionary with cost breakdown from calculate_plan_cost
        output_path: Optional path for CSV file. If None, generates timestamped filename.
        
    Returns:
        Path to the generated CSV file
    """
    try:
        # Generate filename if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"door_cost_breakdown_{timestamp}.csv"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        # Prepare data for CSV
        csv_data = []
        
        # Add header row
        csv_data.append([
            "Type",
            "Item Number",
            "Width (cm)",
            "Height (cm)", 
            "Profile",
            "Perimeter (cm)",
            "Aluminum Bars Needed",
            "Bar Cost ($)",
            "Total Cost ($)",
            "Status"
        ])
        
        # Add door data
        door_costs = cost_result.get('door_costs', [])
        for i, door_cost in enumerate(door_costs):
            if 'error' in door_cost:
                csv_data.append([
                    "Door",
                    i + 1,
                    "N/A",
                    "N/A", 
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "0.00",
                    f"Error: {door_cost['error']}"
                ])
            else:
                specs = door_cost.get('door_specs', {})
                breakdown = door_cost.get('cost_breakdown', {})
                total = door_cost.get('total_cost', 0)
                
                csv_data.append([
                    "Door",
                    i + 1,
                    f"{specs.get('width_cm', 0):.1f}",
                    f"{specs.get('height_cm', 0):.1f}",
                    specs.get('profile', 'Unknown'),
                    f"{door_cost.get('perimeter_cm', 0):.1f}",
                    f"{breakdown.get('aluminium_bars_needed', 0):.1f}",
                    f"{breakdown.get('aluminium_bars_cost', 0):.2f}",
                    f"{total:.2f}",
                    "OK"
                ])
        
        # Add window data
        window_costs = cost_result.get('window_costs', [])
        for i, window_cost in enumerate(window_costs):
            if 'error' in window_cost:
                csv_data.append([
                    "Window",
                    i + 1,
                    "N/A",
                    "N/A", 
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "0.00",
                    f"Error: {window_cost['error']}"
                ])
            else:
                specs = window_cost.get('window_specs', {})
                breakdown = window_cost.get('cost_breakdown', {})
                total = window_cost.get('total_cost', 0)
                
                csv_data.append([
                    "Window",
                    i + 1,
                    f"{specs.get('width_cm', 0):.1f}",
                    f"{specs.get('height_cm', 0):.1f}",
                    specs.get('profile', 'Unknown'),
                    f"{window_cost.get('perimeter_cm', 0):.1f}",
                    f"{breakdown.get('aluminium_bars_needed', 0):.1f}",
                    f"{breakdown.get('aluminium_bars_cost', 0):.2f}",
                    f"{total:.2f}",
                    "OK"
                ])
        
        # Add summary row
        plan_summary = cost_result.get('plan_summary', {})
        total_cost = plan_summary.get('total_cost', 0)
        total_doors = plan_summary.get('total_doors', 0)
        total_windows = plan_summary.get('total_windows', 0)
        
        csv_data.append([])  # Empty row
        csv_data.append([
            "SUMMARY",
            "",
            "",
            "",
            "",
            "",
            "",
            f"{total_cost:.2f}",
            f"Total: {total_doors} doors, {total_windows} windows"
        ])
        
        # Write CSV file
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(csv_data)
        
        return output_path
        
    except (IOError, OSError) as e:
        raise IOError(f"CSV export error: {str(e)}")

def calculate_and_export_cost_csv(plan_json: str, output_path: str = None) -> str:
    """
    Calculate cost and export to CSV in one step.
    
    Args:
        plan_json: JSON string containing the plan data
        output_path: Optional path for CSV file
        
    Returns:
        Path to the generated CSV file
    """
    cost_result = calculate_plan_cost(plan_json)
    return export_cost_breakdown_to_csv(cost_result, output_path)
