"""
Main script to run SWDE evaluation

This script runs the web2json agent on SWDE dataset and evaluates the results.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.evaluator import SWDEEvaluator
from evaluation.visualization import EvaluationReporter


# SWDE dataset configuration
VERTICALS = {
    'auto': ['autoweb', 'aol', 'cars', 'carquotes', 'motortrend', 'yahoo', 'automotive', 'kbb', 'msn', 'thecarconnection'],
    'book': ['abebooks', 'amazon', 'barnesandnoble', 'bookdepository', 'booksamillion', 'borders', 'buy', 'christianbook', 'deepdiscount', 'waterstones'],
    'camera': ['amazon', 'buzzillions', 'cnet', 'ecost', 'jr', 'newegg', 'onsale', 'pcmag', 'ritz', 'thenerds'],
    'job': ['careerbuilder', 'dice', 'hotjobs', 'jobtarget', 'monster', 'jobcircle', 'jobs', 'nettemps', 'techcentric', 'employment'],
    'movie': ['allmovie', 'amctv', 'blockbuster', 'hollywood', 'iheartmovies', 'imdb', 'metacritic', 'msn', 'rottentomatoes', 'yahoo'],
    'nbaplayer': ['espn', 'fanhouse', 'foxsports', 'msnca', 'si', 'slam', 'sportingnews', 'usatoday', 'yahoo', 'nba'],
    'restaurant': ['fodors', 'frommers', 'gayot', 'localcom', 'restaurantica', 'thestranger', 'timeout', 'tripadvisor', 'usdininguides', 'zagat'],
    'university': ['collegeboard', 'collegenavigator', 'collegetoolkit', 'embark', 'matchcollege', 'princetonreview', 'studentaid', 'usnews', 'ecampustours', 'collegeprowler']
}

ATTRIBUTES = {
    'auto': ['model', 'price', 'engine', 'fuel_economy'],
    'book': ['title', 'author', 'isbn_13', 'publisher', 'publication_date'],
    'camera': ['model', 'price', 'manufacturer'],
    'job': ['title', 'company', 'location', 'date_posted'],
    'movie': ['title', 'director', 'genre', 'mpaa_rating'],
    'nbaplayer': ['name', 'team', 'height', 'weight'],
    'restaurant': ['name', 'address', 'phone', 'cuisine'],
    'university': ['name', 'phone', 'website', 'type']
}


class SWDEEvaluationRunner:
    """Runs the complete SWDE evaluation pipeline."""

    def __init__(
        self,
        dataset_dir: str,
        groundtruth_dir: str,
        output_root: str,
        python_cmd: str = "python3"
    ):
        """
        Initialize the evaluation runner.

        Args:
            dataset_dir: Root directory of SWDE dataset
            groundtruth_dir: Directory containing groundtruth files
            output_root: Root directory for outputs
            python_cmd: Python command to use
        """
        self.dataset_dir = Path(dataset_dir)
        self.groundtruth_dir = Path(groundtruth_dir)
        self.output_root = Path(output_root)
        self.python_cmd = python_cmd

        self.output_root.mkdir(parents=True, exist_ok=True)

    def get_html_directory(self, vertical: str, website: str) -> Path:
        """
        Get the HTML directory for a vertical-website combination.

        Args:
            vertical: Vertical name
            website: Website name

        Returns:
            Path to HTML directory
        """
        # Try different naming patterns
        patterns = [
            f"{vertical}-{website}(*)",
            f"{vertical}-{website}",
        ]

        for pattern in patterns:
            matches = list(self.dataset_dir.glob(pattern))
            if matches:
                return matches[0]

        raise FileNotFoundError(f"HTML directory not found for {vertical}/{website}")

    def run_agent(self, vertical: str, website: str) -> Path:
        """
        Run the web2json agent on a website.

        Args:
            vertical: Vertical name
            website: Website name

        Returns:
            Path to agent output directory
        """
        print(f"\n{'='*80}")
        print(f"Running agent for: {vertical}/{website}")
        print(f"{'='*80}")

        # Get HTML directory
        html_dir = self.get_html_directory(vertical, website)
        print(f"HTML directory: {html_dir}")

        # Create output directory
        output_dir = self.output_root / vertical / website
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run the agent
        cmd = [
            self.python_cmd,
            "main.py",
            "-d", str(html_dir),
            "-o", str(output_dir),
            "--domain", website,
            "--skip-config-check"
        ]

        print(f"Command: {' '.join(cmd)}")
        print("Running agent (this may take a while)...")

        try:
            result = subprocess.run(
                cmd,
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )

            if result.returncode != 0:
                print(f"Error running agent:")
                print(result.stderr)
                raise RuntimeError(f"Agent failed with return code {result.returncode}")

            print("Agent completed successfully!")

            # Return result directory
            result_dir = output_dir / "result"
            if not result_dir.exists():
                raise FileNotFoundError(f"Result directory not found: {result_dir}")

            return result_dir

        except subprocess.TimeoutExpired:
            print("Agent execution timed out!")
            raise

    def evaluate_website(self, vertical: str, website: str, agent_output_dir: Path) -> Dict:
        """
        Evaluate agent output for a website.

        Args:
            vertical: Vertical name
            website: Website name
            agent_output_dir: Directory containing agent output

        Returns:
            Evaluation results
        """
        print(f"\nEvaluating {vertical}/{website}...")

        evaluator = SWDEEvaluator(str(self.groundtruth_dir))
        results = evaluator.evaluate_website(vertical, website, agent_output_dir)

        print(f"Evaluation completed!")
        print(f"  Precision: {results['overall_metrics']['precision']:.2%}")
        print(f"  Recall: {results['overall_metrics']['recall']:.2%}")
        print(f"  F1 Score: {results['overall_metrics']['f1']:.2%}")

        return results

    def generate_reports(self, vertical: str, website: str, results: Dict) -> None:
        """
        Generate evaluation reports.

        Args:
            vertical: Vertical name
            website: Website name
            results: Evaluation results
        """
        report_dir = self.output_root / vertical / website / "evaluation"
        reporter = EvaluationReporter(report_dir)
        reporter.generate_full_report(results)

    def run_single_website(self, vertical: str, website: str) -> Dict:
        """
        Run complete evaluation for a single website.

        Args:
            vertical: Vertical name
            website: Website name

        Returns:
            Evaluation results
        """
        # Run agent
        agent_output_dir = self.run_agent(vertical, website)

        # Evaluate
        results = self.evaluate_website(vertical, website, agent_output_dir)

        # Generate reports
        self.generate_reports(vertical, website, results)

        return results

    def run_vertical(self, vertical: str) -> List[Dict]:
        """
        Run evaluation for all websites in a vertical.

        Args:
            vertical: Vertical name

        Returns:
            List of evaluation results
        """
        if vertical not in VERTICALS:
            raise ValueError(f"Unknown vertical: {vertical}")

        websites = VERTICALS[vertical]
        all_results = []

        for website in websites:
            try:
                results = self.run_single_website(vertical, website)
                all_results.append(results)
            except Exception as e:
                print(f"Error processing {vertical}/{website}: {e}")
                import traceback
                traceback.print_exc()

        # Generate summary report
        self.generate_vertical_summary(vertical, all_results)

        return all_results

    def generate_vertical_summary(self, vertical: str, results_list: List[Dict]) -> None:
        """
        Generate summary report for a vertical.

        Args:
            vertical: Vertical name
            results_list: List of evaluation results
        """
        summary_dir = self.output_root / vertical / "_summary"
        summary_dir.mkdir(parents=True, exist_ok=True)

        # Aggregate statistics
        summary = {
            'vertical': vertical,
            'timestamp': datetime.now().isoformat(),
            'total_websites': len(results_list),
            'websites': {}
        }

        for results in results_list:
            website = results['website']
            summary['websites'][website] = {
                'precision': results['overall_metrics']['precision'],
                'recall': results['overall_metrics']['recall'],
                'f1': results['overall_metrics']['f1'],
                'evaluated_pages': results['statistics']['evaluated_pages'],
                'errors': results['statistics']['errors']
            }

        # Calculate average metrics
        if results_list:
            avg_precision = sum(r['overall_metrics']['precision'] for r in results_list) / len(results_list)
            avg_recall = sum(r['overall_metrics']['recall'] for r in results_list) / len(results_list)
            avg_f1 = sum(r['overall_metrics']['f1'] for r in results_list) / len(results_list)

            summary['average_metrics'] = {
                'precision': avg_precision,
                'recall': avg_recall,
                'f1': avg_f1
            }

        # Save summary
        summary_file = summary_dir / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        print(f"\nVertical summary saved to: {summary_file}")
        print(f"\nAverage metrics for {vertical}:")
        print(f"  Precision: {summary['average_metrics']['precision']:.2%}")
        print(f"  Recall: {summary['average_metrics']['recall']:.2%}")
        print(f"  F1 Score: {summary['average_metrics']['f1']:.2%}")


def main():
    parser = argparse.ArgumentParser(description='Run SWDE evaluation for web2json-agent')
    parser.add_argument('--dataset-dir', type=str, required=True,
                       help='Root directory of SWDE dataset')
    parser.add_argument('--groundtruth-dir', type=str, required=True,
                       help='Directory containing groundtruth files')
    parser.add_argument('--output-dir', type=str, required=True,
                       help='Root directory for outputs')
    parser.add_argument('--vertical', type=str, choices=list(VERTICALS.keys()),
                       help='Vertical to evaluate (if not specified, evaluate all)')
    parser.add_argument('--website', type=str,
                       help='Specific website to evaluate (requires --vertical)')
    parser.add_argument('--python', type=str, default='python3',
                       help='Python command to use (default: python3)')

    args = parser.parse_args()

    # Validate arguments
    if args.website and not args.vertical:
        parser.error("--website requires --vertical")

    # Create runner
    runner = SWDEEvaluationRunner(
        dataset_dir=args.dataset_dir,
        groundtruth_dir=args.groundtruth_dir,
        output_root=args.output_dir,
        python_cmd=args.python
    )

    # Run evaluation
    if args.website:
        # Single website
        runner.run_single_website(args.vertical, args.website)
    elif args.vertical:
        # All websites in vertical
        runner.run_vertical(args.vertical)
    else:
        # All verticals
        for vertical in VERTICALS.keys():
            print(f"\n{'#'*80}")
            print(f"# Processing vertical: {vertical}")
            print(f"{'#'*80}")
            try:
                runner.run_vertical(vertical)
            except Exception as e:
                print(f"Error processing vertical {vertical}: {e}")
                import traceback
                traceback.print_exc()


if __name__ == '__main__':
    main()
