"""
Main Training Script for Grid Cell Classification
Trains a model to classify objects in 8x8 grid cells: 0=no object, 1=ball, 2=bat, 3=stump
"""

import numpy as np
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import json
import os
from tqdm import tqdm

from feature_extractor import HandCraftedFeatureExtractor
from grid_processor import GridProcessor


class GridCellClassifier:
    """Train and manage classifier for grid cell object detection"""
    
    def __init__(self, team_name="TeamIITB"):
        self.team_name = team_name
        self.feature_extractor = HandCraftedFeatureExtractor()
        self.grid_processor = GridProcessor()
        self.scaler = StandardScaler()
        self.classifier = None
        self.label_map = {0: 'no_object', 1: 'ball', 2: 'bat', 3: 'stump'}
        self.reverse_label_map = {v: k for k, v in self.label_map.items()}
    
    def load_annotations(self, annotations_path):
        """
        Load annotations from JSON file
        Expected format:
        {
            "image_filename.jpg": {
                "cells": [
                    {"row": 0, "col": 0, "label": 1},
                    {"row": 0, "col": 1, "label": 0},
                    ...
                ]
            },
            ...
        }
        """
        if not os.path.exists(annotations_path):
            raise FileNotFoundError(f"Annotations file not found: {annotations_path}")
        
        with open(annotations_path, 'r') as f:
            annotations = json.load(f)
        
        return annotations
    
    def prepare_training_data(self, images_dir, annotations_path=None):
        """
        Prepare training data from images and annotations
        If annotations_path is None, creates empty labels for manual annotation
        """
        images_dir = Path(images_dir)
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.JPG"))
        
        if len(image_files) == 0:
            raise ValueError(f"No images found in {images_dir}")
        
        print(f"Found {len(image_files)} images")
        
        # Load annotations if provided
        annotations = None
        if annotations_path and os.path.exists(annotations_path):
            annotations = self.load_annotations(annotations_path)
            print(f"Loaded annotations from {annotations_path}")
        
        features_list = []
        labels_list = []
        image_info = []  # Store image filename and cell position for reference
        
        print("\nExtracting features from grid cells...")
        
        for img_path in tqdm(image_files, desc="Processing images"):
            try:
                # Divide image into grid cells
                cells, cell_positions = self.grid_processor.divide_image_into_grid(img_path)
                
                img_name = img_path.name
                
                for cell, (row, col) in zip(cells, cell_positions):
                    # Extract features
                    features = self.feature_extractor.extract_all_features(cell)
                    features_list.append(features)
                    image_info.append({
                        'image': img_name,
                        'row': row,
                        'col': col
                    })
                    
                    # Get label from annotations if available
                    if annotations and img_name in annotations:
                        cell_annotations = annotations[img_name].get('cells', [])
                        # Find matching cell annotation
                        label = 0  # Default: no object
                        for cell_ann in cell_annotations:
                            if cell_ann.get('row') == row and cell_ann.get('col') == col:
                                label = cell_ann.get('label', 0)
                                break
                        labels_list.append(label)
                    else:
                        # No annotation available - will need manual labeling
                        labels_list.append(-1)  # Use -1 to indicate unlabeled
                        
            except Exception as e:
                print(f"\nError processing {img_path.name}: {str(e)}")
                continue
        
        features_array = np.array(features_list)
        labels_array = np.array(labels_list)
        
        print(f"\nExtracted features shape: {features_array.shape}")
        print(f"Labels shape: {labels_array.shape}")
        
        if annotations:
            unique, counts = np.unique(labels_array, return_counts=True)
            print("\nLabel distribution:")
            for label, count in zip(unique, counts):
                label_name = self.label_map.get(label, f"Unknown({label})")
                print(f"  {label_name}: {count}")
        
        return features_array, labels_array, image_info
    
    def train(self, X, y, test_size=0.2, classifier_type='random_forest', 
              save_scaler=True):
        """
        Train the classifier
        classifier_type: 'random_forest' or 'svm'
        """
        print(f"\nTraining {classifier_type} classifier...")
        
        # Filter out unlabeled data
        labeled_mask = y != -1
        X_labeled = X[labeled_mask]
        y_labeled = y[labeled_mask]
        
        if len(X_labeled) == 0:
            raise ValueError("No labeled data available for training!")
        
        print(f"Training with {len(X_labeled)} labeled samples")
        
        # Split into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(
            X_labeled, y_labeled, test_size=test_size, random_state=42, stratify=y_labeled
        )
        
        # Scale features
        print("Scaling features...")
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Initialize classifier
        if classifier_type == 'random_forest':
            self.classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'
            )
        elif classifier_type == 'svm':
            self.classifier = SVC(
                kernel='rbf',
                C=10.0,
                gamma='scale',
                probability=True,
                random_state=42,
                class_weight='balanced'
            )
        else:
            raise ValueError(f"Unknown classifier type: {classifier_type}")
        
        # Train
        print("Fitting classifier...")
        self.classifier.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.classifier.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\nTest Accuracy: {accuracy:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, 
                                  target_names=[self.label_map[i] for i in sorted(self.label_map.keys())]))
        
        print("\nConfusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        return accuracy
    
    def save_model(self, model_path=None):
        """Save the trained model"""
        if self.classifier is None:
            raise ValueError("Model not trained yet!")
        
        if model_path is None:
            model_path = f"model_{self.team_name}.pkl"
        
        model_data = {
            'classifier': self.classifier,
            'scaler': self.scaler,
            'feature_extractor': self.feature_extractor,
            'grid_processor': self.grid_processor,
            'label_map': self.label_map,
            'team_name': self.team_name
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"\nModel saved to {model_path}")
        return model_path
    
    def predict_cell(self, cell_image):
        """Predict label for a single cell image"""
        if self.classifier is None:
            raise ValueError("Model not trained yet!")
        
        # Extract features
        features = self.feature_extractor.extract_all_features(cell_image)
        features = features.reshape(1, -1)
        
        # Scale
        features_scaled = self.scaler.transform(features)
        
        # Predict
        prediction = self.classifier.predict(features_scaled)[0]
        probabilities = self.classifier.predict_proba(features_scaled)[0]
        
        return prediction, probabilities


def create_sample_annotation_template(images_dir, output_path="annotations_template.json"):
    """Create a template annotation file for manual labeling"""
    images_dir = Path(images_dir)
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.JPG"))
    
    template = {}
    grid_processor = GridProcessor()
    
    print("Creating annotation template...")
    print("Label values: 0=no_object, 1=ball, 2=bat, 3=stump")
    
    for img_path in image_files[:5]:  # Create template for first 5 images
        template[img_path.name] = {
            "cells": []
        }
        
        # Create empty cells
        for row in range(8):
            for col in range(8):
                template[img_path.name]["cells"].append({
                    "row": row,
                    "col": col,
                    "label": 0  # Default: no object
                })
    
    with open(output_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"\nAnnotation template saved to {output_path}")
    print("Please edit this file to add labels, then use it for training.")


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train grid cell classifier')
    parser.add_argument('--images_dir', type=str, default='data/processed',
                       help='Directory containing training images')
    parser.add_argument('--annotations', type=str, default=None,
                       help='Path to annotations JSON file (optional)')
    parser.add_argument('--team_name', type=str, default='TeamIITB',
                       help='Team name for model filename')
    parser.add_argument('--classifier', type=str, default='random_forest',
                       choices=['random_forest', 'svm'],
                       help='Classifier type to use')
    parser.add_argument('--create_template', action='store_true',
                       help='Create annotation template file')
    
    args = parser.parse_args()
    
    # Create annotation template if requested
    if args.create_template:
        create_sample_annotation_template(args.images_dir)
        return
    
    # Initialize classifier
    classifier = GridCellClassifier(team_name=args.team_name)
    
    # Prepare training data
    try:
        X, y, image_info = classifier.prepare_training_data(
            args.images_dir, 
            args.annotations
        )
    except Exception as e:
        print(f"Error preparing training data: {str(e)}")
        print("\nIf you don't have annotations yet, run with --create_template first")
        return
    
    # Check if we have labels
    if np.all(y == -1):
        print("\n⚠️  No annotations found! All cells are unlabeled.")
        print("Options:")
        print("1. Create annotation template: python train_model.py --create_template")
        print("2. Provide annotations file: python train_model.py --annotations annotations.json")
        return
    
    # Train model
    try:
        accuracy = classifier.train(X, y, classifier_type=args.classifier)
        model_path = classifier.save_model()
        print(f"\n✅ Training complete! Model saved to {model_path}")
    except Exception as e:
        print(f"Error during training: {str(e)}")
        raise


if __name__ == "__main__":
    main()

