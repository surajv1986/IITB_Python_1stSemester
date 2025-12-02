"""
Grid Processor - Divides images into 8x8 grid cells
"""

import numpy as np
from PIL import Image
import cv2


class GridProcessor:
    """Process images by dividing them into grid cells"""
    
    def __init__(self, grid_rows=8, grid_cols=8, image_width=800, image_height=600):
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.image_width = image_width
        self.image_height = image_height
        
        # Calculate cell dimensions
        self.cell_width = image_width // grid_cols  # 100 pixels
        self.cell_height = image_height // grid_rows  # 75 pixels
    
    def divide_image_into_grid(self, image_path):
        """
        Divide an image into grid cells
        Returns: List of cell images and their positions (row, col)
        """
        # Load image
        img = Image.open(image_path)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to expected dimensions if needed
        if img.size != (self.image_width, self.image_height):
            img = img.resize((self.image_width, self.image_height), Image.LANCZOS)
        
        # Convert to numpy array
        img_array = np.array(img)
        
        cells = []
        cell_positions = []
        
        # Extract each grid cell
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                # Calculate cell boundaries
                y_start = row * self.cell_height
                y_end = (row + 1) * self.cell_height
                x_start = col * self.cell_width
                x_end = (col + 1) * self.cell_width
                
                # Extract cell
                cell = img_array[y_start:y_end, x_start:x_end]
                
                cells.append(cell)
                cell_positions.append((row, col))
        
        return cells, cell_positions
    
    def get_cell_coordinates(self, row, col):
        """Get pixel coordinates for a grid cell"""
        y_start = row * self.cell_height
        y_end = (row + 1) * self.cell_height
        x_start = col * self.cell_width
        x_end = (col + 1) * self.cell_width
        return (x_start, y_start, x_end, y_end)

