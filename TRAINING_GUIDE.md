# Grid Cell Object Classification - Training Guide

## Overview
This program divides 800×600 images into an 8×8 grid (64 cells) and trains a classifier to detect objects in each cell:
- **0** = no object
- **1** = ball
- **2** = bat
- **3** = stump

The solution uses **hand-crafted features** only (NO CNNs or automatic feature extraction):
- Histogram of Oriented Gradients (HOG)
- Local Binary Patterns (LBP)
- Color Histograms
- Texture Features (variance, entropy, contrast, energy)
- Edge Features (Canny, Sobel)
- Shape Features (Hu moments, area ratio)

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Create Annotation Template (Optional)

If you don't have annotations yet, create a template file:

```bash
python train_model.py --create_template
```

This creates `annotations_template.json` with empty labels for the first 5 images. You can manually edit this file to add labels.

### Step 2: Prepare Annotations

Create a JSON file with annotations in the following format:

```json
{
  "image_filename.jpg": {
    "cells": [
      {"row": 0, "col": 0, "label": 1},
      {"row": 0, "col": 1, "label": 0},
      {"row": 0, "col": 2, "label": 2},
      ...
    ]
  },
  ...
}
```

**Label values:**
- `0` = no object
- `1` = ball
- `2` = bat
- `3` = stump

**Important:** Each image should have 64 cell annotations (8 rows × 8 columns). If multiple objects are present in a cell, label it with any ONE of them.

### Step 3: Train the Model

Train with annotations:

```bash
python train_model.py --images_dir data/processed --annotations annotations.json --team_name TeamIITB --classifier random_forest
```

**Arguments:**
- `--images_dir`: Directory containing training images (default: `data/processed`)
- `--annotations`: Path to annotations JSON file (optional)
- `--team_name`: Team name for model filename (default: `TeamIITB`)
- `--classifier`: Classifier type - `random_forest` or `svm` (default: `random_forest`)

The trained model will be saved as `model_<team_name>.pkl`.

## Example Workflow

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create annotation template (if needed)
python train_model.py --create_template

# 3. Edit annotations_template.json to add your labels
# Save as annotations.json

# 4. Train the model
python train_model.py --images_dir data/processed --annotations annotations.json --team_name TeamIITB

# 5. Model saved as model_TeamIITB.pkl
```

## Model Architecture

### Feature Extraction
Each grid cell (100×75 pixels) is processed to extract:
- **HOG features**: ~36-324 features (depending on cell size)
- **LBP features**: 10 features
- **Color histogram**: 48 features (16 bins × 3 channels)
- **Texture features**: 6 features
- **Edge features**: 3 features
- **Shape features**: 3 features

Total feature vector: ~100-400 features per cell

### Classifiers
- **Random Forest**: Default, robust, fast training
- **SVM**: Alternative, can be more accurate with good hyperparameters

Both use class balancing to handle imbalanced datasets.

## Files Structure

```
.
├── feature_extractor.py    # Hand-crafted feature extraction
├── grid_processor.py       # Grid division logic
├── train_model.py          # Main training script
├── requirements.txt        # Python dependencies
├── TRAINING_GUIDE.md       # This file
└── data/
    └── processed/          # Training images (800×600)
```

## Notes

1. **No CNNs**: This solution uses only hand-crafted features as required.
2. **Grid Division**: Each 800×600 image is divided into 8×8 grid = 64 cells (100×75 pixels each)
3. **Multiple Objects**: If multiple objects appear in one cell, label with any ONE object
4. **Model File**: Saved as `model_<teamname>.pkl` containing classifier, scaler, and metadata

## Troubleshooting

- **No annotations found**: Run with `--create_template` first, then edit and provide annotations
- **Import errors**: Install dependencies with `pip install -r requirements.txt`
- **Memory issues**: Reduce number of images or use SVM instead of Random Forest

