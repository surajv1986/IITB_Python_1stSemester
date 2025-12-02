# Solution Summary

## Problem Statement
Divide each 800×600 image from `data/processed` into an 8×8 grid (64 cells) and predict for each grid cell:
- **0** = no object
- **1** = ball
- **2** = bat
- **3** = stump

**Constraints:**
- Use only hand-crafted feature engineering (NO CNNs or automatic feature extraction)
- If multiple objects in a cell, detect any ONE of them
- Save trained model as `model_<teamname>.pkl`

## Solution Components

### 1. Feature Extraction (`feature_extractor.py`)
Hand-crafted features extracted from each grid cell:
- **HOG (Histogram of Oriented Gradients)**: Captures shape and texture patterns
- **LBP (Local Binary Patterns)**: Texture descriptors
- **Color Histograms**: RGB channel distributions
- **Texture Features**: Variance, entropy, contrast, energy
- **Edge Features**: Canny edges, Sobel gradients
- **Shape Features**: Hu moments, area ratios

### 2. Grid Processing (`grid_processor.py`)
Divides 800×600 images into 8×8 grid:
- Each cell: 100×75 pixels
- Returns cells and their positions (row, col)

### 3. Training Pipeline (`train_model.py`)
Complete training workflow:
- Loads images and annotations
- Extracts features for all grid cells
- Trains Random Forest or SVM classifier
- Saves model as `model_<teamname>.pkl`
- Includes evaluation metrics

### 4. Prediction Script (`predict.py`)
Uses trained model to predict objects in new images:
- Divides image into grid
- Predicts class for each cell
- Displays results and saves to JSON

## Files Created

```
├── feature_extractor.py    # Hand-crafted feature extraction
├── grid_processor.py       # Grid division (8×8)
├── train_model.py          # Main training script
├── predict.py              # Prediction script
├── requirements.txt        # Dependencies
├── TRAINING_GUIDE.md       # Detailed usage guide
├── example_usage.py        # Example code
└── SOLUTION_SUMMARY.md     # This file
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Create Annotation Template
```bash
python train_model.py --create_template
```

### 3. Edit Annotations
Edit `annotations_template.json` with labels (0-3) for each grid cell.

### 4. Train Model
```bash
python train_model.py --images_dir data/processed \
                      --annotations annotations.json \
                      --team_name TeamIITB \
                      --classifier random_forest
```

Model will be saved as `model_TeamIITB.pkl`

### 5. Make Predictions
```bash
python predict.py --image data/processed/sample.jpg \
                  --model model_TeamIITB.pkl \
                  --output predictions.json
```

## Key Features

✅ **Hand-crafted features only** - No CNNs or automatic feature extraction
✅ **8×8 grid division** - Splits 800×600 images into 64 cells
✅ **Multiple feature types** - HOG, LBP, color, texture, edges, shape
✅ **Flexible classifiers** - Random Forest or SVM
✅ **Complete pipeline** - Training, evaluation, and prediction
✅ **Model serialization** - Saves as `model_<teamname>.pkl`

## Model Architecture

- **Input**: 100×75 pixel grid cell
- **Features**: ~100-400 hand-crafted features per cell
- **Classifier**: Random Forest (default) or SVM
- **Output**: Class label (0, 1, 2, or 3)

## Notes

1. **Team Name**: Default is "TeamIITB" but can be customized with `--team_name` parameter
2. **Multiple Objects**: When multiple objects appear in one cell, label with any ONE object
3. **Annotations**: Required for training - use template generator to create annotation file
4. **Evaluation**: Training script automatically splits data and shows accuracy, classification report, and confusion matrix

## Dependencies

- numpy
- scikit-image (for HOG, LBP)
- opencv-python (for image processing)
- scikit-learn (for classifiers)
- Pillow (for image I/O)
- tqdm (for progress bars)

See `requirements.txt` for exact versions.

