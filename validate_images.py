"""
Image Validation Script
Checks if images in Original-Images folder match specifications:
- 4:3 aspect ratio
- 800x600 pixels resolution
- Deletes images that don't match (especially those < 800x600)
"""

import os
from pathlib import Path
from PIL import Image
import math

# Target specifications
TARGET_WIDTH = 800
TARGET_HEIGHT = 600
TARGET_ASPECT_RATIO = 4 / 3  # 1.333...
ASPECT_TOLERANCE = 0.01  # Small tolerance for floating point comparison

def check_aspect_ratio(width, height):
    """Check if image has 4:3 aspect ratio"""
    aspect_ratio = width / height
    return abs(aspect_ratio - TARGET_ASPECT_RATIO) < ASPECT_TOLERANCE

def validate_image(image_path):
    """
    Validate an image against specifications.
    Returns: (is_valid, reason)
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Check if resolution is lower than 800x600
            if width < TARGET_WIDTH or height < TARGET_HEIGHT:
                return False, f"Resolution too low: {width}x{height} (< 800x600)"
            
            # Check if exactly 800x600
            if width != TARGET_WIDTH or height != TARGET_HEIGHT:
                return False, f"Not 800x600: {width}x{height}"
            
            # Check aspect ratio
            if not check_aspect_ratio(width, height):
                return False, f"Not 4:3 aspect ratio: {width}x{height} (ratio: {width/height:.3f})"
            
            return True, "Valid"
            
    except Exception as e:
        return False, f"Error reading image: {str(e)}"

def main():
    # Get the Original-Images folder path
    base_path = Path("Dataset")
    
    if not base_path.exists():
        print(f"Error: {base_path} folder not found!")
        return
    
    # Find all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(base_path.rglob(f"*{ext}"))
    
    print(f"Found {len(image_files)} image files in {base_path}")
    print("-" * 80)
    
    valid_images = []
    deleted_images = []
    
    for image_path in image_files:
        is_valid, reason = validate_image(image_path)
        
        if is_valid:
            valid_images.append(image_path)
            print(f"✓ VALID: {image_path.name}")
        else:
            print(f"✗ INVALID: {image_path.name} - {reason}")
            try:
                image_path.unlink()  # Delete the file
                deleted_images.append(image_path)
                print(f"  → Deleted")
            except Exception as e:
                print(f"  → Error deleting: {str(e)}")
    
    print("-" * 80)
    print(f"\nSummary:")
    print(f"  Total images found: {len(image_files)}")
    print(f"  Valid images (kept): {len(valid_images)}")
    print(f"  Invalid images (deleted): {len(deleted_images)}")
    print(f"\n✓ Final dataset contains {len(valid_images)} images")

if __name__ == "__main__":
    main()

