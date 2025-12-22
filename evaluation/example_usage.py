"""
Simple example showing how to use the SWDE evaluation system
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.run_swde_evaluation import SWDEEvaluationRunner


def main():
    """
    Example: Evaluate web2json-agent on a single SWDE website
    """

    # Paths configuration
    dataset_dir = "/Users/brown/Projects/AILabProject/web2json-agent/evaluationSet"
    groundtruth_dir = "/Users/brown/Projects/AILabProject/web2json-agent/evaluationSet/groundtruth"
    output_dir = "/Users/brown/Projects/AILabProject/web2json-agent/swde_evaluation_output"

    # Choose what to evaluate
    vertical = "book"      # Options: auto, book, camera, job, movie, nbaplayer, restaurant, university
    website = "abebooks"   # See VERTICALS dict in run_swde_evaluation.py for options

    print(f"SWDE Evaluation Example")
    print(f"Vertical: {vertical}")
    print(f"Website: {website}")
    print()

    # Create evaluation runner
    runner = SWDEEvaluationRunner(
        dataset_dir=dataset_dir,
        groundtruth_dir=groundtruth_dir,
        output_root=output_dir
    )

    # Run evaluation on a single website
    # This will:
    # 1. Run the agent on all HTML files for this website
    # 2. Evaluate the extracted JSON against groundtruth
    # 3. Generate detailed reports with visualizations
    results = runner.run_single_website(vertical, website)

    # Print summary
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80)
    print(f"\nOverall Metrics:")
    print(f"  Precision: {results['overall_metrics']['precision']:.2%}")
    print(f"  Recall:    {results['overall_metrics']['recall']:.2%}")
    print(f"  F1 Score:  {results['overall_metrics']['f1']:.2%}")

    print(f"\nPer-Attribute Metrics:")
    for attr, metrics in results['attribute_metrics'].items():
        print(f"  {attr:20s} - Precision: {metrics['precision']:.2%}, "
              f"Recall: {metrics['recall']:.2%}, F1: {metrics['f1']:.2%}")

    print(f"\nStatistics:")
    print(f"  Total Pages:     {results['statistics']['total_pages']}")
    print(f"  Evaluated Pages: {results['statistics']['evaluated_pages']}")
    print(f"  Errors:          {results['statistics']['errors']}")

    print(f"\nReports saved to:")
    report_dir = Path(output_dir) / vertical / website / "evaluation"
    print(f"  {report_dir}/report.html")
    print(f"  {report_dir}/evaluation_charts.png")
    print(f"  {report_dir}/results.json")
    print(f"  {report_dir}/summary.csv")


if __name__ == '__main__':
    main()
