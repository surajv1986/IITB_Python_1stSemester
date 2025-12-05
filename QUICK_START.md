# Quick Start Guide - Cricket Image Classification Project

## What We've Built

A complete pipeline from web scraping to ML-ready datasets:
1. ✅ Downloaded 900 cricket images from ESPNCricinfo
2. ✅ Processed to 800×600 normalized format
3. ✅ Manually annotated 301 images (8×8 grid, 19,264 cells total)
4. ✅ Extracted 326 features per cell (HOG + HSV + LBP)
5. ✅ Applied PCA → reduced to 133 dimensions
6. ✅ Split 70/30 train/test (stratified)
7. ✅ Visualized with t-SNE

**Current Status:** Ready for classifier training! 🎯

---

## Quick Reference: Run Commands

```powershell
# 1. Download images
python img_downloader_self.py

# 2. Process to 800×600
python process_images.py

# 3. Extract features (after annotation)
# Uses clean images from data/raw, NOT annotated images
python extract_features.py `
  --csv "data/annotated&csv/cricket_labels.csv" `
  --images "data/raw" `
  --out-dir "data/features" `
  --output-format both `
  --padding 0

# 4. PCA + train/test split
python reduce_features.py `
  --input data/features/features.npz `
  --output-dir data/features `
  --variance 0.95 `
  --test-size 0.3

# 5. t-SNE visualization
python visualize_tsne.py `
  --input data/features/features_train_pca.npz `
  --output data/features/tsne_pca_all.png `
  --perplexity 30 `
  --n-samples 15000
```

---

## Key Files You Need

### For Classifier Training
- `data/features/features_train_pca.npz` → Training set (13,484 × 133)
- `data/features/features_test_pca.npz` → Test set (5,780 × 133)

### Documentation
- `README.md` → Complete step-by-step guide
- `PROJECT_DOCUMENTATION.md` → Technical deep-dive
- `.github/copilot-instructions.md` → AI assistant quick reference

### Stats & Plots
- `data/features/pca_split_stats.json` → All statistics
- `data/features/pca_variance_plot.png` → PCA variance explained
- `data/features/tsne_pca_all.png` → 2D class visualization

---

## Important Numbers

**Dataset:**
- 19,264 total samples (cells)
- 13,484 training samples (70%)
- 5,780 test samples (30%)

**Features:**
- 326 raw dimensions → 133 PCA components
- 95.06% variance retained

**Classes (Severe Imbalance!):**
- Class 0 (None): 90.8%
- Class 1 (Ball): 0.7% ← very rare!
- Class 2 (Bat): 3.9%
- Class 3 (Stumps): 4.6%

---

## Next Step: Train Classifier

### Recommended First Model: Random Forest

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# Load data
train = np.load('data/features/features_train_pca.npz')
test = np.load('data/features/features_test_pca.npz')

X_train, y_train = train['X'], train['y']
X_test, y_test = test['X'], test['y']

# Train with class weights (handles imbalance)
clf = RandomForestClassifier(
    n_estimators=200,
    class_weight='balanced',  # CRITICAL for imbalance
    random_state=42,
    n_jobs=-1
)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))
```

**Key:** Use `class_weight='balanced'` and evaluate with F1-score, NOT accuracy!

---

## Critical Reminders

### ⚠️ Class Imbalance
- **DO:** Use `class_weight='balanced'`
- **DO:** Evaluate with F1-score, precision, recall
- **DON'T:** Use accuracy (misleading with 90% imbalance)

### ⚠️ Data Leakage
- **DO:** Always fit transformers on train only
- **DO:** Transform both train and test with fitted transformer
- **DON'T:** Fit on all data before splitting

### ⚠️ Features
- **DO:** Use PCA-reduced features (`*_pca.npz`) for training
- **DON'T:** Re-standardize (already done in `reduce_features.py`)

---

## File Locations

```
PML_Project_self/
├── data/features/
│   ├── features_train_pca.npz    ← Train here
│   ├── features_test_pca.npz     ← Test here
│   ├── pca_split_stats.json      ← Read stats
│   ├── pca_variance_plot.png     ← View variance
│   └── tsne_pca_all.png          ← View separability
│
├── README.md                     ← User guide
├── PROJECT_DOCUMENTATION.md      ← Technical docs
└── .github/copilot-instructions.md  ← AI reference
```

---

## Common Issues & Solutions

**Q: Why only 133 features instead of 326?**
A: PCA reduced dimensions while keeping 95% of information. Faster training, less overfitting.

**Q: Why such class imbalance?**
A: Most cricket image cells are background (grass, crowd). This is the real data distribution.

**Q: Can I use raw 326 features?**
A: Yes, load `features.npz` and split yourself, but PCA is recommended.

**Q: Why is test accuracy so high but F1 so low?**
A: Because of imbalance! Model predicts "none" for everything → 90% accuracy but useless.

**Q: How to improve Ball class (only 139 samples)?**
A: Data augmentation, SMOTE oversampling, or collect more data.

---

## Performance Expectations

**Baseline (Random Forest with class weights):**
- Overall F1: ~0.50-0.70 (macro-averaged)
- Class 0 (None): F1 ~0.90+ (easy, lots of data)
- Class 1 (Ball): F1 ~0.10-0.30 (hard, very few samples)
- Class 2-3 (Bat/Stumps): F1 ~0.40-0.60 (medium difficulty)

**Good Result:**
- Macro F1 > 0.60
- Ball recall > 0.20 (finding 20% of balls is decent given rarity)
- Stumps/Bat F1 > 0.50

---

## What's Next

1. **Implement** `train_classifier.py` (Random Forest baseline)
2. **Evaluate** with proper metrics (F1, confusion matrix)
3. **Analyze** errors (which cells are misclassified?)
4. **Improve** with:
   - Hyperparameter tuning
   - SMOTE for minority classes
   - Ensemble methods
   - Transfer learning (CNN features)

---

## Help & Resources

**Documentation:**
- Full guide: `README.md`
- Technical details: `PROJECT_DOCUMENTATION.md`
- AI assistant notes: `.github/copilot-instructions.md`

**Stats:**
- Class distribution: `data/features/pca_split_stats.json`
- Feature details: `data/features/dataset_stats.json`

**Visualizations:**
- PCA variance: `data/features/pca_variance_plot.png`
- t-SNE clusters: `data/features/tsne_pca_all.png`

---

**Good luck with classifier training! 🏏🤖**

*Last updated: December 5, 2025*
