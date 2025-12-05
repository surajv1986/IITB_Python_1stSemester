import os
from PIL import Image
import concurrent.futures

# --- Configuration ---
# Source folder for raw images (set by DATA_DIR env var)
script_dir = os.path.dirname(os.path.abspath(__file__))
raw_folder = os.getenv('DATA_DIR', os.path.join(script_dir, 'data', 'raw'))
# Output folder for processed images (size_processed by default)
processed_folder = os.getenv('PROCESSED_DIR', os.path.join(script_dir, 'data', 'size_processed'))
os.makedirs(processed_folder, exist_ok=True)

# Target dimensions and aspect ratio
TARGET_WIDTH = 800
TARGET_HEIGHT = 600
TARGET_RATIO = TARGET_WIDTH / TARGET_HEIGHT  # 4:3

def processed_exists(filepath):
    """Check if processed image already exists in processed_folder."""
    base = os.path.splitext(os.path.basename(filepath))[0]
    out_path = os.path.join(processed_folder, f"{base}_processed.jpg")
    return os.path.exists(out_path)

def process_image(filepath):
    """
    Crop image to 4:3 aspect ratio (center crop, no black bars), 
    then downsize to 800x600, and save to processed_folder.
    """
    try:
        if processed_exists(filepath):
            print(f"[INFO] Skipping already processed: {filepath}")
            return
        with Image.open(filepath) as img:
            # Convert to RGB if necessary (e.g., for PNGs with transparency)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get current dimensions and ratio
            width, height = img.size
            current_ratio = width / height
            
            if width == TARGET_WIDTH and height == TARGET_HEIGHT:
                print(f"[INFO] Skipping {filepath} - already 800x600")
                return
            
            # Step 1: Crop to 4:3 aspect ratio (center crop, no black bars)
            if current_ratio > TARGET_RATIO:
                # Image is wider than 4:3 - crop left and right
                crop_width = int(height * TARGET_RATIO)
                left = (width - crop_width) // 2
                top = 0
                crop_box = (left, top, left + crop_width, top + height)
            else:
                # Image is taller than 4:3 - crop top and bottom
                crop_height = int(width / TARGET_RATIO)
                left = 0
                top = (height - crop_height) // 2
                crop_box = (left, top, left + width, top + crop_height)
            
            cropped = img.crop(crop_box)
            
            # Step 2: Downsize to 800x600
            resized = cropped.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
            
            # Step 3: Save to processed_folder
            base = os.path.splitext(os.path.basename(filepath))[0]
            out_path = os.path.join(processed_folder, f"{base}_processed.jpg")
            resized.save(out_path, quality=95)
            print(f"[SUCCESS] Processed {filepath} -> {out_path}")
            
    except Exception as e:
        print(f"[ERROR] Failed to process {filepath}: {e}")

def main():
    """Find all images in raw_folder and process them in parallel, skipping already processed files."""
    # Find all image files in raw_folder
    image_files = [os.path.join(raw_folder, f) for f in os.listdir(raw_folder)
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    if not image_files:
        print("[INFO] No images found to process")
        return
    
    print(f"[INFO] Found {len(image_files)} images to process")
    
    # Process images in parallel
    max_workers = min(32, (os.cpu_count() or 4) * 4)
    print(f"[INFO] Processing images with {max_workers} workers...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_image, f) for f in image_files]
        try:
            concurrent.futures.wait(futures)
        except KeyboardInterrupt:
            print("[INFO] Processing interrupted by user")
            executor.shutdown(cancel_futures=True)
            return
    
    print("[INFO] Processing complete")

if __name__ == '__main__':
    main()