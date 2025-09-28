import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from service.image import get_image_summary

def door_summary(image: str):
    # Get image summary
    # Get door dimensions in dynamic JSON format 
    # Get BOMs (if any) in dynamic JSON format
    # For each door
        # Get material cost for typical profiles (GALA 66, PROBBA, GALA NORMAL)
        # Get material cost for typical leaf (glass-based: DHC)
        # Get material cost for typical hardware: locks, handles, hinge.
    image_summary = get_image_summary(image)
    print(image_summary)