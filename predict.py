"""
Prediction Script - Use trained model to predict objects in grid cells
"""

import pickle
import numpy as np
from pathlib import Path
from PIL import Image
import argparse
import json

from feature_extractor import HandCraftedFeatureExtractor
from grid_processor import GridProcessor


def load_model(model_path):
    """Load the trained model"""
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    return model_data


def predict_image_grid(image_path, model_data, output_json=None):
    """
    Predict objects for all grid cells in an image
    Returns grid predictions as 8x8 array
    """
    # Extract components from model
    classifier = model_data['classifier']
    scaler = model_data['scaler']
    feature_extractor = model_data['feature_extractor']
    grid_processor = model_data['grid_processor']
    label_map = model_data.get('label_map', {0: 'no_object', 1: 'ball', 2: 'bat', 3: 'stump'})
    
    # Divide image into grid
    cells, cell_positions = grid_processor.divide_image_into_grid(image_path)
    
    # Initialize prediction grid
    predictions = np.zeros((8, 8), dtype=int)
    probabilities_grid = {}
    
    print(f"Processing {Path(image_path).name}...")
    
    # Predict each cell
    for cell, (row, col) in zip(cells, cell_positions):
        # Extract features
        features = feature_extractor.extract_all_features(cell)
        features = features.reshape(1, -1)
        
        # Scale
        features_scaled = scaler.transform(features)
        
        # Predict
        prediction = classifier.predict(features_scaled)[0]
        probabilities = classifier.predict_proba(features_scaled)[0]
        
        predictions[row, col] = prediction
        
        # Store probabilities
        probabilities_grid[f"{row}_{col}"] = {
            label_map.get(i, f"class_{i}"): float(prob) 
            for i, prob in enumerate(probabilities)
        }
    
    # Print results
    print("\nGrid Predictions (8×8):")
    print("   ", end="")
    for col in range(8):
        print(f"{col:>4}", end="")
    print()
    
    for row in range(8):
        print(f"{row:2} ", end="")
        for col in range(8):
            pred = predictions[row, col]
            label = label_map.get(pred, f"class_{pred}")
            symbol = {0: ".", 1: "B", 2: "T", 3: "S"}.get(pred, "?")
            print(f"{symbol:>4}", end="")
        print()
    
    print("\nLegend: . = no_object, B = ball, T = bat, S = stump")
    
    # Save to JSON if requested
    if output_json:
        result = {
            'image': Path(image_path).name,
            'predictions': predictions.tolist(),
            'probabilities': probabilities_grid,
            'label_map': {str(k): v for k, v in label_map.items()}
        }
        
        with open(output_json, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nResults saved to {output_json}")
    
    return predictions, probabilities_grid


def main():
    """Main prediction function"""
    parser = argparse.ArgumentParser(description='Predict objects in grid cells')
    parser.add_argument('--image', type=str, required=True,
                       help='Path to image file')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to trained model file (.pkl)')
    parser.add_argument('--output', type=str, default=None,
                       help='Path to save JSON output (optional)')
    
    args = parser.parse_args()
    
    # Load model
    print(f"Loading model from {args.model}...")
    try:
        model_data = load_model(args.model)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return
    
    # Predict
    try:
        predictions, probabilities = predict_image_grid(
            args.image, 
            model_data, 
            args.output
        )
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()

