# Automated Annotation - Quick Start Guide

## 🚀 Quick Start

### Method 1: Rule-Based Auto-Annotation (Fastest)
```bash
python auto_annotate.py --images_dir data/processed --output auto_annotations.json
```

### Method 2: Clustering-Based (Better Quality)
```bash
python auto_annotate_clustering.py --images_dir data/processed --output cluster_annotations.json
```

### Visualize Results
```bash
python visualize_annotations.py --annotations auto_annotations.json --images_dir data/processed --output_dir visualizations
```

### Use for Training
```bash
python train_model.py --images_dir data/processed --annotations auto_annotations.json --team_name TeamIITB
```

## 📋 Complete Workflow

```bash
# Step 1: Auto-annotate (choose one method)
python auto_annotate.py --images_dir data/processed --output annotations.json

# OR use clustering
python auto_annotate_clustering.py --images_dir data/processed --output annotations.json

# Step 2: Review visualizations
python visualize_annotations.py --annotations annotations.json \
                                --images_dir data/processed \
                                --output_dir visualizations \
                                --max_images 10

# Step 3: Edit annotations.json if needed (manual corrections)

# Step 4: Train model
python train_model.py --images_dir data/processed \
                      --annotations annotations.json \
                      --team_name TeamIITB

# Step 5: Model saved as model_TeamIITB.pkl
```

## 🔍 What Each Method Does

### Rule-Based Detection (`auto_annotate.py`)
- Uses traditional CV techniques:
  - **Hough Circle Transform** → detects balls
  - **Hough Line Transform** → detects stumps  
  - **Shape analysis** → detects bats
  - **Edge density** → detects empty cells

### Clustering-Based (`auto_annotate_clustering.py`)
- Groups similar cells together
- Analyzes patterns across images
- Better for finding systematic patterns

## ✅ Advantages

- ✅ **No CNNs** - Uses only traditional CV (complies with constraints)
- ✅ **Fast** - Processes hundreds of images in minutes
- ✅ **Automated** - No manual clicking required
- ✅ **Reproducible** - Same inputs = same outputs

## 📝 Next Steps

1. Run auto-annotation
2. Visualize and review results
3. Manually correct any errors in JSON file
4. Train your model
5. Evaluate and iterate!

For detailed information, see `AUTO_ANNOTATION_GUIDE.md`

