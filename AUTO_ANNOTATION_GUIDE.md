# Automated Annotation Guide

## Overview
This guide explains how to automate the annotation process using traditional computer vision techniques (NO CNNs).

## Available Methods

### 1. Rule-Based Detection (`auto_annotate.py`)
Uses traditional CV techniques to detect objects based on shape, color, and geometric properties.

**Features:**
- **Ball Detection**: Hough Circle Transform to detect circular objects
- **Stump Detection**: Hough Line Transform to detect vertical lines
- **Bat Detection**: Shape analysis (aspect ratio, elongation)
- **Empty Cell Detection**: Edge density analysis

**Usage:**
```bash
# Annotate all images
python auto_annotate.py --images_dir data/processed --output auto_annotations.json

# Process only first 10 images (for testing)
python auto_annotate.py --images_dir data/processed --output auto_annotations.json --sample_size 10
```

### 2. Clustering-Based Annotation (`auto_annotate_clustering.py`)
Groups similar cells together using unsupervised learning, then assigns labels.

**Features:**
- Extracts hand-crafted features from all cells
- Clusters similar cells (K-means or DBSCAN)
- Auto-labels clusters by analyzing samples
- Useful for finding patterns in the data

**Usage:**
```bash
# Use K-means clustering
python auto_annotate_clustering.py --images_dir data/processed \
                                   --output cluster_annotations.json \
                                   --n_clusters 8 \
                                   --method kmeans

# Use DBSCAN clustering
python auto_annotate_clustering.py --images_dir data/processed \
                                   --output cluster_annotations.json \
                                   --method dbscan
```

## Detection Techniques Used

### Ball Detection
1. **Hough Circle Transform**: Detects circular shapes
2. **Circularity Analysis**: Measures how circular a shape is (4π×area/perimeter²)
3. **Area Ratio**: Checks if object occupies significant portion of cell

### Bat Detection
1. **Aspect Ratio Analysis**: Bats are elongated (rectangular)
2. **Orientation Analysis**: Horizontal/diagonal orientation
3. **Shape Features**: Width-to-height ratio

### Stump Detection
1. **Vertical Line Detection**: Hough Line Transform for vertical lines
2. **Aspect Ratio**: Very tall, narrow objects
3. **Verticality Score**: Measures how vertical an object is

### Empty Cell Detection
1. **Edge Density**: Very few edges = empty
2. **Area Ratio**: Very small occupied area = empty

## Recommended Workflow

### Option 1: Fully Automated (Quick Start)
```bash
# 1. Run rule-based auto-annotation
python auto_annotate.py --images_dir data/processed --output annotations.json

# 2. Review and manually correct if needed
# Edit annotations.json

# 3. Train model
python train_model.py --images_dir data/processed --annotations annotations.json
```

### Option 2: Semi-Automated with Clustering (Better Quality)
```bash
# 1. Use clustering to find patterns
python auto_annotate_clustering.py --images_dir data/processed \
                                   --output cluster_annotations.json \
                                   --max_images 50

# 2. Review cluster assignments and labels
# Edit cluster_annotations.json to correct cluster labels

# 3. Train model
python train_model.py --images_dir data/processed --annotations cluster_annotations.json
```

### Option 3: Hybrid Approach (Best Quality)
```bash
# 1. Start with rule-based auto-annotation
python auto_annotate.py --images_dir data/processed --output auto_annotations.json

# 2. Use clustering to refine and find missed patterns
python auto_annotate_clustering.py --images_dir data/processed \
                                   --output cluster_refined.json

# 3. Merge annotations (keep manual edits)
# Write a small script to merge both annotation files

# 4. Train model
python train_model.py --images_dir data/processed --annotations merged_annotations.json
```

## Accuracy Tips

1. **Start Small**: Test on a few images first (`--sample_size 10`)
2. **Review Results**: Check auto-annotations before training
3. **Manual Corrections**: Edit JSON files to correct obvious errors
4. **Iterative Refinement**: Use clustering to find and fix systematic errors

## Advantages of Automated Annotation

✅ **Faster**: Annotate hundreds of images in minutes  
✅ **Consistent**: Same rules applied to all cells  
✅ **Scalable**: Easy to process large datasets  
✅ **No Deep Learning**: Uses only traditional CV (complies with constraints)  
✅ **Reproducible**: Same inputs produce same outputs  

## Limitations

⚠️ **May Not Be Perfect**: Rule-based detection has limitations  
⚠️ **Needs Tuning**: Parameters may need adjustment for your data  
⚠️ **Review Recommended**: Manual review and correction improves quality  

## Annotation File Format

All methods produce JSON files in this format:
```json
{
  "image_filename.jpg": {
    "cells": [
      {
        "row": 0,
        "col": 0,
        "label": 1,
        "method": "auto_cv"
      },
      ...
    ]
  }
}
```

**Labels:**
- `0` = no object
- `1` = ball
- `2` = bat
- `3` = stump

## Next Steps

After auto-annotation:
1. Review the generated JSON file
2. Manually correct any obvious errors
3. Use for training: `python train_model.py --annotations your_annotations.json`
4. Evaluate model performance
5. Iterate: correct annotations and retrain if needed

