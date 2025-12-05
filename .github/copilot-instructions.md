# copilot instructions — PML_Project_self

Purpose: Short, actionable guidance for an AI coding assistant working in this cricket image classification repository.

## Project Overview

**Goal:** Build a complete cricket object detection/classification pipeline from web scraping to ML model training.

**Current Status:** Data collection, preprocessing, feature extraction, PCA dimensionality reduction, and t-SNE visualization complete. Ready for classifier implementation.

**Tech Stack:** Python, Selenium, scikit-learn, scikit-image, Pillow, NumPy, pandas, matplotlib

---

## Project Structure

### Core Scripts
1. `img_downloader_self.py` — Web scraper (ESPNCricinfo) → `data/raw/`
2. `process_images.py` — Image preprocessing (center-crop + resize to 800×600) → `data/size_processed/`
3. `run_pipeline.py` — Orchestrator for download + process with logging
4. `extract_features.py` — Per-cell feature extraction (HOG+HSV+LBP) → `data/features/features.npz`
5. `reduce_features.py` — PCA + train/test split → `features_train_pca.npz`, `features_test_pca.npz`
6. `visualize_tsne.py` — t-SNE 2D visualization → `tsne_pca_all.png`

### Key Files
- `requirements.txt` — Full runtime dependencies (selenium, scikit-learn, scikit-image, pillow, etc.)
- `README.md` — Complete user guide with step-by-step instructions
- `PROJECT_DOCUMENTATION.md` — Comprehensive technical documentation
- `pipeline.log` — Auto-generated log from `run_pipeline.py`

### Data Layout
```
data/
├── raw/                    # Downloaded images (original)
├── size_processed/         # 800×600 normalized images
├── annotated&csv/          # Manual annotations
│   ├── cricket_labels.csv
│   └── annotated_images/annotated_*.png
└── features/               # Feature outputs
    ├── features.npz        # Raw features (19,264 × 326)
    ├── features_train_pca.npz  # Train set (13,484 × 133)
    ├── features_test_pca.npz   # Test set (5,780 × 133)
    ├── pca_variance_plot.png
    └── tsne_pca_all.png
```

---

## Runtime & Dependencies

**Python:** 3.8+ required

**Core Libraries:**
- `selenium` + `webdriver-manager` — Web scraping with Chrome automation
- `requests`, `beautifulsoup4` — HTTP and HTML parsing
- `Pillow` — Image I/O and manipulation
- `numpy`, `pandas` — Data handling
- `scikit-learn` — PCA, StandardScaler, train_test_split
- `scikit-image` — HOG, LBP feature extraction
- `matplotlib` — Plotting

**Install:**
```pwsh
python -m pip install -r requirements.txt
```

**Chrome Browser:** Required for Selenium (ChromeDriver auto-installed by webdriver-manager)

---

## Key Conventions & Patterns

### Configuration
- **Top-level constants** in scripts (e.g., `MAX_LINKS`, `MAX_DOWNLOADS` in `img_downloader_self.py`)
- **CLI arguments** for flexibility (all scripts use `argparse`)
- **Environment variable** `DATA_DIR` for custom save locations (optional)

### Logging & Output
- `print` statements with prefixes: `[INFO]`, `[ERROR]`, `[SUCCESS]`
- `run_pipeline.py` captures output → `pipeline.log`
- Progress bars via `tqdm` for long operations

### File I/O
- **Atomic writes:** Downloads use `.part` files, then rename
- **Skip existing:** Scripts check if file exists before processing (safe to rerun)
- **NPZ format:** Compressed NumPy arrays for large datasets
- **JSON stats:** Human-readable metadata and statistics

### Data Pipeline Best Practices
- **No data leakage:** StandardScaler and PCA fit on train only, transform both
- **Stratified split:** Preserves class distribution in train/test
- **Reproducibility:** Random seeds (default: 42) for deterministic results
- **Feature normalization:** HOG uses block-norm, histograms sum to 1

---

## Dataset Characteristics

**Images:** 301 annotated cricket images (800×600)
**Samples:** 19,264 cells (301 × 64 per image)
**Grid:** 8×8 cells per image (cell size: 100×75 px)

**Classes:**
- 0 = None/Background: 17,497 (90.8%) ← **severe imbalance**
- 1 = Ball: 139 (0.7%)
- 2 = Bat: 743 (3.9%)
- 3 = Stumps: 885 (4.6%)

