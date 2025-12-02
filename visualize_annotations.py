"""
Visualization tool to review automated annotations
Shows grid cells with predicted labels overlaid on images
"""

import numpy as np
import cv2
from pathlib import Path
import json
import argparse
from PIL import Image, ImageDraw, ImageFont

from grid_processor import GridProcessor


class AnnotationVisualizer:
    """Visualize annotations on images"""
    
    def __init__(self):
        self.grid_processor = GridProcessor()
        self.label_colors = {
            0: (128, 128, 128),  # Gray - no object
            1: (255, 0, 0),      # Red - ball
            2: (0, 255, 0),      # Green - bat
            3: (0, 0, 255)       # Blue - stump
        }
        self.label_names = {
            0: 'none',
            1: 'ball',
            2: 'bat',
            3: 'stump'
        }
    
    def draw_grid_and_labels(self, image_path, annotations, output_path=None, 
                            show_labels=True, show_grid=True):
        """
        Draw grid and labels on an image
        """
        # Load image
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        if img.size != (800, 600):
            img = img.resize((800, 600), Image.LANCZOS)
        
        # Create drawing context
        draw = ImageDraw.Draw(img)
        
        # Draw grid
        if show_grid:
            for row in range(9):  # 8 cells = 9 lines
                y = row * self.grid_processor.cell_height
                draw.line([(0, y), (800, y)], fill=(200, 200, 200), width=1)
            
            for col in range(9):
                x = col * self.grid_processor.cell_width
                draw.line([(x, 0), (x, 600)], fill=(200, 200, 200), width=1)
        
        # Draw cell labels
        if show_labels:
            for cell in annotations.get('cells', []):
                row = cell['row']
                col = cell['col']
                label = cell['label']
                
                # Get cell coordinates
                x_start = col * self.grid_processor.cell_width
                y_start = row * self.grid_processor.cell_height
                x_end = (col + 1) * self.grid_processor.cell_width
                y_end = (row + 1) * self.grid_processor.cell_height
                
                # Draw semi-transparent rectangle
                overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                
                color = self.label_colors.get(label, (128, 128, 128))
                overlay_draw.rectangle(
                    [x_start, y_start, x_end, y_end],
                    fill=(*color, 64)  # Semi-transparent
                )
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                draw = ImageDraw.Draw(img)
                
                # Draw label text
                if label > 0:  # Only show labels for non-empty cells
                    label_text = self.label_names.get(label, '?')
                    
                    # Calculate text position (center of cell)
                    text_x = x_start + (x_end - x_start) // 2
                    text_y = y_start + (y_end - y_start) // 2
                    
                    # Draw text with background
                    bbox = draw.textbbox((text_x, text_y), label_text)
                    draw.rectangle(bbox, fill=(255, 255, 255, 200))
                    draw.text((text_x, text_y), label_text, fill=(0, 0, 0), anchor='mm')
        
        # Save or return
        if output_path:
            img.save(output_path)
            print(f"Saved visualization to {output_path}")
        
        return img
    
    def visualize_annotations_file(self, annotations_file, images_dir, 
                                  output_dir=None, max_images=10):
        """
        Visualize annotations for all images in the annotations file
        """
        # Load annotations
        with open(annotations_file, 'r') as f:
            all_annotations = json.load(f)
        
        images_dir = Path(images_dir)
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
        
        print(f"Visualizing annotations for {min(len(all_annotations), max_images)} images...")
        
        for idx, (img_name, annotations) in enumerate(all_annotations.items()):
            if idx >= max_images:
                break
            
            img_path = images_dir / img_name
            
            if not img_path.exists():
                print(f"Warning: {img_name} not found, skipping...")
                continue
            
            if output_dir:
                output_path = output_dir / f"vis_{img_name}"
            else:
                output_path = None
            
            self.draw_grid_and_labels(img_path, annotations, output_path)
        
        print(f"\n✅ Visualization complete!")
        if output_dir:
            print(f"   Visualizations saved to {output_dir}")
    
    def compare_annotations(self, image_path, annotations1, annotations2, output_path=None):
        """
        Compare two sets of annotations side by side
        """
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        if img.size != (800, 600):
            img = img.resize((800, 600), Image.LANCZOS)
        
        # Create side-by-side comparison
        comparison = Image.new('RGB', (1600, 600))
        
        # Draw first set of annotations
        img1 = self.draw_grid_and_labels(image_path, annotations1, show_labels=True)
        comparison.paste(img1, (0, 0))
        
        # Draw second set of annotations
        img2 = self.draw_grid_and_labels(image_path, annotations2, show_labels=True)
        comparison.paste(img2, (800, 0))
        
        if output_path:
            comparison.save(output_path)
            print(f"Comparison saved to {output_path}")
        
        return comparison


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Visualize annotations')
    parser.add_argument('--annotations', type=str, required=True,
                       help='Annotations JSON file')
    parser.add_argument('--images_dir', type=str, default='data/processed',
                       help='Directory containing images')
    parser.add_argument('--output_dir', type=str, default='visualizations',
                       help='Output directory for visualizations')
    parser.add_argument('--max_images', type=int, default=10,
                       help='Maximum number of images to visualize')
    parser.add_argument('--image', type=str, default=None,
                       help='Visualize single image (optional)')
    
    args = parser.parse_args()
    
    visualizer = AnnotationVisualizer()
    
    if args.image:
        # Visualize single image
        annotations_file = Path(args.annotations)
        with open(annotations_file, 'r') as f:
            all_annotations = json.load(f)
        
        img_path = Path(args.images_dir) / args.image
        if args.image in all_annotations:
            output_path = Path(args.output_dir) / f"vis_{args.image}"
            Path(args.output_dir).mkdir(exist_ok=True)
            
            visualizer.draw_grid_and_labels(
                img_path,
                all_annotations[args.image],
                output_path
            )
        else:
            print(f"Image {args.image} not found in annotations file")
    else:
        # Visualize all images
        visualizer.visualize_annotations_file(
            args.annotations,
            args.images_dir,
            args.output_dir,
            args.max_images
        )


if __name__ == "__main__":
    main()

