# Cricket Image Classification Project - Complete Documentation

## Executive Summary

This document provides a comprehensive overview of the complete cricket image classification pipeline, from data collection to feature extraction and visualization, ready for machine learning model training.

**Project Goal:** Build a cricket object detection/classification system that identifies balls, bats, and stumps in cricket images using computer vision and machine learning.

**Current Status:** ✅ Data collection, preprocessing, feature extraction, dimensionality reduction, and visualization complete. Ready for classifier training.

---

## Pipeline Architecture

### Complete Workflow (7 Phases)

1. **Image Collection** → ESPNCricinfo web scraping → Raw images
2. **Image Processing** → Center-crop & resize → 800×600 normalized images
3. **Manual Annotation** → 8×8 grid labeling → Annotated datasets with labels
4. **Feature Extraction** → HOG+HSV+LBP → 326-dimensional feature vectors per cell
5. **Dimensionality Reduction** → PCA (95% variance) → 133 components
6. **Train/Test Split** → Stratified 70/30 split → Separate train/test datasets
7. **Visualization** → t-SNE 2D projection → Class separability analysis

---

## Phase-by-Phase Details

### Phase 1: Image Collection (`img_downloader_self.py`)

**Purpose:** Scrape cricket images from ESPNCricinfo galleries

**Technology Stack:**
- Selenium WebDriver (Chrome automation)
- BeautifulSoup (HTML parsing)
- Requests (HTTP downloads)
- ThreadPoolExecutor (concurrent downloads)

**Process:**
1. Launch Chrome with Selenium
2. Navigate to ESPNCricinfo gallery index
3. Scroll page to load dynamic content (AJAX)
4. Collect `/gallery/` links (up to MAX_LINKS)
5. Parse each gallery page for high-resolution image URLs
6. Filter by minimum size (800×600)
7. Download concurrently with atomic writes (`.part` files)
8. Save to `data/raw/`

**Configuration:**
- `MAX_LINKS = 50` (galleries to scan)
- `MAX_DOWNLOADS = 900` (images to download)
- `SCROLL_PAUSE = 2` (seconds between scrolls)
- `DATA_DIR` environment variable for custom paths

**Output:**
- ~900 high-resolution JPG images in `data/raw/`

**Key Features:**
- Atomic writes prevent corruption
- Skip already-downloaded files
- WebDriver manager auto-installs ChromeDriver
- Timeout handling for unreliable network

---

### Phase 2: Image Processing (`process_images.py`)

**Purpose:** Normalize all images to 800×600 with proper aspect ratio

**Technology Stack:**
- Pillow (PIL) for image I/O and manipulation
- LANCZOS resampling (high-quality resize)
- ThreadPoolExecutor (concurrent processing)

**Process:**
1. Load image from `data/raw/`
2. Convert to RGB (handle RGBA, grayscale, etc.)
3. Calculate 4:3 aspect ratio crop:
   - If too wide: center-crop horizontally
   - If too tall: center-crop vertically
4. Resize cropped region to exactly 800×600 using LANCZOS
5. Save as JPEG (quality=95) to `data/size_processed/`

**Why Center Crop?**
- No black bars or padding
- Preserves central content (where action typically occurs)
- Consistent dimensions for feature extraction

**Output:**
- ~900 processed 800×600 JPG images in `data/size_processed/`

---

### Phase 3: Manual Annotation (External)

**Purpose:** Label objects in images for supervised learning

**Annotation Scheme:**
- Each 800×600 image divided into **8×8 grid** (64 cells)
- Cell size: 100×75 pixels
- Single-label classification per cell:
  - `0` = No object / background
  - `1` = Ball
  - `2` = Bat
  - `3` = Stumps

**CSV Format:**
```csv
ImageFileName,TrainOrTest,Cell_0_0,Cell_0_1,...,Cell_7_7
192.jpg,train,0,0,1,0,0,2,...,0
```

