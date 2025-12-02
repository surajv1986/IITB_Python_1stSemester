"""
Hand-crafted Feature Extraction for Grid Cells
Extracts features without using CNNs or automatic feature extraction
"""

import numpy as np
from skimage import feature, filters, exposure
from skimage.feature import hog, local_binary_pattern
import cv2


class HandCraftedFeatureExtractor:
    """Extract hand-crafted features from image cells"""
    
    def __init__(self):
        self.feature_names = []
    
    def extract_hog_features(self, image, orientations=9, pixels_per_cell=(8, 8), 
                            cells_per_block=(2, 2)):
        """
        Extract Histogram of Oriented Gradients (HOG) features
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Extract HOG features
        hog_features = hog(
            gray,
            orientations=orientations,
            pixels_per_cell=pixels_per_cell,
            cells_per_block=cells_per_block,
            block_norm='L2-Hys',
            visualize=False,
            feature_vector=True
        )
        return hog_features
    
    def extract_lbp_features(self, image, num_points=8, radius=1):
        """
        Extract Local Binary Pattern (LBP) features
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Compute LBP
        lbp = local_binary_pattern(gray, num_points, radius, method='uniform')
        
        # Calculate histogram
        n_bins = num_points + 2
        hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins))
        
        # Normalize
        hist = hist.astype(float)
        hist /= (hist.sum() + 1e-7)
        
        return hist
    
    def extract_color_histogram(self, image, bins=32):
        """
        Extract color histogram features from RGB channels
        """
        histograms = []
        
        # Extract histogram for each channel
        for channel_idx in range(3):
            channel = image[:, :, channel_idx]
            hist, _ = np.histogram(channel, bins=bins, range=(0, 256))
            # Normalize
            hist = hist.astype(float)
            hist /= (hist.sum() + 1e-7)
            histograms.append(hist)
        
        return np.concatenate(histograms)
    
    def extract_texture_features(self, image):
        """
        Extract texture-based features (variance, entropy, etc.)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        features = []
        
        # Variance
        features.append(np.var(gray))
        
        # Standard deviation
        features.append(np.std(gray))
        
        # Mean
        features.append(np.mean(gray))
        
        # Entropy (using histogram)
        hist, _ = np.histogram(gray.ravel(), bins=256, range=(0, 256))
        hist = hist[hist > 0]  # Remove zeros
        entropy = -np.sum((hist / hist.sum()) * np.log2(hist / hist.sum()))
        features.append(entropy)
        
        # Contrast (using standard deviation)
        features.append(np.std(gray))
        
        # Energy (squared sum of pixel values)
        energy = np.sum(gray.astype(float) ** 2) / (gray.shape[0] * gray.shape[1])
        features.append(energy)
        
        return np.array(features)
    
    def extract_edge_features(self, image):
        """
        Extract edge-based features using Canny edge detector
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        features = []
        
        # Edge density (percentage of edge pixels)
        edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
        features.append(edge_density)
        
        # Mean edge strength
        # Apply Sobel for edge strength
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge_strength = np.sqrt(sobelx**2 + sobely**2)
        features.append(np.mean(edge_strength))
        features.append(np.std(edge_strength))
        
        return np.array(features)
    
    def extract_shape_features(self, image):
        """
        Extract shape-based features
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Threshold to get binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        features = []
        
        # Calculate moments
        moments = cv2.moments(binary)
        
        # Central moments
        if moments['m00'] != 0:
            # Normalized central moments
            nu20 = moments.get('nu20', 0)
            nu02 = moments.get('nu02', 0)
            nu11 = moments.get('nu11', 0)
            
            # Hu moments (first 2 for simplicity)
            hu1 = nu20 + nu02
            hu2 = (nu20 - nu02)**2 + 4*nu11**2
            
            features.extend([hu1, hu2])
        else:
            features.extend([0, 0])
        
        # Area ratio (non-zero pixels / total pixels)
        area_ratio = np.sum(binary > 0) / (binary.shape[0] * binary.shape[1])
        features.append(area_ratio)
        
        return np.array(features[:3])  # Return first 3 features
    
    def extract_all_features(self, image):
        """
        Extract all hand-crafted features from an image cell
        Returns a feature vector
        """
        features = []
        
        # Ensure image is in RGB format
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        elif image.shape[2] == 1:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        
        # Resize if too small for HOG
        if image.shape[0] < 16 or image.shape[1] < 16:
            image = cv2.resize(image, (16, 16))
        
        try:
            # HOG features
            hog_feat = self.extract_hog_features(image, orientations=9, 
                                                pixels_per_cell=(4, 4) if min(image.shape[:2]) < 32 else (8, 8),
                                                cells_per_block=(2, 2))
            features.extend(hog_feat)
        except:
            # Fallback for very small images
            features.extend([0] * 36)  # Approximate HOG feature size
        
        # LBP features
        try:
            lbp_feat = self.extract_lbp_features(image, num_points=8, radius=1)
            features.extend(lbp_feat)
        except:
            features.extend([0] * 10)
        
        # Color histogram features
        try:
            color_feat = self.extract_color_histogram(image, bins=16)
            features.extend(color_feat)
        except:
            features.extend([0] * 48)
        
        # Texture features
        try:
            texture_feat = self.extract_texture_features(image)
            features.extend(texture_feat)
        except:
            features.extend([0] * 6)
        
        # Edge features
        try:
            edge_feat = self.extract_edge_features(image)
            features.extend(edge_feat)
        except:
            features.extend([0] * 3)
        
        # Shape features
        try:
            shape_feat = self.extract_shape_features(image)
            features.extend(shape_feat)
        except:
            features.extend([0] * 3)
        
        return np.array(features, dtype=np.float32)

