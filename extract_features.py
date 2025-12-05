#!/usr/bin/env python3
"""
extract_features.py

Extract per-cell features from annotated cricket images.

Features per cell:
 - HOG (computed on grayscale)
 - HSV color histogram
 - LBP histogram

Saves outputs as CSV and/or NumPy .npz and stores sample visualizations and
intermediate grayscale / LBP images (optional, temporary).

Usage examples:
  python extract_features.py --csv path/to/cricket_labels.csv --images data/annotated&csv/annotated_images \
      --out-dir data/features --output-format both --padding 2 --save-intermediates

"""
import os
import argparse
import numpy as np
import pandas as pd
from PIL import Image
from skimage.feature import hog, local_binary_pattern
import matplotlib.pyplot as plt
from tqdm import tqdm
import json
import random


def ensure_dirs(d):
    os.makedirs(d, exist_ok=True)


def filename_to_annotated(name):
    """Map '192.jpg' -> 'annotated_192.png' when needed."""
    base = os.path.basename(name)
    if base.lower().endswith(('.jpg', '.jpeg', '.png')):
        num = ''.join([c for c in os.path.splitext(base)[0] if c.isdigit()])
        if num:
            return f"annotated_{num}.png"
    # fallback to the raw basename
    return base


def crop_cell(img_arr, r, c, cell_h, cell_w, pad=0):
    h, w = img_arr.shape[:2]
    left = max(0, c * cell_w - pad)
    top = max(0, r * cell_h - pad)
    right = min(w, (c + 1) * cell_w + pad)
    bottom = min(h, (r + 1) * cell_h + pad)
    cell = img_arr[top:bottom, left:right]
    
    # Resize to fixed size (cell_h, cell_w) to ensure consistent feature dimensions
    # This handles edge cells and padding variations
    if cell.shape[:2] != (cell_h, cell_w):
        cell = np.array(Image.fromarray(cell).resize((cell_w, cell_h), Image.LANCZOS))
    
    return cell


def color_hist_hsv(pil_img, h_bins=16, s_bins=8, v_bins=4):
    # PIL conversion to HSV (0-255 per channel)
    hsv = pil_img.convert('HSV')
    a = np.array(hsv)
    H = a[:, :, 0].ravel()
    S = a[:, :, 1].ravel()
    V = a[:, :, 2].ravel()
    h_hist, _ = np.histogram(H, bins=h_bins, range=(0, 256))
    s_hist, _ = np.histogram(S, bins=s_bins, range=(0, 256))
    v_hist, _ = np.histogram(V, bins=v_bins, range=(0, 256))
    hist = np.concatenate([h_hist, s_hist, v_hist]).astype(np.float32)
    # normalize
    s = hist.sum()
    if s > 0:
        hist /= s
    return hist


def lbp_histogram(gray_arr, P=8, R=1, method='uniform'):
    lbp = local_binary_pattern(gray_arr, P, R, method=method)
    n_bins = P + 2 if method == 'uniform' else int(lbp.max() + 1)
    hist, _ = np.histogram(lbp.ravel(), bins=n_bins, range=(0, n_bins))
    hist = hist.astype(np.float32)
    s = hist.sum()
    if s > 0:
        hist /= s
    return hist, lbp


def extract_features_row(cell_img_arr, hog_params, hsv_bins, lbp_params, debug_info=None):
    # cell_img_arr is an HxWx3 uint8 array (RGB)
    from skimage import color
    gray = np.array(Image.fromarray(cell_img_arr).convert('L'))

    # HOG on grayscale
    hog_vec = hog(
        gray,
        orientations=hog_params['orientations'],
        pixels_per_cell=hog_params['pixels_per_cell'],
        cells_per_block=hog_params['cells_per_block'],
        block_norm=hog_params.get('block_norm', 'L2-Hys'),
        feature_vector=True,
    )
    
    if debug_info is not None:
        debug_info['hog_size'] = len(hog_vec)

    # HSV color histogram
    pil_cell = Image.fromarray(cell_img_arr)
    hsv_hist = color_hist_hsv(pil_cell, *hsv_bins)

    # LBP histogram
    lbp_hist, lbp_map = lbp_histogram(gray, lbp_params['P'], lbp_params['R'], lbp_params.get('method', 'uniform'))

    features = np.concatenate([hog_vec, hsv_hist, lbp_hist]).astype(np.float32)
    return features, gray, lbp_map