**File Naming:**
- CSV entry `192.jpg` → Annotated file `annotated_192.png`
- Store in `data/annotated&csv/annotated_images/`

**Dataset Statistics (301 images):**
- Total cells: 19,264 (301 × 64)
- Class distribution:
  - Class 0 (None): 17,497 (90.8%) ← **severe imbalance**
  - Class 1 (Ball): 139 (0.7%)
  - Class 2 (Bat): 743 (3.9%)
  - Class 3 (Stumps): 885 (4.6%)

**Challenge:** Extreme class imbalance requires special handling (class weights, resampling, etc.)

---

### Phase 4: Feature Extraction (`extract_features.py`)

**Purpose:** Extract per-cell computer vision features for ML

**Technology Stack:**
- scikit-image (HOG, LBP)
- Pillow (HSV conversion)
- NumPy (array operations)

**Feature Types:**

#### 1. HOG (Histogram of Oriented Gradients)
- **Purpose:** Capture shape and edge information
- **Method:** Gradient orientation histograms in local regions
- **Parameters:**
  - Convert cell to grayscale
  - `orientations = 9` (9 angle bins)
  - `pixels_per_cell = (20, 20)` (grid resolution)
  - `cells_per_block = (2, 2)` (normalization blocks)
  - `block_norm = 'L2-Hys'` (robust L2 normalization)
- **Output:** ~288 features per cell
- **Why:** Excellent for object shape recognition, robust to illumination

#### 2. HSV Color Histogram
- **Purpose:** Capture color distribution
- **Method:** Histogram of Hue, Saturation, Value channels
- **Parameters:**
  - Convert to HSV color space
  - H: 16 bins, S: 8 bins, V: 4 bins
  - Normalize to sum=1 (probability distribution)
- **Output:** 28 features per cell (16+8+4)
- **Why:** HSV is more perceptually uniform than RGB

#### 3. LBP (Local Binary Pattern)
- **Purpose:** Capture texture information
- **Method:** Binary patterns of local pixel neighborhoods
- **Parameters:**
  - `P = 8` (8 neighbors)
  - `R = 1` (radius 1 pixel)
  - `method = 'uniform'` (rotation-invariant patterns)
  - Normalize histogram to sum=1
- **Output:** 10 features per cell (uniform LBP → 8+2 bins)
- **Why:** Fast, rotation-invariant texture descriptor

**Total Features per Cell:** ~326 (288 HOG + 28 HSV + 10 LBP)

**Process:**
1. Map CSV filename to annotated image (`192.jpg` → `annotated_192.png`)
2. Validate image is 800×600 (skip if not)
3. Divide into 8×8 grid (cell_h=75, cell_w=100)
4. For each of 64 cells:
   - Crop cell region (with optional padding)
   - Resize to standard size to ensure consistent feature dimensions
   - Extract HOG on grayscale
   - Extract HSV histogram
   - Extract LBP histogram
   - Concatenate into single feature vector (326-dim)
5. Store features in matrix X (19,264 × 326)
6. Store labels in vector y (19,264)
7. Save as NPZ (compressed) and/or CSV

**Why These Features?**
- **Complementary:** HOG = shape, HSV = color, LBP = texture
- **Proven:** State-of-the-art before deep learning era
- **Interpretable:** Can analyze which features matter
- **Fast:** Real-time extraction possible

**Output Files:**
- `data/features/features.npz` — Compressed NumPy arrays (X, y, filenames, cell_idx)
- `data/features/features.csv` — Human-readable CSV
- `data/features/dataset_stats.json` — Class distribution
- `data/features/feature_analysis/sample_histograms.png` — Sample visualizations

---

### Phase 5: Dimensionality Reduction & Splitting (`reduce_features.py`)

**Purpose:** Reduce feature dimensions and prepare ML-ready train/test datasets