**Features:**
- Raw: 326 dimensions (HOG + HSV histogram + LBP)
- PCA-reduced: 133 components (95.06% variance retained)

**Split:**
- Train: 13,484 samples (70%)
- Test: 5,780 samples (30%)

---

## Common Tasks

### Run Full Pipeline (Download → Process)
```pwsh
python run_pipeline.py
```

### Extract Features from Annotated Images
```pwsh
python extract_features.py --csv "data/annotated&csv/cricket_labels.csv" --images "data/annotated&csv/annotated_images" --out-dir "data/features" --output-format both --padding 0
```

### Apply PCA + Train/Test Split
```pwsh
python reduce_features.py --input data/features/features.npz --output-dir data/features --variance 0.95 --test-size 0.3 --random-seed 42
```

### Visualize with t-SNE
```pwsh
python visualize_tsne.py --input data/features/features_train_pca.npz --output data/features/tsne_pca_all.png --perplexity 30 --n-samples 15000
```

---

## What AI Assistants Can Safely Do

### Minor Edits (No Confirmation Needed)
- Fix obvious bugs (typos, syntax errors)
- Add missing dependencies to `requirements.txt`
- Improve error messages or logging
- Add CLI arguments for flexibility
- Optimize performance (e.g., parallel processing)

### Safe Additions
- Add new feature extraction methods (keep existing ones)
- Create visualization scripts (don't modify existing outputs)
- Add data validation checks
- Implement `train_classifier.py` (next logical step)

### Preserve These
- **Existing output files:** Don't change NPZ structure (breaks downstream code)
- **Print prefix patterns:** `[INFO]`, `[ERROR]`, `[SUCCESS]` (used by `run_pipeline.py`)
- **File naming conventions:** `annotated_*.png`, `features_train_pca.npz`, etc.
- **Data pipeline order:** Split → Fit on train → Transform both (no leakage!)

---

## What NOT to Change Without Confirmation

### Critical Parameters
- Image dimensions (800×600) — entire pipeline depends on this
- Grid size (8×8 cells) — matches annotations
- Feature extraction params (HOG `pixels_per_cell`, histogram bins) — changing invalidates existing features
- Class label codes (0/1/2/3) — matches annotations
- Train/test split ratio (70/30) — for consistency

### Feature Extraction Logic
- **DO NOT remove normalization** (HOG block-norm, histogram sum=1) — this is correct and necessary
- **DO NOT standardize before saving features** — StandardScaler is applied later in `reduce_features.py`
- **DO NOT change padding** from 0 without testing — causes dimension mismatches

### PCA Pipeline
- **DO NOT fit on all data** — always split first, then fit on train only
- **DO NOT change random seed** without updating docs — breaks reproducibility

---

## Next Steps (Future Work)

### Immediate: Classifier Training
Implement `train_classifier.py`:
- Load `features_train_pca.npz` and `features_test_pca.npz`
- Train models: Random Forest, SVM, XGBoost
- Use `class_weight='balanced'` (handles imbalance)
- Evaluate with F1-score, confusion matrix (NOT accuracy)
- Save trained models and metrics

### Later: Improvements
- Data augmentation (flip, rotate) before feature extraction
- SMOTE for minority class oversampling
- Transfer learning with pre-trained CNNs
- Hyperparameter tuning with cross-validation
- Error analysis and iterative improvement

---

## Troubleshooting Quick Reference

**Selenium errors:** Update Chrome, check `SCROLL_PAUSE` constant
**Feature dimension mismatch:** Ensure all images are 800×600, use `--padding 0`
**Memory errors (PCA/t-SNE):** Reduce `--n-samples`, close other apps
**Import errors:** Activate venv, reinstall requirements
**Class imbalance warnings:** Expected! Use class weights in classifiers

---

## Documentation Locations

- **User Guide:** `README.md` (step-by-step instructions, commands)
- **Technical Deep-Dive:** `PROJECT_DOCUMENTATION.md` (architecture, decisions, rationale)
- **This File:** `.github/copilot-instructions.md` (quick reference for AI assistants)

---

**Key Principle:** This project follows ML best practices (no data leakage, stratified splits, reproducibility). Preserve these patterns when making changes.
