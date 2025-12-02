"""
Example usage of the grid cell classification system
This script demonstrates how to use the training and prediction modules
"""

from pathlib import Path
from grid_processor import GridProcessor
from feature_extractor import HandCraftedFeatureExtractor
import numpy as np


def example_grid_division():
    """Example: Divide an image into grid cells"""
    print("=" * 60)
    print("Example 1: Grid Division")
    print("=" * 60)
    
    processor = GridProcessor(grid_rows=8, grid_cols=8, 
                            image_width=800, image_height=600)
    
    # Find an image
    images_dir = Path("data/processed")
    image_files = list(images_dir.glob("*.jpg"))
    
    if image_files:
        sample_image = image_files[0]
        print(f"\nProcessing: {sample_image.name}")
        
        cells, positions = processor.divide_image_into_grid(sample_image)
        print(f"Divided into {len(cells)} cells (8×8 grid)")
        print(f"Each cell size: {processor.cell_width}×{processor.cell_height} pixels")
        
        print(f"\nFirst 5 cell positions: {positions[:5]}")
    else:
        print("No images found in data/processed")


def example_feature_extraction():
    """Example: Extract features from a grid cell"""
    print("\n" + "=" * 60)
    print("Example 2: Feature Extraction")
    print("=" * 60)
    
    extractor = HandCraftedFeatureExtractor()
    processor = GridProcessor()
    
    # Find an image
    images_dir = Path("data/processed")
    image_files = list(images_dir.glob("*.jpg"))
    
    if image_files:
        sample_image = image_files[0]
        print(f"\nProcessing: {sample_image.name}")
        
        cells, positions = processor.divide_image_into_grid(sample_image)
        
        if cells:
            # Extract features from first cell
            cell = cells[0]
            print(f"\nExtracting features from cell at position {positions[0]}")
            print(f"Cell shape: {cell.shape}")
            
            features = extractor.extract_all_features(cell)
            print(f"\nExtracted {len(features)} features")
            print(f"Feature vector shape: {features.shape}")
            print(f"Feature vector dtype: {features.dtype}")
            
            # Show breakdown
            print("\nFeature breakdown (approximate):")
            print("  - HOG features: ~36-324")
            print("  - LBP features: 10")
            print("  - Color histogram: 48")
            print("  - Texture features: 6")
            print("  - Edge features: 3")
            print("  - Shape features: 3")
    else:
        print("No images found in data/processed")


def example_training_command():
    """Example: Show training commands"""
    print("\n" + "=" * 60)
    print("Example 3: Training Commands")
    print("=" * 60)
    
    print("\nTo train the model, use:")
    print("\n1. Create annotation template:")
    print("   python train_model.py --create_template")
    
    print("\n2. Edit annotations_template.json to add labels")
    print("   (0=no_object, 1=ball, 2=bat, 3=stump)")
    
    print("\n3. Train with Random Forest:")
    print("   python train_model.py --images_dir data/processed \\")
    print("                         --annotations annotations.json \\")
    print("                         --team_name TeamIITB \\")
    print("                         --classifier random_forest")
    
    print("\n4. Train with SVM:")
    print("   python train_model.py --images_dir data/processed \\")
    print("                         --annotations annotations.json \\")
    print("                         --team_name TeamIITB \\")
    print("                         --classifier svm")


def example_prediction_command():
    """Example: Show prediction commands"""
    print("\n" + "=" * 60)
    print("Example 4: Prediction Commands")
    print("=" * 60)
    
    print("\nTo predict objects in an image, use:")
    print("\n   python predict.py --image data/processed/sample.jpg \\")
    print("                      --model model_TeamIITB.pkl \\")
    print("                      --output predictions.json")
    
    print("\nThis will:")
    print("  - Divide the image into 8×8 grid cells")
    print("  - Predict object class for each cell")
    print("  - Display results as a grid")
    print("  - Save detailed results to JSON (optional)")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Grid Cell Object Classification - Examples")
    print("=" * 60)
    
    try:
        example_grid_division()
        example_feature_extraction()
        example_training_command()
        example_prediction_command()
        
        print("\n" + "=" * 60)
        print("For more details, see TRAINING_GUIDE.md")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\nError running examples: {str(e)}")
        print("Make sure you have:")
        print("  1. Installed all dependencies: pip install -r requirements.txt")
        print("  2. Images in data/processed folder")

