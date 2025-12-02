"""
Enhanced Automated Annotation using Unsupervised Clustering
Groups similar cells together and provides semi-automated labeling
NO CNNs - uses hand-crafted features + clustering
"""

import numpy as np
import json
from pathlib import Path
from tqdm import tqdm
import argparse
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

from grid_processor import GridProcessor
from feature_extractor import HandCraftedFeatureExtractor
from auto_annotate import AutoAnnotator


class ClusteringAnnotator:
    """
    Uses clustering to group similar cells, then applies labels
    Useful for batch annotation and finding patterns
    """
    
    def __init__(self):
        self.grid_processor = GridProcessor()
        self.feature_extractor = HandCraftedFeatureExtractor()
        self.auto_annotator = AutoAnnotator()
        self.scaler = StandardScaler()
    
    def extract_all_features_batch(self, images_dir, max_images=None):
        """
        Extract features from all cells in all images
        Returns: features array, image_info list
        """
        images_dir = Path(images_dir)
        image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.JPG"))
        
        if max_images:
            image_files = image_files[:max_images]
        
        all_features = []
        image_info = []
        
        print(f"Extracting features from {len(image_files)} images...")
        
        for img_path in tqdm(image_files, desc="Extracting features"):
            try:
                cells, cell_positions = self.grid_processor.divide_image_into_grid(img_path)
                
                for cell, (row, col) in zip(cells, cell_positions):
                    features = self.feature_extractor.extract_all_features(cell)
                    all_features.append(features)
                    image_info.append({
                        'image': img_path.name,
                        'row': row,
                        'col': col
                    })
            except Exception as e:
                print(f"\nError processing {img_path.name}: {str(e)}")
                continue
        
        return np.array(all_features), image_info
    
    def cluster_cells(self, features, n_clusters=8, method='kmeans'):
        """
        Cluster cells based on their features
        Returns: cluster labels
        """
        print(f"\nClustering cells using {method}...")
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        if method == 'kmeans':
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = clusterer.fit_predict(features_scaled)
        
        elif method == 'dbscan':
            clusterer = DBSCAN(eps=0.5, min_samples=5)
            cluster_labels = clusterer.fit_predict(features_scaled)
        
        else:
            raise ValueError(f"Unknown clustering method: {method}")
        
        unique_clusters = np.unique(cluster_labels)
        print(f"Found {len(unique_clusters)} clusters")
        
        return cluster_labels, clusterer
    
    def auto_label_clusters(self, cluster_labels, image_info, n_sample_per_cluster=3):
        """
        Automatically label clusters by analyzing sample cells from each cluster
        Returns: dict mapping cluster_id -> predicted_label
        """
        unique_clusters = np.unique(cluster_labels)
        cluster_labels_map = {}
        
        print("\nAuto-labeling clusters...")
        
        # Group cells by cluster
        clusters_dict = {}
        for idx, cluster_id in enumerate(cluster_labels):
            if cluster_id not in clusters_dict:
                clusters_dict[cluster_id] = []
            clusters_dict[cluster_id].append(idx)
        
        # For each cluster, sample cells and predict
        for cluster_id in tqdm(unique_clusters, desc="Labeling clusters"):
            if cluster_id == -1:  # Noise in DBSCAN
                cluster_labels_map[cluster_id] = 0  # Default to no_object
                continue
            
            cell_indices = clusters_dict[cluster_id]
            
            # Sample a few cells from this cluster
            sample_size = min(n_sample_per_cluster, len(cell_indices))
            sample_indices = np.random.choice(cell_indices, sample_size, replace=False)
            
            # Predict labels for sampled cells
            predictions = []
            images_dir = Path("data/processed")
            
            for idx in sample_indices:
                info = image_info[idx]
                img_path = images_dir / info['image']
                
                try:
                    cells, positions = self.grid_processor.divide_image_into_grid(img_path)
                    
                    # Find the corresponding cell
                    for cell, (row, col) in zip(cells, positions):
                        if row == info['row'] and col == info['col']:
                            pred = self.auto_annotator.classify_cell(cell)
                            predictions.append(pred)
                            break
                except:
                    continue
            
            if predictions:
                # Use most common prediction for the cluster
                cluster_labels_map[cluster_id] = int(np.bincount(predictions).argmax())
            else:
                cluster_labels_map[cluster_id] = 0  # Default
        
        return cluster_labels_map
    
    def create_annotations_from_clusters(self, cluster_labels, cluster_labels_map, 
                                        image_info, images_dir):
        """
        Create annotation JSON from cluster assignments
        """
        images_dir = Path(images_dir)
        
        # Group by image
        images_dict = {}
        
        for idx, info in enumerate(image_info):
            img_name = info['image']
            
            if img_name not in images_dict:
                images_dict[img_name] = {
                    'cells': []
                }
            
            cluster_id = cluster_labels[idx]
            predicted_label = cluster_labels_map.get(cluster_id, 0)
            
            images_dict[img_name]['cells'].append({
                'row': info['row'],
                'col': info['col'],
                'label': predicted_label,
                'cluster': int(cluster_id),
                'method': 'clustering'
            })
        
        return images_dict
    
    def annotate_with_clustering(self, images_dir, output_path, 
                                n_clusters=8, method='kmeans', 
                                max_images=None):
        """
        Main method: Annotate using clustering approach
        """
        # Extract features
        features, image_info = self.extract_all_features_batch(images_dir, max_images)
        
        print(f"\nExtracted {len(features)} cell feature vectors")
        print(f"Feature dimension: {features.shape[1]}")
        
        # Cluster
        cluster_labels, clusterer = self.cluster_cells(features, n_clusters, method)
        
        # Auto-label clusters
        cluster_labels_map = self.auto_label_clusters(cluster_labels, image_info)
        
        # Create annotations
        annotations = self.create_annotations_from_clusters(
            cluster_labels, cluster_labels_map, image_info, images_dir
        )
        
        # Save
        with open(output_path, 'w') as f:
            json.dump(annotations, f, indent=2)
        
        print(f"\n✅ Clustering-based annotations saved to {output_path}")
        
        # Print statistics
        self.print_cluster_statistics(cluster_labels, cluster_labels_map)
        
        return annotations
    
    def print_cluster_statistics(self, cluster_labels, cluster_labels_map):
        """Print cluster statistics"""
        unique_clusters = np.unique(cluster_labels)
        label_names = {0: 'no_object', 1: 'ball', 2: 'bat', 3: 'stump'}
        
        print("\n" + "=" * 60)
        print("Cluster Statistics:")
        print("=" * 60)
        
        for cluster_id in sorted(unique_clusters):
            count = np.sum(cluster_labels == cluster_id)
            label = cluster_labels_map.get(cluster_id, 0)
            label_name = label_names.get(label, f"Unknown({label})")
            
            print(f"  Cluster {cluster_id:2d}: {count:5d} cells -> {label_name}")
        
        print("=" * 60)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Clustering-based annotation')
    parser.add_argument('--images_dir', type=str, default='data/processed',
                       help='Directory containing images')
    parser.add_argument('--output', type=str, default='cluster_annotations.json',
                       help='Output JSON file')
    parser.add_argument('--n_clusters', type=int, default=8,
                       help='Number of clusters for K-means')
    parser.add_argument('--method', type=str, default='kmeans',
                       choices=['kmeans', 'dbscan'],
                       help='Clustering method')
    parser.add_argument('--max_images', type=int, default=None,
                       help='Process only first N images (for testing)')
    
    args = parser.parse_args()
    
    annotator = ClusteringAnnotator()
    
    annotations = annotator.annotate_with_clustering(
        args.images_dir,
        args.output,
        args.n_clusters,
        args.method,
        args.max_images
    )
    
    print(f"\n✅ Clustering annotation complete!")
    print(f"You can now use these annotations for training.")


if __name__ == "__main__":
    main()

