"""
Quick test script for SWDE evaluation system

This script runs a quick test on a small sample to verify the evaluation system works.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.run_swde_evaluation import SWDEEvaluationRunner


def test_evaluation():
    """Run a quick test on one website."""

    # Configuration
    dataset_dir = "/Users/brown/Projects/AILabProject/web2json-agent/evaluationSet"
    groundtruth_dir = "/Users/brown/Projects/AILabProject/web2json-agent/evaluationSet/groundtruth"
    output_dir = "/Users/brown/Projects/AILabProject/web2json-agent/swde_evaluation_output"

    # Test with book/abebooks (first website in book vertical)
    vertical = "book"
    website = "abebooks"

    print("="*80)
    print("SWDE Evaluation System Test")
    print("="*80)
    print(f"\nTesting with: {vertical}/{website}")
    print(f"Dataset directory: {dataset_dir}")
    print(f"Groundtruth directory: {groundtruth_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Create runner
    runner = SWDEEvaluationRunner(
        dataset_dir=dataset_dir,
        groundtruth_dir=groundtruth_dir,
        output_root=output_dir
    )

    # Run evaluation
    try:
        results = runner.run_single_website(vertical, website)

        print("\n" + "="*80)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"\nFinal Results for {vertical}/{website}:")
        print(f"  Precision: {results['overall_metrics']['precision']:.2%}")
        print(f"  Recall: {results['overall_metrics']['recall']:.2%}")
        print(f"  F1 Score: {results['overall_metrics']['f1']:.2%}")
        print(f"  Evaluated Pages: {results['statistics']['evaluated_pages']}")
        print(f"\nReports saved to: {output_dir}/{vertical}/{website}/evaluation/")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == '__main__':
    success = test_evaluation()
    sys.exit(0 if success else 1)
