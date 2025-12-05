#!/usr/bin/env python3
"""
visualize_tsne.py

Apply t-SNE to visualize high-dimensional feature space in 2D.
Can be applied to either raw features or PCA-reduced features.

t-SNE (t-Distributed Stochastic Neighbor Embedding) is useful for:
- Visualizing class separability
- Detecting clusters and outliers
- Understanding feature space structure

Usage:
  # Visualize PCA features (recommended - faster and often better):
  python visualize_tsne.py --input data/features/features_train_pca.npz --output data/features/tsne_pca.png --perplexity 30

  # Visualize raw features (slower):
  python visualize_tsne.py --input data/features/features.npz --output data/features/tsne_raw.png --perplexity 50

Arguments:
  --input: Path to NPZ file (features.npz, features_train_pca.npz, etc.)
  --output: Path to save plot (PNG)
  --perplexity: t-SNE perplexity (5-50, default 30). Higher = focuses on global structure
  --n-samples: Max samples to use (default 5000). t-SNE is slow on large datasets
  --random-seed: Random seed for reproducibility (default 42)

"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input NPZ file')
    parser.add_argument('--output', default='data/features/tsne_plot.png', help='Output plot path')
    parser.add_argument('--perplexity', type=int, default=30, help='t-SNE perplexity (5-50)')
    parser.add_argument('--n-samples', type=int, default=5000, help='Max samples to use (t-SNE is slow)')
    parser.add_argument('--random-seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    print(f"[INFO] Loading features from {args.input}...")
    data = np.load(args.input)
    X = data['X']
    y = data['y']

    print(f"[INFO] Original shape: {X.shape}")
    print(f"[INFO] Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    # Subsample if needed (t-SNE is O(n²) so slow on large datasets)
    if len(X) > args.n_samples:
        print(f"[INFO] Subsampling {args.n_samples} samples for t-SNE (original: {len(X)})...")
        np.random.seed(args.random_seed)
        idx = np.random.choice(len(X), args.n_samples, replace=False)
        X_sub = X[idx]
        y_sub = y[idx]
    else:
        X_sub = X
        y_sub = y

    print(f"[INFO] Applying t-SNE (perplexity={args.perplexity})...")
    print(f"[INFO] This may take a few minutes for {len(X_sub)} samples...")
    tsne = TSNE(n_components=2, perplexity=args.perplexity, random_state=args.random_seed, verbose=1)
    X_tsne = tsne.fit_transform(X_sub)

    print(f"[SUCCESS] t-SNE complete. Shape: {X_tsne.shape}")

    # Plot
    print(f"[INFO] Generating visualization...")
    fig, ax = plt.subplots(figsize=(12, 10))

    class_names = {0: 'None', 1: 'Ball', 2: 'Bat', 3: 'Stumps'}
    colors = {0: 'lightgray', 1: 'red', 2: 'blue', 3: 'green'}
    markers = {0: '.', 1: 'o', 2: '^', 3: 's'}

    for cls in np.unique(y_sub):
        mask = y_sub == cls
        ax.scatter(
            X_tsne[mask, 0], 
            X_tsne[mask, 1],
            c=colors[cls],
            marker=markers[cls],
            label=f'{class_names[cls]} (n={mask.sum()})',
            alpha=0.6 if cls == 0 else 0.8,
            s=20 if cls == 0 else 60,
            edgecolors='black' if cls != 0 else 'none',
            linewidth=0.5
        )

    ax.set_xlabel('t-SNE Component 1', fontsize=14)
    ax.set_ylabel('t-SNE Component 2', fontsize=14)
    ax.set_title(f't-SNE Visualization (perplexity={args.perplexity}, n={len(X_sub)})', 
                 fontsize=16, fontweight='bold')
    ax.legend(fontsize=12, loc='best', framealpha=0.9)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    fig.savefig(args.output, dpi=150)
    plt.close(fig)

    print(f"[SUCCESS] Plot saved to {args.output}")
    print(f"\n[SUMMARY]")
    print(f"  Input features: {X.shape[1]} dimensions")
    print(f"  Samples visualized: {len(X_sub)}")
    print(f"  Output: {args.output}")
    print(f"\n[INTERPRETATION TIPS]")
    print(f"  - Tight clusters = class is well-separated in feature space")
    print(f"  - Overlapping points = classes are hard to distinguish")
    print(f"  - Class 0 (None) likely dominates due to imbalance (~90%)")


if __name__ == '__main__':
    main()
