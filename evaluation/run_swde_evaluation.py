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

# Force change working directory to project root (fix IDE working directory issue)
project_root = Path(__file__).parent.parent
if Path.cwd() != project_root:
    print(f"⚠️  Warning: Changing working directory from {Path.cwd()} to {project_root}")
    os.chdir(project_root)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.evaluator import SWDEEvaluator
from evaluation.visualization import EvaluationReporter
from evaluation.schema_generator import SchemaGenerator
from web2json.config.settings import settings


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
        python_cmd: str = "python3",
        resume: bool = False,
        skip_agent: bool = False,
        skip_evaluation: bool = False,
        force: bool = False,
        use_predefined_schema: bool = False
    ):
        """
        Initialize the evaluation runner.

        Args:
            dataset_dir: Root directory of SWDE dataset
            groundtruth_dir: Directory containing groundtruth files
            output_root: Root directory for outputs
            python_cmd: Python command to use
            resume: Whether to resume from existing results (skip already completed)
            skip_agent: Skip agent execution if output already exists
            skip_evaluation: Skip evaluation if report already exists
            force: Force re-run everything (overrides resume/skip options)
            use_predefined_schema: Use predefined schema templates from groundtruth
        """
        self.dataset_dir = Path(dataset_dir)
        self.groundtruth_dir = Path(groundtruth_dir)
        self.output_root = Path(output_root)
        self.python_cmd = python_cmd
        self.resume = resume and not force
        self.skip_agent = skip_agent and not force
        self.skip_evaluation = skip_evaluation and not force
        self.force = force
        self.use_predefined_schema = use_predefined_schema

        self.output_root.mkdir(parents=True, exist_ok=True)

        # Global summary file path
        self.global_summary_file = self.output_root / "summary.json"

        # Clean previous evaluation results if not in resume mode
        if not self.resume:
            self._clean_evaluation_results()

        # Load or initialize global summary
        self.global_summary = self._load_global_summary()

        # Initialize schema generator and schema paths
        self.schema_generator = None
        self.schema_paths = {}
        if self.use_predefined_schema:
            self._initialize_schemas()

    def _clean_evaluation_results(self) -> None:
        """
        Clean all previous evaluation results.
        This includes:
        - Global summary.json
        - All evaluation/ directories in vertical/website folders
        - Vertical _summary/ directories
        - Integrated error reports

        Note: This preserves agent outputs (result/, parsers/, schemas/, etc.)
        """
        import shutil

        print("\n" + "="*80)
        print("🧹 Cleaning Previous Evaluation Results")
        print("="*80)

        cleaned_items = []

        # 1. Remove global summary.json
        if self.global_summary_file.exists():
            self.global_summary_file.unlink()
            cleaned_items.append(f"  ✓ Removed: {self.global_summary_file.name}")

        # 2. Remove integrated error reports
        integrated_report = self.output_root / "integrated_error_report.html"
        if integrated_report.exists():
            integrated_report.unlink()
            cleaned_items.append(f"  ✓ Removed: {integrated_report.name}")

        # 3. Traverse vertical directories and clean evaluation results
        for vertical_dir in self.output_root.iterdir():
            if not vertical_dir.is_dir():
                continue

            vertical_name = vertical_dir.name

            # Skip special directories
            if vertical_name.startswith('_') or vertical_name not in VERTICALS:
                continue

            # Remove vertical summary
            summary_dir = vertical_dir / "_summary"
            if summary_dir.exists():
                shutil.rmtree(summary_dir)
                cleaned_items.append(f"  ✓ Removed: {vertical_name}/_summary/")

            # Clean each website's evaluation directory
            for website_dir in vertical_dir.iterdir():
                if not website_dir.is_dir() or website_dir.name.startswith('_'):
                    continue

                eval_dir = website_dir / "evaluation"
                if eval_dir.exists():
                    shutil.rmtree(eval_dir)
                    cleaned_items.append(f"  ✓ Removed: {vertical_name}/{website_dir.name}/evaluation/")

        if cleaned_items:
            print("\nCleaned evaluation results:")
            for item in cleaned_items:
                print(item)
            print(f"\nTotal items cleaned: {len(cleaned_items)}")
        else:
            print("  ℹ No previous evaluation results found")

        print("="*80 + "\n")

    def _initialize_schemas(self) -> None:
        """Initialize schema generator and generate schema templates."""
        print("\n" + "="*80)
        print("Initializing Predefined Schema Templates from Groundtruth")
        print("="*80)

        self.schema_generator = SchemaGenerator(str(self.groundtruth_dir))

        # Generate schemas for all verticals and websites
        schema_output_dir = self.output_root / "_schemas"
        schema_output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Generating schema templates to: {schema_output_dir}")
        self.schema_paths = self.schema_generator.generate_all_schemas(
            verticals=VERTICALS,
            output_dir=schema_output_dir,
            sample_count=5
        )

        print("="*80)
        print(f"✓ Schema templates generated successfully")
        print("="*80 + "\n")

    def _load_global_summary(self) -> Dict:
        """Load or initialize the global summary."""
        if self.global_summary_file.exists():
            with open(self.global_summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                'timestamp': datetime.now().isoformat(),
                'verticals': {},
                'overall': {
                    'total_websites': 0,
                    'completed_websites': 0,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1': 0.0
                }
            }

    def _save_global_summary(self) -> None:
        """Save the global summary to file."""
        with open(self.global_summary_file, 'w', encoding='utf-8') as f:
            json.dump(self.global_summary, f, indent=2, ensure_ascii=False)
        print(f"✅ Global summary updated: {self.global_summary_file}")

    def _update_global_summary(self, vertical: str, website: str, results: Dict) -> None:
        """
        Update the global summary with new results.

        Args:
            vertical: Vertical name
            website: Website name
            results: Evaluation results
        """
        # Initialize vertical if not exists
        if vertical not in self.global_summary['verticals']:
            self.global_summary['verticals'][vertical] = {
                'websites': {},
                'metrics': {
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1': 0.0
                },
                'completed_websites': 0,
                'total_websites': len(VERTICALS.get(vertical, []))
            }

        # Add website results
        self.global_summary['verticals'][vertical]['websites'][website] = {
            'timestamp': datetime.now().isoformat(),
            'precision': results['overall_metrics']['precision'],
            'recall': results['overall_metrics']['recall'],
            'f1': results['overall_metrics']['f1'],
            'evaluated_pages': results['statistics']['evaluated_pages'],
            'errors': results['statistics']['errors'],
            'attribute_metrics': results['attribute_metrics']
        }

        # Update vertical metrics (average across all completed websites)
        vertical_data = self.global_summary['verticals'][vertical]
        completed_sites = list(vertical_data['websites'].values())
        if completed_sites:
            vertical_data['metrics']['precision'] = sum(s['precision'] for s in completed_sites) / len(completed_sites)
            vertical_data['metrics']['recall'] = sum(s['recall'] for s in completed_sites) / len(completed_sites)
            vertical_data['metrics']['f1'] = sum(s['f1'] for s in completed_sites) / len(completed_sites)
            vertical_data['completed_websites'] = len(completed_sites)

        # Update overall metrics (weighted average across all websites in all verticals)
        all_results = []
        total_websites = 0
        completed_websites = 0

        for vert_name, vert_data in self.global_summary['verticals'].items():
            total_websites += vert_data['total_websites']
            for site_results in vert_data['websites'].values():
                all_results.append(site_results)
                completed_websites += 1

        if all_results:
            self.global_summary['overall']['precision'] = sum(r['precision'] for r in all_results) / len(all_results)
            self.global_summary['overall']['recall'] = sum(r['recall'] for r in all_results) / len(all_results)
            self.global_summary['overall']['f1'] = sum(r['f1'] for r in all_results) / len(all_results)
            self.global_summary['overall']['completed_websites'] = completed_websites
            self.global_summary['overall']['total_websites'] = total_websites

        # Update timestamp
        self.global_summary['timestamp'] = datetime.now().isoformat()

        # Save to file
        self._save_global_summary()

    def _is_agent_completed(self, vertical: str, website: str) -> bool:
        """
        Check if agent has already generated results for a website.

        Args:
            vertical: Vertical name
            website: Website name

        Returns:
            True if agent output exists, False otherwise
        """
        if not self.skip_agent:
            return False

        output_dir = self.output_root / vertical / website
        result_dir = output_dir / "result"

        # Check if result directory exists and has JSON files
        if not result_dir.exists():
            return False

        json_files = list(result_dir.glob("*.json"))
        if not json_files:
            return False

        print(f"  ✓ Agent output found: {len(json_files)} result files")
        return True

    def _is_evaluation_completed(self, vertical: str, website: str) -> bool:
        """
        Check if evaluation has already been completed for a website.

        Args:
            vertical: Vertical name
            website: Website name

        Returns:
            True if evaluation report exists, False otherwise
        """
        if not self.skip_evaluation:
            return False

        eval_dir = self.output_root / vertical / website / "evaluation"
        report_file = eval_dir / "evaluation_report.json"

        if report_file.exists():
            print(f"  ✓ Evaluation report found: {report_file}")
            return True

        return False

    def _is_website_completed(self, vertical: str, website: str) -> bool:
        """
        Check if a website has already been fully evaluated.

        Args:
            vertical: Vertical name
            website: Website name

        Returns:
            True if already completed, False otherwise
        """
        if not self.resume:
            return False

        # Check global summary
        if vertical not in self.global_summary['verticals']:
            return False

        if website not in self.global_summary['verticals'][vertical]['websites']:
            return False

        # Also verify the files actually exist
        output_dir = self.output_root / vertical / website
        result_dir = output_dir / "result"
        eval_dir = output_dir / "evaluation"

        has_results = result_dir.exists() and list(result_dir.glob("*.json"))
        has_eval = (eval_dir / "evaluation_report.json").exists()

        if has_results and has_eval:
            print(f"  ✓ Found existing results and evaluation")
            return True
        else:
            print(f"  ⚠ Entry in summary but missing files (will re-run)")
            return False

    def _print_progress(self) -> None:
        """Print current overall progress and metrics."""
        overall = self.global_summary['overall']
        print(f"\n{'='*80}")
        print(f"📊 OVERALL PROGRESS")
        print(f"{'='*80}")
        print(f"Progress: {overall['completed_websites']}/{overall['total_websites']} websites completed")
        if overall['completed_websites'] > 0:
            print(f"Current Overall Metrics:")
            print(f"  Precision: {overall['precision']:.2%}")
            print(f"  Recall:    {overall['recall']:.2%}")
            print(f"  F1 Score:  {overall['f1']:.2%}")
        print(f"{'='*80}\n")

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

        # First try in the vertical subdirectory
        vertical_dir = self.dataset_dir / vertical
        if vertical_dir.exists():
            for pattern in patterns:
                matches = list(vertical_dir.glob(pattern))
                if matches:
                    return matches[0]

        # Fallback: try in the root dataset directory
        for pattern in patterns:
            matches = list(self.dataset_dir.glob(pattern))
            if matches:
                return matches[0]

        # Return None instead of raising exception (website may not exist in dataset)
        return None

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
        if self.use_predefined_schema:
            print(f"Mode: Using Predefined Schema from Groundtruth")
        else:
            print(f"Mode: Auto Schema Extraction")
        print(f"{'='*80}")

        # Get HTML directory
        html_dir = self.get_html_directory(vertical, website)
        if html_dir is None:
            print(f"⊘ Skipping {vertical}/{website}: HTML directory not found in dataset")
            raise FileNotFoundError(f"HTML directory not found for {vertical}/{website}")
        print(f"HTML directory: {html_dir}")

        # Create output directory
        output_dir = self.output_root / vertical / website
        output_dir.mkdir(parents=True, exist_ok=True)

        # If using predefined schema, call agent directly via Python API
        if self.use_predefined_schema:
            # Get schema template path
            schema_path = self.schema_paths.get(vertical, {}).get(website)
            if not schema_path:
                raise ValueError(f"Schema template not found for {vertical}/{website}")

            print(f"Using schema template: {schema_path}")

            # Load schema template from file
            import json
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_template = json.load(f)

            print(f"Loaded schema with fields: {list(schema_template.keys())}")

            # Import and call agent directly
            from web2json.agent import ParserAgent

            # Get HTML files
            html_files = sorted([str(f) for f in Path(html_dir).glob("*.htm*")])
            if not html_files:
                raise FileNotFoundError(f"No HTML files found in {html_dir}")

            print(f"Found {len(html_files)} HTML files")

            # Create agent with predefined schema
            agent = ParserAgent(
                output_dir=str(output_dir),
                schema_mode="predefined",
                schema_template=schema_template  # Pass loaded schema dict
            )

            # Run agent
            print("Running agent with predefined schema (this may take a while)...")
            print("-" * 80)

            try:
                result = agent.generate_parser(
                    html_files=html_files,
                    domain=website,
                    iteration_rounds=3
                    # schema_mode and schema_template already set in agent initialization
                )

                print("-" * 80)
                if not result.get('success'):
                    error_msg = result.get('error', 'Unknown error')
                    print(f"Error: Agent failed - {error_msg}")
                    raise RuntimeError(f"Agent failed: {error_msg}")

                print("✅ Agent completed successfully!")

                # Return result directory
                result_dir = output_dir / "result"
                if not result_dir.exists():
                    raise FileNotFoundError(f"Result directory not found: {result_dir}")

                return result_dir

            except Exception as e:
                print(f"Error running agent: {e}")
                raise

        else:
            # Original subprocess-based approach
            cmd = [
                self.python_cmd,
                "-m", "web2json.main",
                "-d", str(html_dir),
                "-o", str(output_dir),
                "--domain", website
            ]

            print(f"Command: {' '.join(cmd)}")
            print("Running agent (this may take a while)...")
            print("-" * 80)

            try:
                result = subprocess.run(
                    cmd,
                    cwd=Path(__file__).parent.parent,
                    timeout=3600  # 1 hour timeout
                )

                print("-" * 80)
                if result.returncode != 0:
                    print(f"Error running agent (return code {result.returncode})")
                    raise RuntimeError(f"Agent failed with return code {result.returncode}")

                print("✅ Agent completed successfully!")

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
        print(f"\n{'='*80}")
        print(f"Processing: {vertical}/{website}")
        print(f"{'='*80}")

        # Check if already completed (resume mode)
        if self._is_website_completed(vertical, website):
            print(f"⏭️  Skipping {vertical}/{website} - already completed (resume mode)")
            # Return existing results from global summary
            return self.global_summary['verticals'][vertical]['websites'][website]

        # Check if agent output already exists
        skip_agent = self._is_agent_completed(vertical, website)

        # Run agent if needed
        if skip_agent:
            print(f"⏭️  Skipping agent execution - using existing output")
            output_dir = self.output_root / vertical / website
            agent_output_dir = output_dir / "result"
        else:
            agent_output_dir = self.run_agent(vertical, website)

        # Check if evaluation already exists
        skip_evaluation = self._is_evaluation_completed(vertical, website)

        # Evaluate if needed
        if skip_evaluation:
            print(f"⏭️  Skipping evaluation - using existing report")
            # Load existing evaluation results
            eval_dir = self.output_root / vertical / website / "evaluation"
            report_file = eval_dir / "evaluation_report.json"
            with open(report_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
        else:
            results = self.evaluate_website(vertical, website, agent_output_dir)
            # Generate reports
            self.generate_reports(vertical, website, results)

        # Update global summary (always update to ensure consistency)
        self._update_global_summary(vertical, website, results)

        # Print current overall progress
        self._print_progress()

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
            except FileNotFoundError as e:
                # Website not in dataset - skip silently
                print(f"⊘ Skipped {vertical}/{website}: {e}")
            except Exception as e:
                print(f"✗ Error processing {vertical}/{website}: {e}")
                import traceback
                traceback.print_exc()

        # Generate summary report
        self.generate_vertical_summary(vertical, all_results)

        # Generate integrated error report for this vertical
        if all_results:
            integrated_report_path = self.output_root / vertical / "_summary" / "integrated_error_report.html"
            print(f"\nGenerating integrated error report for {vertical}...")
            EvaluationReporter.generate_integrated_report(all_results, integrated_report_path)

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

        if 'average_metrics' in summary:
            print(f"\nAverage metrics for {vertical}:")
            print(f"  Precision: {summary['average_metrics']['precision']:.2%}")
            print(f"  Recall: {summary['average_metrics']['recall']:.2%}")
            print(f"  F1 Score: {summary['average_metrics']['f1']:.2%}")
        else:
            print(f"\nNo successful evaluations for {vertical} - cannot compute average metrics")

    def load_existing_results(self, vertical: str = None, website: str = None) -> List[Dict]:
        """
        Load existing evaluation results from disk.

        Args:
            vertical: Optional vertical name to filter (if None, load all)
            website: Optional website name to filter (requires vertical)

        Returns:
            List of evaluation results
        """
        results_list = []

        if website and vertical:
            # Load single website result
            eval_file = self.output_root / vertical / website / "evaluation" / "results.json"
            if eval_file.exists():
                with open(eval_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                    results_list.append(results)
        elif vertical:
            # Load all websites in vertical
            vertical_dir = self.output_root / vertical
            if vertical_dir.exists():
                for website_dir in vertical_dir.iterdir():
                    if website_dir.is_dir() and not website_dir.name.startswith('_'):
                        eval_file = website_dir / "evaluation" / "results.json"
                        if eval_file.exists():
                            with open(eval_file, 'r', encoding='utf-8') as f:
                                results = json.load(f)
                                results_list.append(results)
        else:
            # Load all results
            for vert_dir in self.output_root.iterdir():
                if vert_dir.is_dir() and vert_dir.name in VERTICALS:
                    for website_dir in vert_dir.iterdir():
                        if website_dir.is_dir() and not website_dir.name.startswith('_'):
                            eval_file = website_dir / "evaluation" / "results.json"
                            if eval_file.exists():
                                with open(eval_file, 'r', encoding='utf-8') as f:
                                    results = json.load(f)
                                    results_list.append(results)

        return results_list


def main():
    parser = argparse.ArgumentParser(
        description='Run SWDE evaluation for web2json-agent',
        epilog='All options can be configured in .env file. Command line arguments override .env settings.'
    )
    parser.add_argument('--dataset-dir', type=str, default=settings.swde_dataset_dir,
                       help=f'Root directory of SWDE dataset (default: {settings.swde_dataset_dir})')
    parser.add_argument('--groundtruth-dir', type=str, default=settings.swde_groundtruth_dir,
                       help=f'Directory containing groundtruth files (default: {settings.swde_groundtruth_dir})')
    parser.add_argument('--output-dir', type=str, default=settings.swde_output_dir,
                       help=f'Root directory for outputs (default: {settings.swde_output_dir})')
    parser.add_argument('--vertical', type=str, choices=list(VERTICALS.keys()),
                       help='Vertical to evaluate (if not specified, evaluate all)')
    parser.add_argument('--website', type=str,
                       help='Specific website to evaluate (requires --vertical)')
    parser.add_argument('--python', type=str, default=settings.swde_python_cmd,
                       help=f'Python command to use (default: {settings.swde_python_cmd})')
    parser.add_argument('--resume', action='store_true', default=settings.swde_resume,
                       help=f'Resume from previous run (default: {settings.swde_resume})')
    parser.add_argument('--skip-agent', action='store_true', default=settings.swde_skip_agent,
                       help=f'Skip agent execution if output already exists (default: {settings.swde_skip_agent})')
    parser.add_argument('--skip-evaluation', action='store_true', default=settings.swde_skip_evaluation,
                       help=f'Skip evaluation if report already exists (default: {settings.swde_skip_evaluation})')
    parser.add_argument('--force', action='store_true', default=settings.swde_force,
                       help=f'Force re-run everything (default: {settings.swde_force})')
    parser.add_argument('--use-predefined-schema', action='store_true', default=settings.swde_use_predefined_schema,
                       help=f'Use predefined schema templates generated from groundtruth (default: {settings.swde_use_predefined_schema})')

    args = parser.parse_args()

    # Print configuration
    print(f"\n{'='*80}")
    print(f"SWDE Evaluation Configuration")
    print(f"{'='*80}")
    print(f"Dataset directory:       {args.dataset_dir}")
    print(f"Groundtruth directory:   {args.groundtruth_dir}")
    print(f"Output directory:        {args.output_dir}")
    print(f"Python command:          {args.python}")
    print(f"Use predefined schema:   {args.use_predefined_schema}")
    print(f"Resume mode:             {args.resume}")
    print(f"Skip agent:              {args.skip_agent}")
    print(f"Skip evaluation:         {args.skip_evaluation}")
    print(f"Force mode:              {args.force}")
    if args.vertical:
        print(f"Target vertical:         {args.vertical}")
    if args.website:
        print(f"Target website:          {args.website}")
    print(f"{'='*80}\n")

    # Validate arguments
    if args.website and not args.vertical:
        parser.error("--website requires --vertical")

    # Create runner
    runner = SWDEEvaluationRunner(
        dataset_dir=args.dataset_dir,
        groundtruth_dir=args.groundtruth_dir,
        output_root=args.output_dir,
        python_cmd=args.python,
        resume=args.resume,
        skip_agent=args.skip_agent,
        skip_evaluation=args.skip_evaluation,
        force=args.force,
        use_predefined_schema=args.use_predefined_schema
    )

    # Run evaluation
    if args.website:
        # Single website
        results = runner.run_single_website(args.vertical, args.website)
        # Generate single-website integrated report (just shows that one website)
        integrated_report_path = runner.output_root / args.vertical / args.website / "evaluation" / "report.html"
        print(f"\n{'='*80}")
        print(f"Report saved to: {integrated_report_path}")
        print(f"{'='*80}")
    elif args.vertical:
        # All websites in vertical
        runner.run_vertical(args.vertical)
    else:
        # All verticals
        print(f"\n{'#'*80}")
        print(f"# RUNNING FULL SWDE EVALUATION")
        print(f"# Total verticals: {len(VERTICALS)}")
        print(f"# Total websites: {sum(len(sites) for sites in VERTICALS.values())}")
        print(f"# Resume mode: {'ON' if args.resume else 'OFF'}")
        print(f"# Skip agent: {'ON' if args.skip_agent else 'OFF'}")
        print(f"# Skip evaluation: {'ON' if args.skip_evaluation else 'OFF'}")
        print(f"# Force mode: {'ON' if args.force else 'OFF'}")
        print(f"# Predefined schema: {'ON' if args.use_predefined_schema else 'OFF'}")
        print(f"{'#'*80}\n")

        all_results = []
        for vertical in VERTICALS.keys():
            print(f"\n{'#'*80}")
            print(f"# Processing vertical: {vertical}")
            print(f"{'#'*80}")
            try:
                vertical_results = runner.run_vertical(vertical)
                all_results.extend(vertical_results)
            except Exception as e:
                print(f"Error processing vertical {vertical}: {e}")
                import traceback
                traceback.print_exc()

        # Generate integrated error report for all results
        if all_results:
            integrated_report_path = runner.output_root / "integrated_error_report.html"
            print(f"\n{'='*80}")
            print(f"Generating complete integrated error report for all verticals...")
            print(f"{'='*80}")
            EvaluationReporter.generate_integrated_report(all_results, integrated_report_path)

        # Print final summary
        print(f"\n{'#'*80}")
        print(f"# EVALUATION COMPLETE!")
        print(f"{'#'*80}")
        runner._print_progress()
        print(f"\nGlobal summary saved to: {runner.global_summary_file}")



if __name__ == '__main__':
    main()
