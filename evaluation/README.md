# SWDE Evaluation System

This directory contains the evaluation system for testing web2json-agent against the SWDE (Structured Web Data Extraction) dataset.

## Overview

The SWDE evaluation system:
1. Runs the web2json agent on SWDE dataset websites
2. Compares extracted JSON against groundtruth
3. Computes precision, recall, and F1 scores
4. Generates detailed reports with visualizations

## Installation

Install required dependencies:

```bash
pip install matplotlib tqdm
```

## Quick Start

### Test on a single website

```bash
python evaluation/test_evaluation.py
```

This will run a test on the `book/abebooks` website and generate reports.

### Evaluate a single website

```bash
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --vertical book \
  --website abebooks
```

### Evaluate all websites in a vertical

```bash
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output \
  --vertical book
```

### Evaluate all verticals

```bash
python evaluation/run_swde_evaluation.py \
  --dataset-dir evaluationSet \
  --groundtruth-dir evaluationSet/groundtruth \
  --output-dir swde_evaluation_output
```

## Output Structure

```
swde_evaluation_output/
├── <vertical>/
│   ├── <website>/
│   │   ├── evaluation/
│   │   │   ├── report.html          # Interactive HTML report
│   │   │   ├── evaluation_charts.png # Visualization charts
│   │   │   ├── results.json         # Detailed results
│   │   │   └── summary.csv          # CSV summary
│   │   ├── result/                  # Agent output JSONs
│   │   ├── parsers/                 # Generated parser code
│   │   └── ...
│   └── _summary/
│       └── summary.json             # Vertical-level summary
```

## Reports

### HTML Report
- Overall performance metrics
- Per-attribute breakdown
- Sample extraction results
- Error analysis

### Charts
- Bar charts of precision/recall/F1 per attribute
- Pie chart of overall performance
- Stacked bar charts of TP/FP/FN
- F1 score comparison

### JSON Results
- Complete evaluation data
- Page-level details
- Field-level extraction results

### CSV Summary
- Easy-to-analyze tabular format
- Per-attribute metrics
- Confusion matrix data

## Evaluation Metrics

### Precision
Percentage of extracted values that match groundtruth:
```
Precision = True Positives / (True Positives + False Positives)
```

### Recall
Percentage of groundtruth values successfully extracted:
```
Recall = True Positives / (True Positives + False Negatives)
```

### F1 Score
Harmonic mean of precision and recall:
```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

## Matching Strategy

The evaluation uses **substring matching**: if a groundtruth value is contained in an extracted value, it's considered a match. This accounts for:
- Extra whitespace
- Case differences
- Additional extracted text around the target value

## Module Structure

- `groundtruth_loader.py` - Loads SWDE groundtruth files
- `metrics.py` - Computes evaluation metrics
- `evaluator.py` - Compares agent output with groundtruth
- `visualization.py` - Generates reports and charts
- `run_swde_evaluation.py` - Main evaluation script
- `test_evaluation.py` - Quick test script

## SWDE Dataset

The SWDE dataset contains:
- 8 verticals (auto, book, camera, job, movie, nbaplayer, restaurant, university)
- 10 websites per vertical
- 200-2,000 pages per website
- 3-5 attributes per vertical

See `evaluationSet/readme.txt` for full dataset documentation.

## Customization

### Modify matching logic
Edit `metrics.py:value_match()` to change how values are matched.

### Add new metrics
Add methods to `ExtractionMetrics` class in `metrics.py`.

### Customize reports
Modify `visualization.py` to change report format or add new visualizations.

## Troubleshooting

**Agent fails to run:**
- Check that main.py is in the parent directory
- Verify Python dependencies are installed
- Check logs in the output directory

**No JSON files generated:**
- Ensure agent completed successfully
- Check that result/ directory exists
- Verify HTML files are in correct location

**Evaluation errors:**
- Verify groundtruth files exist
- Check file encoding (should be UTF-8)
- Ensure JSON files are valid

## Example Results

After running evaluation, you'll see output like:

```
Evaluating book/abebooks...
Evaluation completed!
  Precision: 92.34%
  Recall: 88.12%
  F1 Score: 90.18%
```

Open `report.html` in a browser for detailed interactive results.
