"""
Automated Annotation Tool using Traditional Computer Vision
Uses rule-based detection, shape analysis, and contour detection
NO CNNs or deep learning - only hand-crafted features and traditional CV
"""

import numpy as np
import cv2
from pathlib import Path
import json
from tqdm import tqdm
import argparse

from grid_processor import GridProcessor
from feature_extractor import HandCraftedFeatureExtractor


class AutoAnnotator:
    """Automated annotation using traditional CV techniques"""
    
    def __init__(self):
        self.grid_processor = GridProcessor()
        self.feature_extractor = HandCraftedFeatureExtractor()
        
        # Detection parameters
        self.circle_params = {
            'dp': 1,
            'minDist': 20,
            'param1': 50,
            'param2': 30,
            'minRadius': 5,
            'maxRadius': 40
        }
    
    def detect_circles(self, cell_image):
        """
        Detect circular objects (ball) using Hough Circle Transform
        Returns: list of (x, y, radius) tuples
        """
        gray = cv2.cvtColor(cell_image, cv2.COLOR_RGB2GRAY) if len(cell_image.shape) == 3 else cell_image
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Detect circles
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            **self.circle_params
        )
        
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            return circles.tolist()
        return []
    
    def detect_vertical_lines(self, cell_image):
        """
        Detect vertical lines (stumps) using Hough Line Transform
        Returns: number of significant vertical lines
        """
        gray = cv2.cvtColor(cell_image, cv2.COLOR_RGB2GRAY) if len(cell_image.shape) == 3 else cell_image
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Detect lines
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=10,
            minLineLength=20,
            maxLineGap=5
        )
        
        if lines is not None:
            # Count vertical lines (angle close to 90 degrees)
            vertical_count = 0
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if abs(x1 - x2) < 5:  # Nearly vertical
                    vertical_count += 1
            return vertical_count
        return 0
    
    def analyze_shape(self, cell_image):
        """
        Analyze shape characteristics to detect bat (elongated) or stump (vertical)
        Returns: dict with shape features
        """
        gray = cv2.cvtColor(cell_image, cv2.COLOR_RGB2GRAY) if len(cell_image.shape) == 3 else cell_image
        
        # Threshold to get binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'circularity': 0, 'aspect_ratio': 0, 'area_ratio': 0, 'verticality': 0}
        
        # Get largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        if area < 50:  # Too small
            return {'circularity': 0, 'aspect_ratio': 0, 'area_ratio': 0, 'verticality': 0}
        
        # Bounding rectangle
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Aspect ratio
        aspect_ratio = h / w if w > 0 else 0
        
        # Circularity
        perimeter = cv2.arcLength(largest_contour, True)
        if perimeter > 0:
            circularity = 4 * np.pi * area / (perimeter ** 2)
        else:
            circularity = 0
        
        # Area ratio
        total_area = cell_image.shape[0] * cell_image.shape[1]
        area_ratio = area / total_area
        
        # Verticality (how vertical the bounding box is)
        verticality = aspect_ratio if aspect_ratio > 1 else 1 / aspect_ratio if aspect_ratio > 0 else 0
        
        return {
            'circularity': circularity,
            'aspect_ratio': aspect_ratio,
            'area_ratio': area_ratio,
            'verticality': verticality,
            'area': area
        }
    
    def detect_by_color(self, cell_image):
        """
        Detect objects by color characteristics
        Returns: dominant color features
        """
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(cell_image, cv2.COLOR_RGB2HSV) if len(cell_image.shape) == 3 else cell_image
        
        if len(cell_image.shape) == 2:
            # Already grayscale
            return {'color_variance': np.var(cell_image), 'brightness': np.mean(cell_image)}
        
        # Analyze color distribution
        h_channel = hsv[:, :, 0]
        s_channel = hsv[:, :, 1]
        v_channel = hsv[:, :, 2]
        
        return {
            'color_variance': np.var(cell_image),
            'brightness': np.mean(v_channel),
            'saturation': np.mean(s_channel)
        }
    
    def classify_cell(self, cell_image):
        """
        Classify a grid cell using rule-based traditional CV methods
        Returns: predicted label (0=no_object, 1=ball, 2=bat, 3=stump)
        """
        # Check for empty/background cells
        gray = cv2.cvtColor(cell_image, cv2.COLOR_RGB2GRAY) if len(cell_image.shape) == 3 else cell_image
        edge_density = np.sum(cv2.Canny(gray, 50, 150) > 0) / (gray.shape[0] * gray.shape[1])
        
        # If very few edges, likely empty
        if edge_density < 0.05:
            return 0  # no_object
        
        # Analyze shape
        shape_features = self.analyze_shape(cell_image)
        
        # Detect circles (ball)
        circles = self.detect_circles(cell_image)
        
        # Detect vertical lines (stumps)
        vertical_lines = self.detect_vertical_lines(cell_image)
        
        # Get color features
        color_features = self.detect_by_color(cell_image)
        
        # Rule-based classification
        
        # 1. Check for ball (circular objects)
        if circles:
            # Found circles - likely a ball
            return 1  # ball
        
        circularity = shape_features.get('circularity', 0)
        area_ratio = shape_features.get('area_ratio', 0)
        
        if circularity > 0.7 and area_ratio > 0.1:
            # High circularity - likely ball
            return 1  # ball
        
        # 2. Check for stump (vertical lines or vertical objects)
        aspect_ratio = shape_features.get('aspect_ratio', 0)
        verticality = shape_features.get('verticality', 0)
        
        if vertical_lines >= 2:
            # Multiple vertical lines - likely stump
            return 3  # stump
        
        if aspect_ratio > 2.5 and verticality > 2.5 and area_ratio > 0.15:
            # Very vertical, significant area - likely stump
            return 3  # stump
        
        # 3. Check for bat (elongated, horizontal or diagonal)
        if 1.5 < aspect_ratio < 3.0 and area_ratio > 0.1:
            # Elongated but not too vertical - could be bat
            if verticality < 2.0:  # Not too vertical
                return 2  # bat
        
        # 4. Check by width vs height (bats are often horizontal/diagonal)
        if aspect_ratio < 0.7 and area_ratio > 0.15:
            # Wide object - could be bat from side view
            return 2  # bat
        
        # 5. Default to no_object if nothing matches
        if area_ratio < 0.05:
            return 0  # no_object
        
        # If we have significant content but unclear shape, make educated guess
        # Try to distinguish between bat and stump based on orientation
        if verticality > 2.0:
            return 3  # stump (more vertical)
        elif 0.5 < aspect_ratio < 2.0:
            return 2  # bat (more horizontal)
        
        return 0  # no_object (uncertain)
    
    def auto_annotate_image(self, image_path, confidence_threshold=0.5):
        """
        Automatically annotate all cells in an image
        Returns: dict with annotations
        """
        cells, cell_positions = self.grid_processor.divide_image_into_grid(image_path)
        
        annotations = {
            'cells': []
        }
        
        for cell, (row, col) in zip(cells, cell_positions):
            label = self.classify_cell(cell)
            
            annotations['cells'].append({
                'row': row,
                'col': col,
                'label': int(label),
                'method': 'auto_cv'  # Mark as auto-generated
            })
        
        return annotations
    
    def auto_annotate_directory(self, images_dir, output_path, confidence_threshold=0.5):
        """
        Automatically annotate all images in a directory
        Saves annotations to JSON file
        """
        images_dir = Path(images_dir)
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.JPG"))
        
        if len(image_files) == 0:
            raise ValueError(f"No images found in {images_dir}")
        
        print(f"Auto-annotating {len(image_files)} images...")
        
        all_annotations = {}
        
        for img_path in tqdm(image_files, desc="Annotating images"):
            try:
                annotations = self.auto_annotate_image(img_path, confidence_threshold)
                all_annotations[img_path.name] = annotations
            except Exception as e:
                print(f"\nError processing {img_path.name}: {str(e)}")
                continue
        
        # Save annotations
        with open(output_path, 'w') as f:
            json.dump(all_annotations, f, indent=2)
        
        print(f"\n✅ Annotations saved to {output_path}")
        
        # Print statistics
        self.print_statistics(all_annotations)
        
        return all_annotations
    
    def print_statistics(self, annotations):
        """Print annotation statistics"""
        label_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        label_names = {0: 'no_object', 1: 'ball', 2: 'bat', 3: 'stump'}
        
        for img_name, img_data in annotations.items():
            for cell in img_data['cells']:
                label = cell['label']
                label_counts[label] = label_counts.get(label, 0) + 1
        
        total = sum(label_counts.values())
        
        print("\n" + "=" * 60)
        print("Annotation Statistics:")
        print("=" * 60)
        for label, count in sorted(label_counts.items()):
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {label_names[label]:15s}: {count:6d} ({percentage:5.1f}%)")
        print(f"  {'Total':15s}: {total:6d}")
        print("=" * 60)
    
    def refine_with_feedback(self, annotations_path, manual_corrections):
        """
        Refine auto-annotations with manual feedback
        Useful for iterative improvement
        """
        with open(annotations_path, 'r') as f:
            annotations = json.load(f)
        
        # Apply manual corrections
        for img_name, corrections in manual_corrections.items():
            if img_name in annotations:
                for correction in corrections:
                    row = correction['row']
                    col = correction['col']
                    new_label = correction['label']
                    
                    # Find and update the cell
                    for cell in annotations[img_name]['cells']:
                        if cell['row'] == row and cell['col'] == col:
                            cell['label'] = new_label
                            cell['method'] = 'manual'
                            break
        
        return annotations


def main():
    """Main function for automated annotation"""
    parser = argparse.ArgumentParser(description='Automated annotation using traditional CV')
    parser.add_argument('--images_dir', type=str, default='data/processed',
                       help='Directory containing images to annotate')
    parser.add_argument('--output', type=str, default='auto_annotations.json',
                       help='Output JSON file for annotations')
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Confidence threshold (not used in current implementation)')
    parser.add_argument('--sample_size', type=int, default=None,
                       help='Process only first N images (for testing)')
    
    args = parser.parse_args()
    
    annotator = AutoAnnotator()
    
    images_dir = Path(args.images_dir)
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.JPG"))
    
    if args.sample_size:
        image_files = image_files[:args.sample_size]
        print(f"Processing sample of {len(image_files)} images...")
    
    annotations = annotator.auto_annotate_directory(
        images_dir,
        args.output,
        args.confidence
    )
    
    print(f"\n✅ Automated annotation complete!")
    print(f"   Annotations saved to: {args.output}")
    print(f"\nYou can now:")
    print(f"  1. Review and manually correct annotations in {args.output}")
    print(f"  2. Use for training: python train_model.py --annotations {args.output}")


if __name__ == "__main__":
    main()

