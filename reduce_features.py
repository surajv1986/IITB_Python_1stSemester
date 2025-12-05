#!/usr/bin/env python3
"""
reduce_features.py

Apply PCA (Principal Component Analysis) to reduce feature dimensions while retaining
variance (information content).

Background:
- Raw features from extract_features.py: HOG (normalized per block), HSV histogram 
  (normalized to sum=1), LBP histogram (normalized to sum=1)
- Although features are normalized, they are NOT standardized (zero mean, unit variance)
- PCA requires standardization for optimal performance (features on same scale)
- This script standardizes features, applies PCA, and visualizes explained variance

Usage:
  python reduce_features.py --input data/features/features.npz --output data/features/features_reduced.npz --variance 0.95

Arguments:
  --input: Path to input NPZ file (default: data/features/features.npz)
  --output: Path to output NPZ file (default: data/features/features_reduced.npz)
  --variance: Variance threshold to retain, 0-1 (default: 0.95 = 95%)
  
Outputs:
  - features_reduced.npz: Reduced features with PCA transformation
  - features_reduced_stats.json: Statistics (dimensions, variance, class counts)
  - pca_variance_plot.png: Explained variance per component + cumulative variance
  - pca_scaler.npz: StandardScaler parameters (mean, std) for future transforms

"""
import argparse
import numpy as np
import json
import os
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='data/features/features.npz', help='Input NPZ file')
    parser.add_argument('--output-dir', default='data/features', help='Output directory')
    parser.add_argument('--variance', type=float, default=0.95, help='Variance to retain (0-1)')
    parser.add_argument('--test-size', type=float, default=0.3, help='Test set size (0-1)')
    parser.add_argument('--random-seed', type=int, default=42, help='Random seed for reproducibility')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"[INFO] Loading features from {args.input}...")
    data = np.load(args.input)
    X = data['X']
    y = data['y']
    filenames = data['filenames']
    cell_idx = data['cell_idx']

    print(f"[INFO] Original shape: {X.shape}")
    print(f"[INFO] Original feature dimension: {X.shape[1]}")
    print(f"[INFO] Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # Split train/test (stratified by class to preserve class distribution)
    print(f"[INFO] Splitting data: {(1-args.test_size)*100:.0f}% train / {args.test_size*100:.0f}% test (stratified)...")
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, np.arange(len(y)), 
        test_size=args.test_size, 
        random_state=args.random_seed, 
        stratify=y
    )
    filenames_train = filenames[idx_train]
    filenames_test = filenames[idx_test]
    cell_idx_train = cell_idx[idx_train]
    cell_idx_test = cell_idx[idx_test]

    print(f"[INFO] Train samples: {len(y_train)} | Test samples: {len(y_test)}")
    print(f"[INFO] Train class distribution: {dict(zip(*np.unique(y_train, return_counts=True)))}")
    print(f"[INFO] Test class distribution: {dict(zip(*np.unique(y_test, return_counts=True)))}")

    # Standardize features (fit on train, transform both)
    print(f"[INFO] Standardizing features (fit on train only)...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print(f"[INFO] Train - mean range: [{X_train_scaled.mean(axis=0).min():.6f}, {X_train_scaled.mean(axis=0).max():.6f}]")
    print(f"[INFO] Train - std range: [{X_train_scaled.std(axis=0).min():.6f}, {X_train_scaled.std(axis=0).max():.6f}]")

    # Apply PCA (fit on train, transform both)
    print(f"[INFO] Applying PCA to retain {args.variance*100:.1f}% variance (fit on train only)...")
    pca = PCA(n_components=args.variance, random_state=args.random_seed)
    X_train_pca = pca.fit_transform(X_train_scaled)
    X_test_pca = pca.transform(X_test_scaled)

    n_components = pca.n_components_
    explained_var = pca.explained_variance_ratio_.sum()
    print(f"[SUCCESS] Reduced to {n_components} dimensions")
    print(f"[INFO] Explained variance: {explained_var:.4f} ({explained_var*100:.2f}%)")
    print(f"[INFO] First 10 components explain: {pca.explained_variance_ratio_[:10].sum()*100:.2f}%")
    print(f"[INFO] Train PCA shape: {X_train_pca.shape} | Test PCA shape: {X_test_pca.shape}")

    # Plot explained variance
    print(f"[INFO] Generating PCA variance plots...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Individual explained variance per component
    ax1 = axes[0]
    components_range = np.arange(1, min(51, n_components + 1))  # First 50 or all if less
    ax1.bar(components_range, pca.explained_variance_ratio_[:len(components_range)], alpha=0.7, color='steelblue')
    ax1.set_xlabel('Principal Component', fontsize=12)
    ax1.set_ylabel('Explained Variance Ratio', fontsize=12)
    ax1.set_title('Explained Variance per Component (First 50)', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # Cumulative explained variance
    ax2 = axes[1]
    cumsum = np.cumsum(pca.explained_variance_ratio_)
    ax2.plot(np.arange(1, n_components + 1), cumsum, marker='o', markersize=3, linewidth=2, color='darkgreen')
    ax2.axhline(y=args.variance, color='red', linestyle='--', linewidth=2, label=f'{args.variance*100:.0f}% threshold')
    ax2.axhline(y=0.99, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='99% threshold')
    ax2.set_xlabel('Number of Components', fontsize=12)
    ax2.set_ylabel('Cumulative Explained Variance', fontsize=12)
    ax2.set_title('Cumulative Explained Variance', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    plot_path = os.path.join(args.output_dir, 'pca_variance_plot.png')
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)
    print(f"[SUCCESS] Variance plot saved to {plot_path}")

    # Find components for 99% variance
    idx_99 = np.argmax(cumsum >= 0.99) + 1 if 0.99 <= cumsum[-1] else n_components
    print(f"[INFO] {idx_99} components explain 99% variance")

    # Save reduced features (train and test separately)
    print(f"[INFO] Saving reduced features...")
    train_path = os.path.join(args.output_dir, 'features_train_pca.npz')
    test_path = os.path.join(args.output_dir, 'features_test_pca.npz')
    
    np.savez_compressed(
        train_path,
        X=X_train_pca.astype(np.float32),
        y=y_train,
        filenames=filenames_train,
        cell_idx=cell_idx_train,
        n_components=n_components,
        explained_variance_ratio=pca.explained_variance_ratio_.astype(np.float32),
    )
    
    np.savez_compressed(
        test_path,
        X=X_test_pca.astype(np.float32),
        y=y_test,
        filenames=filenames_test,
        cell_idx=cell_idx_test,
        n_components=n_components,
        explained_variance_ratio=pca.explained_variance_ratio_.astype(np.float32),
    )
    
    print(f"[SUCCESS] Train features saved to {train_path}")
    print(f"[SUCCESS] Test features saved to {test_path}")

    # Save scaler and PCA for future transforms
    scaler_path = os.path.join(args.output_dir, 'pca_scaler.npz')
    pca_path = os.path.join(args.output_dir, 'pca_model.npz')
    np.savez_compressed(scaler_path, mean=scaler.mean_, scale=scaler.scale_)
    np.savez_compressed(pca_path, 
                       components=pca.components_,
                       mean=pca.mean_,
                       explained_variance=pca.explained_variance_,
                       explained_variance_ratio=pca.explained_variance_ratio_)
    print(f"[SUCCESS] Scaler saved to {scaler_path}")
    print(f"[SUCCESS] PCA model saved to {pca_path}")

    # Save stats
    stats = {
        'original_dimension': int(X.shape[1]),
        'reduced_dimension': int(n_components),
        'variance_retained': float(explained_var),
        'components_for_99_percent': int(idx_99),
        'train_samples': int(len(y_train)),
        'test_samples': int(len(y_test)),
        'test_size_ratio': float(args.test_size),
        'random_seed': int(args.random_seed),
        'train_class_counts': {str(int(k)): int(v) for k, v in zip(*np.unique(y_train, return_counts=True))},
        'test_class_counts': {str(int(k)): int(v) for k, v in zip(*np.unique(y_test, return_counts=True))},
        'top_10_components_variance': [float(v) for v in pca.explained_variance_ratio_[:10].tolist()],
    }
    stats_file = os.path.join(args.output_dir, 'pca_split_stats.json')
    with open(stats_file, 'w', encoding='utf-8') as fh:
        json.dump(stats, fh, indent=2)

    print(f"[SUCCESS] Stats saved to {stats_file}")
    print(f"\n[SUMMARY]")
    print(f"  Original features: {X.shape[1]}")
    print(f"  PCA features: {n_components} (retains {explained_var*100:.2f}% variance)")
    print(f"  Train: {len(y_train)} samples | Test: {len(y_test)} samples")
    print(f"  Files: {train_path}, {test_path}")
    print(f"  Plot: {plot_path}")
    print(f"  Stats: {stats_file}")


if __name__ == '__main__':
    main()