**Why Reduce Dimensions?**
- 326 features is manageable but still high-dimensional
- PCA removes redundancy and noise
- Faster training, less overfitting
- Visualization becomes possible

**Technology Stack:**
- scikit-learn (StandardScaler, PCA, train_test_split)
- Matplotlib (variance plots)

**Process:**

#### Step 1: Load Features
- Read `features.npz` (19,264 × 326)

#### Step 2: Train/Test Split (70/30)
- **Stratified split** to preserve class distribution
- Random seed = 42 (reproducibility)
- Train: 13,484 samples (70%)
- Test: 5,780 samples (30%)
- **Why split first?** Prevents data leakage in StandardScaler and PCA

#### Step 3: Standardization (fit on train only)
- Apply StandardScaler: `(X - mean) / std`
- **Fit** scaler on training data → computes mean and std
- **Transform** both train and test with fitted parameters
- **Result:** All features have mean≈0, std≈1
- **Why?** PCA requires features on same scale

#### Step 4: PCA (fit on train only)
- Apply PCA with `n_components=0.95` (retain 95% variance)
- **Fit** PCA on standardized training data → computes principal components
- **Transform** both train and test with fitted PCA
- **Result:** 326 → 133 dimensions (59% reduction)
- **Variance retained:** 95.06%

**Key Results:**
- Original: 326 features
- Reduced: 133 principal components
- Variance explained: 95.06%
- First 10 PCs explain: ~45%
- 133 PCs explain 99%+ variance

**Why This Order Matters:**
```
❌ WRONG (data leakage):
All data → Fit PCA → Split train/test → Train classifier
(PCA sees test data → overly optimistic results)

✅ CORRECT (no leakage):
All data → Split train/test → Fit PCA on train → Transform train & test → Train classifier
(PCA never sees test data → realistic results)
```

**Output Files:**
- `features_train_pca.npz` — Training set (13,484 × 133)
- `features_test_pca.npz` — Test set (5,780 × 133)
- `pca_scaler.npz` — StandardScaler parameters (for future data)
- `pca_model.npz` — PCA transformation matrix (for future data)
- `pca_variance_plot.png` — Individual & cumulative variance plots
- `pca_split_stats.json` — Full statistics

---

### Phase 6: Visualization (`visualize_tsne.py`)

**Purpose:** Visualize high-dimensional feature space in 2D

**Technology Stack:**
- scikit-learn t-SNE (t-Distributed Stochastic Neighbor Embedding)
- Matplotlib (scatter plots)

**What is t-SNE?**
- Non-linear dimensionality reduction
- Preserves local structure (nearby points stay nearby)
- Maps high-dimensional data (133 PCs) → 2D for plotting
- **Not** for feature engineering (non-deterministic, no inverse transform)

**Process:**
1. Load PCA-reduced features (13,484 × 133)
2. Subsample if needed (t-SNE is O(n²), slow on large datasets)
3. Apply t-SNE: 133D → 2D
4. Create scatter plot:
   - Color by class (0=gray, 1=red, 2=blue, 3=green)
   - Different markers per class
   - Class 0 plotted with smaller, transparent points (due to imbalance)

**Parameters:**
- `perplexity = 30` (balance between local and global structure)
- `n_samples = 5000-15000` (computational limit)
- `random_seed = 42`

**Interpretation:**
- **Tight, separated clusters** → classes are well-separated → good for classification
- **Overlapping regions** → classes are ambiguous → challenging classification
- **Class 0 dominates plot** → expected due to 90% imbalance

**Output:**
- `tsne_pca_all.png` — 2D scatter plot

**Runtime:** 5-15 minutes for 13,484 samples

---

## Technical Decisions & Rationale

### 1. Why Center Crop Instead of Padding?
- **Padding** → black bars → wasted space, confuses features
- **Center crop** → removes edges, keeps central content → better features

### 2. Why 800×600 Resolution?
- Large enough to capture details (ball is small!)
- Small enough for fast processing
- 4:3 aspect ratio is natural for photos

