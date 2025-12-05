# Cricket Image Dataset: Scraping, Processing & Feature Extraction Pipeline

A complete end-to-end pipeline for cricket image dataset creation and feature extraction from ESPNCricinfo galleries. Downloads images, processes them to consistent dimensions, extracts per-cell features (HOG, HSV, LBP), applies dimensionality reduction (PCA), and prepares train/test splits for machine learning.

## Table of Contents
- [Features](#features)
- [Pipeline Overview](#pipeline-overview)
- [Setup](#setup)
- [Step-by-Step Workflow](#step-by-step-workflow)
- [Script Reference](#script-reference)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Troubleshooting](#troubleshooting)

## Features

**Image Collection & Processing:**
- Automated scraping of cricket images from ESPNCricinfo galleries
- Concurrent downloads with atomic file writes
- Automatic Chrome/Selenium driver management
- Center-crop to 4:3 aspect ratio and resize to 800×600 (no black bars)
- High-quality LANCZOS resampling
- Progress tracking and comprehensive logging

**Feature Extraction:**
- Per-cell (8×8 grid) feature extraction from annotated images
- HOG (Histogram of Oriented Gradients) on grayscale
- HSV color histograms
- LBP (Local Binary Pattern) histograms
- Outputs: CSV, compressed NPZ, and visualization plots

**Dimensionality Reduction & Visualization:**
- PCA (Principal Component Analysis) with proper train/test splitting
- StandardScaler preprocessing (zero mean, unit variance)
- t-SNE visualization for class separability analysis
- Variance explained plots and statistics

**Data Pipeline Best Practices:**
- Train/test splitting (70/30 stratified by class)
- Fit transformations on training data only (no data leakage)
- Separate train/test output files ready for classifier training
- Comprehensive statistics and metadata preservation

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Image Collection (img_downloader_self.py)              │
│ ESPNCricinfo galleries → data/raw/                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Image Processing (process_images.py)                   │
│ Center-crop + resize → data/size_processed/ (800×600)          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Manual Annotation (external tool)                      │
│ Annotate images in 8×8 grid → data/annotated&csv/             │
│ Labels: 0=none, 1=ball, 2=bat, 3=stumps                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Feature Extraction (extract_features.py)               │
│ HOG + HSV + LBP per cell → data/features/features.npz          │
│ Output: 19,264 samples × 326 features                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: PCA & Train/Test Split (reduce_features.py)           │
│ StandardScaler + PCA (95% variance) → 133 components           │
│ Outputs: features_train_pca.npz, features_test_pca.npz        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Visualization (visualize_tsne.py)                      │
│ t-SNE 2D projection → tsne_pca_all.png                         │
│ Analyze class separability before classification               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Classification (future: train_classifier.py)           │
│ Train ML models (Random Forest, SVM, etc.) on train set        │
│ Evaluate on test set with metrics and confusion matrix         │
└─────────────────────────────────────────────────────────────────┘
```

## Setup

### Prerequisites
- Python 3.8 or newer
- Chrome browser (for Selenium scraping)
- Recommended: 4GB+ RAM for PCA and t-SNE

### Installation

1. **Clone or download this repository**

2. **Create a Python virtual environment** (recommended):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # On Windows PowerShell
# On Linux/Mac: source .venv/bin/activate
```

3. **Install dependencies**:
```powershell
python -m pip install -r requirements.txt
```

Dependencies include:
- `selenium`, `webdriver-manager` (web scraping)
- `requests`, `beautifulsoup4` (HTTP and HTML parsing)
- `Pillow` (image processing)
- `numpy`, `pandas` (data handling)
- `scikit-learn` (PCA, StandardScaler, train/test split)
- `scikit-image` (HOG, LBP feature extraction)
- `matplotlib` (plotting)
- `tqdm` (progress bars)

4. **Verify Chrome is installed** (required for Selenium WebDriver)

## Step-by-Step Workflow

### Phase 1: Image Collection & Processing

#### Step 1.1: Download Images from ESPNCricinfo

Run the scraper to download raw images:

```powershell
python img_downloader_self.py
```

**What it does:**
- Scrolls through ESPNCricinfo gallery pages
- Collects `/gallery/` links (up to `MAX_LINKS` galleries)
- Downloads high-resolution images concurrently (up to `MAX_DOWNLOADS`)
- Filters images by minimum size (≥800×600)
- Saves to `data/raw/`
- Uses atomic writes (`.part` files) to avoid corruption

**Configuration** (edit at top of `img_downloader_self.py`):
- `MAX_LINKS = 50` — Number of gallery pages to scan
- `MAX_DOWNLOADS = 900` — Maximum images to download
- `SCROLL_PAUSE = 2` — Delay between page scrolls (seconds)

**Output:**
- `data/raw/*.jpg` — Downloaded images

---

#### Step 1.2: Process Images to 800×600

Center-crop and resize all downloaded images:

```powershell
python process_images.py
```

**What it does:**
- Loads images from `data/raw/`
- Center-crops to 4:3 aspect ratio (removes excess width/height, no black bars)
- Resizes to exactly 800×600 using high-quality LANCZOS resampling
- Skips already-processed images
- Saves to `data/size_processed/`

**Output:**
- `data/size_processed/*.jpg` — Processed 800×600 images

---

#### Step 1.3: Run Full Pipeline (Alternative)

Run both steps at once with logging:

```powershell
python run_pipeline.py
```

**What it does:**
- Runs `img_downloader_self.py` → downloads to `data/raw/`
- Runs `process_images.py` → processes to `data/size_processed/`
- Logs all output to `pipeline.log`
- Prints summary report (image counts, errors, file locations)

**Output:**
- `data/raw/*.jpg`, `data/size_processed/*.jpg`
- `pipeline.log` — Full execution log

---

### Phase 2: Annotation (Manual Step)

**Manual annotation is required** before feature extraction. Use an image annotation tool to label each 800×600 image in an **8×8 grid** (64 cells per image).

**Label codes:**
- `0` = No object
- `1` = Ball
- `2` = Bat
- `3` = Stumps

**CSV format:**
```csv
ImageFileName,TrainOrTest,c01,c02,c03,...,c64
192.jpg,Train,0,0,1,0,...,2
```

**File locations:**
- **Original images:** `data/raw/` (clean 800×600 images without visual annotations)
- **CSV labels:** `data/annotated&csv/cricket_labels.csv`
- **Annotated images:** `data/annotated&csv/annotated_images/` (for reference only, not used in feature extraction)

**Important:** Feature extraction uses the **clean images from `data/raw/`**, not the annotated images. The annotated images are only for visual reference.

---

### Phase 3: Feature Extraction

#### Step 3.1: Extract Features (HOG + HSV + LBP)

Extract per-cell features from **clean images** in `data/raw/` using labels from CSV:

```powershell
python extract_features.py `
  --csv "data/annotated&csv/cricket_labels.csv" `
  --images "data/raw" `
  --out-dir "data/features" `
  --output-format both `
  --padding 0 `
  --save-intermediates
```

**What it does:**
- Reads labels from `cricket_labels.csv` (e.g., `192.jpg`)
- Loads corresponding **clean images from `data/raw/`** (not annotated images)
- Validates image dimensions (must be 800×600)
- Divides each image into 8×8 grid (64 cells)
- Extracts per-cell features:
  - **HOG (Histogram of Oriented Gradients)**: 
    - Computed on grayscale
    - `orientations=9`, `pixels_per_cell=(20,20)`, `cells_per_block=(2,2)`
    - Block-normalized (L2-Hys)
  - **HSV Color Histogram**: 
    - 16 H bins + 8 S bins + 4 V bins = 28 features
    - Normalized to sum=1 (probability distribution)
  - **LBP (Local Binary Pattern) Histogram**:
    - P=8, R=1, uniform method
    - 10 bins, normalized to sum=1
- Total features per cell: ~326 dimensions
- Outputs CSV and/or compressed NPZ

**Parameters:**
- `--csv`: Path to labels CSV
- `--images`: Folder with clean images (use `data/raw`, not annotated images)
- `--out-dir`: Output directory (default: `data/features`)
- `--output-format`: `csv`, `npz`, or `both`
- `--padding`: Pixel padding around each cell (default: 0, recommended)
- `--save-intermediates`: Save grayscale and LBP maps for inspection

**Output:**
- `data/features/features.csv` — Per-sample feature vectors (19,264 rows × 329 columns)
- `data/features/features.npz` — Compressed NumPy arrays (X, y, filenames, cell_idx)
- `data/features/dataset_stats.json` — Class counts and feature dimension
- `data/features/feature_analysis/sample_histograms.png` — Sample HSV/LBP histograms
- `data/features/intermediates/` — (Optional) Grayscale and LBP maps per cell

**Example stats:**
- Samples: 19,264 (301 images × 64 cells)
- Features: 326 dimensions
- Classes: {0: 17,497, 1: 139, 2: 743, 3: 885} — heavily imbalanced!

---

### Phase 4: Dimensionality Reduction & Data Splitting

#### Step 4.1: Apply PCA with Train/Test Split

Reduce dimensions and prepare ML-ready datasets:

```powershell
python reduce_features.py `
  --input data/features/features.npz `
  --output-dir data/features `
  --variance 0.95 `
  --test-size 0.3 `
  --random-seed 42
```

**What it does:**
1. **Load features** from `features.npz` (19,264 samples × 326 features)
2. **Split train/test** (70/30) with stratification to preserve class balance
3. **Standardize** features (fit StandardScaler on train only):
   - Zero mean, unit variance
   - Transform both train and test with fitted scaler
4. **Apply PCA** (fit on train only):
   - Retain 95% variance (default: ~133 components)
   - Transform both train and test with fitted PCA
5. **Save outputs**:
   - Separate train/test NPZ files
   - Scaler and PCA model for future transforms
   - Variance explained plot (individual + cumulative)
   - Comprehensive stats JSON

**Parameters:**
- `--input`: Input NPZ file (from extract_features.py)
- `--output-dir`: Output directory (default: `data/features`)
- `--variance`: Variance threshold to retain, 0-1 (default: 0.95 = 95%)
- `--test-size`: Test set fraction, 0-1 (default: 0.3 = 30%)
- `--random-seed`: Random seed for reproducibility (default: 42)

**Output:**
- `data/features/features_train_pca.npz` — Training set (13,484 × 133)
- `data/features/features_test_pca.npz` — Test set (5,780 × 133)
- `data/features/pca_scaler.npz` — StandardScaler parameters (mean, scale)
- `data/features/pca_model.npz` — PCA model (components, explained_variance)
- `data/features/pca_variance_plot.png` — Variance explained plots
- `data/features/pca_split_stats.json` — Full statistics:
  ```json
  {
    "original_dimension": 326,
    "reduced_dimension": 133,
    "variance_retained": 0.9506,
    "components_for_99_percent": 133,
    "train_samples": 13484,
    "test_samples": 5780,
    "train_class_counts": {...},
    "test_class_counts": {...}
  }
  ```

**Key Results:**
- **326 → 133 dimensions** (59% reduction)
- **95.06% variance retained**
- First 10 components explain ~45% of variance
- 133 components needed for 99% variance (at 95% threshold, already >99%)

---

### Phase 5: Visualization & Analysis

#### Step 5.1: t-SNE Visualization

Visualize high-dimensional feature space in 2D:

```powershell
# Visualize PCA-reduced training data (recommended)
python visualize_tsne.py `
  --input data/features/features_train_pca.npz `
  --output data/features/tsne_pca_train.png `
  --perplexity 30 `
  --n-samples 5000

# Or visualize all training samples (slower, 5-15 min)
python visualize_tsne.py `
  --input data/features/features_train_pca.npz `
  --output data/features/tsne_pca_all.png `
  --perplexity 30 `
  --n-samples 15000
```

**What it does:**
- Applies t-SNE to reduce 133 PCA dimensions → 2D
- Creates scatter plot colored by class
- Shows class separability and potential clusters
- Useful for understanding feature space structure before training classifiers

**Parameters:**
- `--input`: Input NPZ file (raw features or PCA-reduced)
- `--output`: Output PNG path
- `--perplexity`: t-SNE perplexity, 5-50 (default: 30)
  - Lower: focuses on local structure
  - Higher: focuses on global structure
- `--n-samples`: Max samples to visualize (default: 5000)
  - t-SNE is O(n²), very slow on large datasets
  - Use 5000-10000 for quick results, 15000+ for full dataset
- `--random-seed`: Random seed (default: 42)

**Output:**
- `data/features/tsne_*.png` — 2D scatter plot with class colors

**Interpretation:**
- **Tight, separated clusters** → classes are well-separated → classification should work well
- **Overlapping regions** → classes are hard to distinguish → challenging classification
- **Class 0 dominates visually** due to 90% imbalance (expected)

---

### Phase 6: Classification (Future Work)

**Next step:** Train machine learning classifiers on the prepared train/test splits.

Suggested models:
- Random Forest with class weights (handles imbalance)
- SVM with RBF kernel
- Gradient Boosting (XGBoost, LightGBM)
- Neural Network with weighted loss

Evaluation metrics (due to class imbalance):
- **F1-score** (macro-averaged or per-class)
- **Precision/Recall** per class
- **Confusion matrix**
- Avoid accuracy (misleading with imbalance)

Future script: `train_classifier.py` (to be implemented)

You can also run the scripts separately:

1. Download images:
```powershell
python img_downloader_self.py
```

2. Process downloaded images to 800x600:
```powershell
python process_images.py
```

### Custom Save Location

To save images in a different location:

```powershell
$env:DATA_DIR = "C:\path\to\your\folder"
python run_pipeline.py
```

## Configuration

Key settings in `img_downloader_self.py`:
- `MAX_LINKS`: Number of gallery pages to scan (default: 50)
- `MAX_DOWNLOADS`: Maximum images to download (default: 300)
- `SCROLL_PAUSE`: Delay between page scrolls in seconds (default: 2)

Image processing settings in `process_images.py`:
- Target size: 800x600 pixels
- **Center crop to 4:3 aspect ratio** (no black bars or padding)
- Downsize high-resolution images with high-quality LANCZOS resampling
- JPEG output at 95% quality

## Logging & Summary Report

- All pipeline activity is logged to `pipeline.log` in the project folder
- Errors, successes, and info messages are included
- At the end of each run, a summary report is printed:
  - Number of images downloaded and processed
  - Number of errors
  - Total images in each folder
  - Log file location

## Project Structure

```
./
├── img_downloader_self.py  # Downloads images from ESPNCricinfo
├── process_images.py       # Crops and processes images to 800x600
├── run_pipeline.py         # All-in-one script with logging and summary
├── requirements.txt        # Python dependencies
├── pipeline.log            # Log file (created automatically)
└── data/                   # Created automatically
    ├── raw/                # Original downloaded images
    └── size_processed/     # 800x600 cropped and resized images (no black bars)
```

## Requirements

- Python 3.8 or newer
- Chrome browser
- Dependencies from requirements.txt:
  - selenium
  - requests
  - beautifulsoup4
  - Pillow
  - webdriver-manager
  - tqdm

## Error Recovery
- The pipeline skips already downloaded and processed files
- You can safely interrupt and rerun the pipeline; it will only process new/unprocessed files
- All errors are logged and reported in the summary

## Example Workflow

```powershell
python run_pipeline.py
# Downloads images to ./data/raw
# Processes images to ./data/processed
# Shows progress bars and prints a summary report
```

## Custom Data Folder Example

```powershell
$env:DATA_DIR = "C:\my\custom\data"
python run_pipeline.py
```

## Questions or Issues?
- Check `pipeline.log` for details
- Review the summary report for error counts and folder contents
- For help, open an issue or contact the maintainer

## Script Reference

### Core Scripts

| Script | Purpose | Key Arguments | Output |
|--------|---------|---------------|--------|
| `img_downloader_self.py` | Scrape & download images | Edit constants: `MAX_LINKS`, `MAX_DOWNLOADS` | `data/raw/*.jpg` |
| `process_images.py` | Center-crop & resize to 800×600 | None (reads from `data/raw/`) | `data/size_processed/*.jpg` |
| `run_pipeline.py` | Run download + process with logging | None (orchestrates above two) | Images + `pipeline.log` |
| `extract_features.py` | Extract HOG+HSV+LBP per cell | `--csv`, `--images`, `--out-dir`, `--padding` | `features.npz`, `features.csv` |
| `reduce_features.py` | PCA + train/test split | `--input`, `--variance`, `--test-size` | `features_train_pca.npz`, `features_test_pca.npz` |
| `visualize_tsne.py` | t-SNE 2D visualization | `--input`, `--output`, `--perplexity` | `tsne_*.png` |

### Quick Command Reference

```powershell
# 1. Download images
python img_downloader_self.py

# 2. Process to 800×600
python process_images.py

# 3. Extract features (after manual annotation)
python extract_features.py --csv "data/annotated&csv/cricket_labels.csv" --images "data/raw" --out-dir "data/features" --output-format both --padding 0

# 4. Apply PCA + split train/test
python reduce_features.py --input data/features/features.npz --output-dir data/features --variance 0.95 --test-size 0.3 --random-seed 42

# 5. Visualize with t-SNE
python visualize_tsne.py --input data/features/features_train_pca.npz --output data/features/tsne_pca_all.png --perplexity 30 --n-samples 15000
```

---

## Project Structure

```
PML_Project_self/
├── img_downloader_self.py      # Web scraper for ESPNCricinfo
├── process_images.py            # Image preprocessing (800×600)
├── run_pipeline.py              # Orchestration script with logging
├── extract_features.py          # Feature extraction (HOG+HSV+LBP)
├── reduce_features.py           # PCA + train/test splitting
├── visualize_tsne.py            # t-SNE 2D visualization
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── pipeline.log                 # Auto-generated log file
│
└── data/                        # Data directory (created automatically)
    ├── raw/                     # Downloaded images (original)
    ├── size_processed/          # Processed 800×600 images
    ├── annotated&csv/           # Manual annotations
    │   ├── cricket_labels.csv   # Cell labels (8×8 grid per image)
    │   └── annotated_images/    # Annotated PNG images
    │       └── annotated_*.png
    │
    └── features/                # Feature extraction outputs
        ├── features.npz         # Raw features (19,264 × 326)
        ├── features.csv         # Raw features (CSV format)
        ├── dataset_stats.json   # Class distribution stats
        ├── features_train_pca.npz   # PCA-reduced train set (13,484 × 133)
        ├── features_test_pca.npz    # PCA-reduced test set (5,780 × 133)
        ├── pca_scaler.npz       # StandardScaler parameters
        ├── pca_model.npz        # PCA model parameters
        ├── pca_split_stats.json # Train/test split statistics
        ├── pca_variance_plot.png    # PCA variance explained plot
        ├── tsne_pca_all.png     # t-SNE 2D visualization
        ├── feature_analysis/    # Feature visualization
        │   └── sample_histograms.png
        └── intermediates/       # (Optional) Intermediate images
            ├── grayscale/       # Grayscale cell images
            └── lbp_maps/        # LBP pattern maps
```

---

## Requirements

All dependencies are listed in `requirements.txt`:

```
selenium
requests
beautifulsoup4
Pillow
webdriver-manager
tqdm
numpy
pandas
scikit-learn
scikit-image
matplotlib
opencv-python
```

Install with:
```powershell
python -m pip install -r requirements.txt
```

---

## Troubleshooting

### Common Issues

**1. Selenium/Chrome errors:**
- Ensure Chrome browser is installed and up-to-date
- `webdriver-manager` will auto-download compatible ChromeDriver
- If timeouts occur, increase `SCROLL_PAUSE` in `img_downloader_self.py`

**2. Feature extraction dimension mismatch:**
- Ensure all annotated images are exactly 800×600
- Use `--padding 0` (recommended) to avoid edge cell size variations
- Script validates dimensions and skips mismatched images with warnings

**3. Memory errors during PCA or t-SNE:**
- Reduce `--n-samples` for t-SNE (5000 is a good default)
- Close other applications to free RAM
- For very large datasets, consider running on a machine with more RAM

**4. Class imbalance warnings:**
- Class 0 (~90%) dominates the dataset — this is expected
- Use class weights in classifiers: `class_weight='balanced'`
- Evaluate with F1-score, not accuracy

**5. Import errors (numpy, sklearn, etc.):**
- Activate your virtual environment first
- Reinstall requirements: `python -m pip install -r requirements.txt`

---

## Data Pipeline Best Practices

This project follows ML best practices:

1. **No data leakage:** StandardScaler and PCA are fit on training data only, then applied to test data
2. **Stratified splitting:** Train/test split preserves class distribution
3. **Reproducibility:** Random seeds (default: 42) ensure consistent results
4. **Feature normalization:** HOG uses per-block normalization (L2-Hys), histograms sum to 1
5. **Atomic writes:** Downloads use `.part` files to avoid corruption
6. **Error recovery:** Scripts skip already-processed files (safe to rerun)

---

## Citation & Acknowledgments

- **Data source:** ESPNCricinfo (https://www.espncricinfo.com/)
- **Feature extraction methods:**
  - HOG: Dalal & Triggs (2005)
  - LBP: Ojala et al. (2002)
- **Dimensionality reduction:** PCA (scikit-learn)
- **Visualization:** t-SNE (van der Maaten & Hinton, 2008)

---

## License

This project is for educational purposes. Images are sourced from ESPNCricinfo and subject to their terms of service.

---

## Future Work

- Implement `train_classifier.py` for baseline models (Random Forest, SVM, XGBoost)
- Add cross-validation for hyperparameter tuning
- Implement class balancing techniques (SMOTE, class weights)
- Add confusion matrix and per-class metrics
- Export trained models for deployment
- Add data augmentation for minority classes

---

## Contact

For questions or issues, please open an issue in the repository or contact the maintainer.

**Happy coding! 🏏**