def plot_sample_histograms(samples, out_path):
    # samples: list of dicts with keys: name, hsv_hist, lbp_hist
    n = len(samples)
    fig, axes = plt.subplots(n, 2, figsize=(10, 4 * n))
    if n == 1:
        axes = np.expand_dims(axes, 0)
    for i, s in enumerate(samples):
        ax_h = axes[i, 0]
        ax_l = axes[i, 1]
        # HSV histogram: split by channels
        hb = s['hsv_hist'][:s['h_bins']]
        sb = s['hsv_hist'][s['h_bins']:s['h_bins'] + s['s_bins']]
        vb = s['hsv_hist'][-s['v_bins']:]
        ax_h.bar(range(len(hb)), hb, color='red', alpha=0.6, label='H')
        ax_h.bar(range(len(hb), len(hb) + len(sb)), sb, color='green', alpha=0.6, label='S')
        ax_h.bar(range(len(hb) + len(sb), len(hb) + len(sb) + len(vb)), vb, color='blue', alpha=0.6, label='V')
        ax_h.set_title(f"HSV hist - {s['name']}")
        ax_h.legend()

        ax_l.bar(range(len(s['lbp_hist'])), s['lbp_hist'], color='gray')
        ax_l.set_title(f"LBP hist - {s['name']}")

    plt.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', required=True, help='Path to cricket_labels.csv')
    parser.add_argument('--images', required=True, help='Folder with annotated images')
    parser.add_argument('--out-dir', default=os.path.join('data', 'features'), help='Output folder')
    parser.add_argument('--output-format', choices=['csv', 'npz', 'both'], default='both')
    parser.add_argument('--padding', type=int, default=2, help='Padding (px) to add around each cell')
    parser.add_argument('--save-intermediates', action='store_true', help='Save grayscale and LBP maps for inspection')
    parser.add_argument('--sample-count', type=int, default=4, help='How many sample images to plot histograms for')
    args = parser.parse_args()

    ensure_dirs(args.out_dir)
    inter_dir = os.path.join(args.out_dir, 'intermediates')
    gray_dir = os.path.join(inter_dir, 'grayscale')
    lbp_dir = os.path.join(inter_dir, 'lbp_maps')
    analysis_dir = os.path.join(args.out_dir, 'feature_analysis')
    if args.save_intermediates:
        ensure_dirs(gray_dir)
        ensure_dirs(lbp_dir)
    ensure_dirs(analysis_dir)

    df = pd.read_csv(args.csv)
    # Expect first column image filename, second TrainOrTest, then 64 labels
    col0 = df.columns[0]
    labels_cols = df.columns[2:66] if len(df.columns) >= 66 else df.columns[2:]

    records = []
    X_list = []
    y_list = []
    meta_filenames = []
    meta_cell_idx = []
    cell_sizes_seen = {}  # Track (height, width) -> count
    hog_sizes_seen = {}   # Track HOG vector size -> count

    hog_params = {'orientations': 9, 'pixels_per_cell': (20, 20), 'cells_per_block': (2, 2)}
    hsv_bins = (16, 8, 4)  # H, S, V bins
    lbp_params = {'P': 8, 'R': 1, 'method': 'uniform'}

    sample_candidates = []

    # Process rows
    for _, row in tqdm(df.iterrows(), total=len(df), desc='Images'):
        img_name = str(row[col0])
        # Use original clean images from data/raw/ (not annotated images)
        img_path = os.path.join(args.images, img_name)
        if not os.path.exists(img_path):
            print(f"[INFO] Image not found: {img_path}")
            continue

        # Load image (should be 800x600)
        pil = Image.open(img_path).convert('RGB')
        arr = np.array(pil)
        h, w = arr.shape[:2]
        
        # Validate image dimensions
        if (h, w) != (600, 800):
            print(f"[WARNING] Image {img_name} has size {w}×{h} (expected 800×600). Skipping.")
            continue
        
        cell_h = h // 8
        cell_w = w // 8

        # For sample selection
        sample_candidates.append((img_name, img_path))

        for r in range(8):
            for c in range(8):
                idx = r * 8 + c
                if idx >= len(labels_cols):
                    label = 0
                else:
                    label = int(row[labels_cols[idx]]) if not pd.isna(row[labels_cols[idx]]) else 0

                cell = crop_cell(arr, r, c, cell_h, cell_w, pad=args.padding)
                debug_info = {}
                features, gray_map, lbp_map = extract_features_row(cell, hog_params, hsv_bins, lbp_params, debug_info=debug_info)
                
                # Track cell sizes and HOG sizes
                cell_size = cell.shape[:2]
                cell_sizes_seen[cell_size] = cell_sizes_seen.get(cell_size, 0) + 1
                hog_size = debug_info['hog_size']
                hog_sizes_seen[hog_size] = hog_sizes_seen.get(hog_size, 0) + 1

                X_list.append(features)
                y_list.append(label)
                meta_filenames.append(img_name)
                meta_cell_idx.append(idx)

                if args.save_intermediates:
                    # Save grayscale
                    g_p = os.path.join(gray_dir, f"{os.path.splitext(img_name)[0]}_cell{idx}.png")
                    Image.fromarray(gray_map).save(g_p)
                    # Save LBP map scaled to 0-255 for viewing
                    lbp_scaled = (255 * (lbp_map - lbp_map.min()) / max(1, (lbp_map.max() - lbp_map.min()))).astype(np.uint8)
                    lbp_p = os.path.join(lbp_dir, f"{os.path.splitext(img_name)[0]}_cell{idx}_lbp.png")
                    Image.fromarray(lbp_scaled).save(lbp_p)

    if len(X_list) == 0:
        print('[ERROR] No samples found. Exiting.')
        return
    
    # Diagnostics: report cell sizes and HOG sizes
    print(f"\n[DEBUG] Cell sizes distribution: {cell_sizes_seen}")
    print(f"[DEBUG] HOG vector sizes distribution: {hog_sizes_seen}")
    if len(hog_sizes_seen) > 1:
        print(f"[ERROR] Inconsistent HOG vector sizes detected. Cannot concatenate.")
        print(f"[INFO] This is likely due to edge cells with padding producing different sizes.")
        return

    X = np.vstack(X_list).astype(np.float32)
    y = np.array(y_list, dtype=np.int32)

    # Save outputs
    csv_out = os.path.join(args.out_dir, 'features.csv')
    npz_out = os.path.join(args.out_dir, 'features.npz')

    # Prepare CSV header
    feat_dim = X.shape[1]
    cols = ['image', 'cell_idx', 'label'] + [f'feat_{i}' for i in range(feat_dim)]
    # Write CSV in streaming fashion to avoid huge memory copies
    if args.output_format in ('csv', 'both'):
        with open(csv_out, 'w', encoding='utf-8') as fh:
            fh.write(','.join(cols) + '\n')
            for i in range(len(y)):
                row_vals = [meta_filenames[i], str(meta_cell_idx[i]), str(int(y[i]))] + [str(float(v)) for v in X[i].tolist()]
                fh.write(','.join(row_vals) + '\n')

    if args.output_format in ('npz', 'both'):
        np.savez_compressed(npz_out, X=X, y=y, filenames=np.array(meta_filenames), cell_idx=np.array(meta_cell_idx))

    # Dataset stats
    stats = {
        'num_samples': int(X.shape[0]),
        'feature_dim': int(feat_dim),
        'class_counts': {str(int(k)): int(v) for k, v in zip(*np.unique(y, return_counts=True))},
    }
    with open(os.path.join(args.out_dir, 'dataset_stats.json'), 'w', encoding='utf-8') as fh:
        json.dump(stats, fh, indent=2)

    # Produce sample histograms for a few images
    sample_n = min(args.sample_count, len(sample_candidates))
    chosen = random.sample(sample_candidates, sample_n)
    sample_data = []
    # Recompute histograms for chosen images (center cell)
    for (img_name, img_path) in chosen:
        pil = Image.open(img_path).convert('RGB')
        arr = np.array(pil)
        h, w = arr.shape[:2]
        cell_h = h // 8
        cell_w = w // 8
        r, c = 3, 3
        cell = crop_cell(arr, r, c, cell_h, cell_w, pad=args.padding)
        _, gray_map, lbp_map = extract_features_row(cell, hog_params, hsv_bins, lbp_params, debug_info=None)
        pil_cell = Image.fromarray(cell)
        hsv_hist = color_hist_hsv(pil_cell, *hsv_bins)
        lbp_hist, _ = lbp_histogram(gray_map, lbp_params['P'], lbp_params['R'], lbp_params.get('method', 'uniform'))
        sample_data.append({'name': img_name, 'hsv_hist': hsv_hist, 'lbp_hist': lbp_hist, 'h_bins': hsv_bins[0], 's_bins': hsv_bins[1], 'v_bins': hsv_bins[2]})

    if sample_data:
        plot_sample_histograms(sample_data, os.path.join(analysis_dir, 'sample_histograms.png'))

    print('[SUCCESS] Feature extraction complete.')
    print(f"[INFO] Saved: {csv_out if args.output_format in ('csv','both') else ''} {npz_out if args.output_format in ('npz','both') else ''}, dataset stats in {args.out_dir}")


if __name__ == '__main__':
    main()