### 3. Why HOG + HSV + LBP?
- **Complementary features:** shape, color, texture
- **Proven track record:** State-of-the-art pre-deep-learning
- **Fast:** Real-time extraction possible
- **Interpretable:** Can analyze feature importance

### 4. Why PCA at 95% Variance?
- **Balance:** Reduces dimensions while retaining information
- **95% is standard:** Common threshold in literature
- **Results:** 326 → 133 dimensions (59% reduction)

### 5. Why Train/Test Split Before PCA?
- **Prevents data leakage:** PCA should never see test data
- **Realistic evaluation:** Mimics real-world deployment
- **Best practice:** Industry standard

### 6. Why Stratified Split?
- **Preserves class balance:** 90/0.7/3.9/4.6% → same in train and test
- **Prevents bias:** Ensures all classes represented in both sets

### 7. Why t-SNE After PCA?
- **Speed:** t-SNE on 326 features is very slow
- **Quality:** PCA removes noise, t-SNE works better
- **Standard practice:** PCA → t-SNE is common pipeline

---

## Dataset Characteristics

### Images
- **Count:** 301 annotated images
- **Resolution:** 800×600 pixels (normalized)
- **Source:** ESPNCricinfo cricket galleries
- **Format:** JPEG (quality=95)

### Samples (Cells)
- **Count:** 19,264 (301 images × 64 cells)
- **Cell size:** 100×75 pixels
- **Grid:** 8×8 per image

### Class Distribution (Severe Imbalance!)
| Class | Label | Count | Percentage |
|-------|-------|-------|------------|
| 0 | None/Background | 17,497 | 90.8% |
| 1 | Ball | 139 | 0.7% |
| 2 | Bat | 743 | 3.9% |
| 3 | Stumps | 885 | 4.6% |

**Challenge:** Extreme imbalance requires:
- Class weights in classifier: `class_weight='balanced'`
- Resampling techniques (SMOTE, undersampling)
- Evaluation metrics: F1-score, precision/recall (NOT accuracy)

### Feature Dimensions
- **Raw features:** 326 per cell (HOG + HSV + LBP)
- **PCA features:** 133 components (95.06% variance)
- **Train set:** 13,484 samples (70%)
- **Test set:** 5,780 samples (30%)

---

## Next Steps: Classification

### Recommended Models

1. **Random Forest**
   - Handles class imbalance with `class_weight='balanced'`
   - No scaling required (tree-based)
   - Feature importance analysis
   - Fast training

2. **SVM (Support Vector Machine)**
   - RBF kernel for non-linear boundaries
   - Use `class_weight='balanced'`
   - Already scaled (from StandardScaler)
   - Good for high-dimensional data

3. **Gradient Boosting (XGBoost/LightGBM)**
   - State-of-the-art for tabular data
   - Handles imbalance with `scale_pos_weight`
   - Feature importance
   - May overfit on small dataset

4. **Neural Network**
   - Multi-layer perceptron
   - Weighted loss function for imbalance
   - Dropout for regularization
   - Requires more tuning

### Evaluation Metrics

**DO NOT USE ACCURACY!** (misleading with 90% imbalance)

**Use instead:**
- **F1-score** (macro-averaged): Harmonic mean of precision/recall
- **Per-class precision, recall, F1**
- **Confusion matrix:** Shows per-class performance
- **ROC-AUC** (one-vs-rest): Area under ROC curve

### Hyperparameter Tuning
- Grid search or random search with cross-validation
- Stratified K-Fold (e.g., 5-fold) to preserve class distribution
- Optimize for F1-score (macro), not accuracy

### Expected Challenges
- **Class 1 (Ball):** Only 139 samples (0.7%) → very hard to learn
- **Class 0 dominance:** Model may predict "none" for everything
- **Small dataset:** Only 13,484 train samples → risk of overfitting

### Improvement Strategies
1. **Data augmentation:** Flip, rotate, color jitter (before feature extraction)
2. **SMOTE:** Synthetic minority oversampling
3. **Ensemble methods:** Combine multiple classifiers
4. **Transfer learning:** Use pre-trained CNN features instead of HOG/HSV/LBP
5. **Deep learning:** Train CNN end-to-end (requires more data or augmentation)

---

## File Organization Best Practices

### Naming Conventions
- **Raw downloads:** `{number}.jpg` (e.g., `IMG_1234.jpg`)
- **Processed:** Same filename, different folder
- **Annotated:** `annotated_{number}.png` (e.g., `annotated_192.png`)
- **Features:** `features.npz`, `features_train_pca.npz`
- **Stats:** `*_stats.json` for all statistics
- **Plots:** Descriptive names (`pca_variance_plot.png`, `tsne_pca_all.png`)

### Data Provenance
- Each NPZ file contains metadata: `filenames`, `cell_idx`
- Can trace any sample back to original image and cell location
- Important for error analysis and debugging

---

## Performance & Scalability

### Runtime (Approximate)
- **Download:** 10-30 min (depends on network)
- **Processing:** 2-5 min (depends on CPU cores)
- **Feature extraction:** 5-10 min (301 images)
- **PCA:** <1 min (fast with scikit-learn)
- **t-SNE:** 5-15 min (depends on n_samples)

### Memory Usage
- **Feature extraction:** ~500MB RAM
- **PCA:** ~1GB RAM
- **t-SNE:** ~2-4GB RAM (for 15,000 samples)

### Disk Space
- **Raw images:** ~500MB (900 images)
- **Processed:** ~300MB (compressed JPEG)
- **Features (NPZ):** ~60MB (compressed)
- **PCA output:** ~5MB (much smaller)
- **Total:** ~1-2GB

### Scalability
- **Current:** 301 images → 19K samples (manageable)
- **Can scale to:** 1000+ images → 64K+ samples with same pipeline
- **Bottlenecks:** t-SNE (O(n²)), annotation (manual labor)

---

## Reproducibility

### Fixed Seeds
- `random_seed = 42` used throughout
- Train/test split reproducible
- PCA reproducible
- t-SNE reproducible (with seed)

### Environment
- Python 3.8+
- All dependencies in `requirements.txt` with versions
- Virtual environment recommended

### Version Control
- All code in Git repository
- Data files NOT in Git (too large)
- Generated outputs NOT in Git (reproducible)

---

## Summary

**What We Built:**
A complete end-to-end pipeline from raw web data to ML-ready train/test datasets with visualization.

**Key Achievements:**
✅ Automated data collection (900 images)
✅ Robust preprocessing (800×600 normalization)
✅ Manual annotation (301 images, 19K cells)
✅ Feature extraction (HOG+HSV+LBP, 326 features)
✅ Proper train/test split (70/30 stratified)
✅ Dimensionality reduction (PCA to 133 dims)
✅ Visualization (t-SNE 2D plots)
✅ Zero data leakage (best practices followed)

**Ready For:**
🎯 Classifier training (Random Forest, SVM, XGBoost, Neural Net)
🎯 Hyperparameter tuning with cross-validation
🎯 Performance evaluation with proper metrics
🎯 Error analysis and iterative improvement

**Challenges:**
⚠️ Severe class imbalance (90% vs 0.7%)
⚠️ Small dataset for minority classes (Ball: 139 samples)
⚠️ Manual annotation is labor-intensive

**Next Steps:**
1. Implement `train_classifier.py`
2. Train baseline models with class weights
3. Evaluate with F1-score and confusion matrix
4. Analyze errors and iterate
5. Consider data augmentation or transfer learning

---

**Document Version:** 1.0  
**Last Updated:** December 5, 2025  
**Status:** Production-ready for ML training
