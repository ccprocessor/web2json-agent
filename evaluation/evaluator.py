"""
Evaluator for comparing agent output with SWDE groundtruth
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from .groundtruth_loader import GroundtruthLoader
from .metrics import ExtractionMetrics


class SWDEEvaluator:
    """Evaluates agent output against SWDE groundtruth."""

    def __init__(self, groundtruth_dir: str):
        """
        Initialize the evaluator.

        Args:
            groundtruth_dir: Path to groundtruth directory
        """
        self.gt_loader = GroundtruthLoader(groundtruth_dir)
        self.metrics_computer = ExtractionMetrics()

    def load_agent_output(self, output_file: Path) -> Optional[Dict[str, Any]]:
        """
        Load agent-generated JSON output.

        Args:
            output_file: Path to agent output JSON file

        Returns:
            Parsed JSON data or None if error
        """
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {output_file}: {e}")
            return None

    def extract_values_from_json(self, json_data: Dict[str, Any], attribute: str) -> List[str]:
        """
        Extract values for a specific attribute from JSON data.
        Searches recursively through the JSON structure.

        Args:
            json_data: Parsed JSON data
            attribute: Attribute name to search for

        Returns:
            List of values found
        """
        values = []

        def search_dict(obj, key):
            """Recursively search for key in nested dict/list."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    # Check if key matches (case-insensitive, allowing underscores/hyphens)
                    if self._key_matches(k, key):
                        if isinstance(v, list):
                            values.extend([str(item) for item in v if item])
                        elif v is not None:
                            values.append(str(v))
                    # Continue searching recursively
                    search_dict(v, key)
            elif isinstance(obj, list):
                for item in obj:
                    search_dict(item, key)

        search_dict(json_data, attribute)
        return values

    def _key_matches(self, json_key: str, attribute: str) -> bool:
        """
        Check if JSON key matches attribute name.
        Handles variations like underscores, hyphens, case differences.

        Args:
            json_key: Key from JSON
            attribute: Target attribute name

        Returns:
            True if they match
        """
        norm_key = json_key.lower().replace('_', '').replace('-', '').replace(' ', '')
        norm_attr = attribute.lower().replace('_', '').replace('-', '').replace(' ', '')
        return norm_key == norm_attr

    def evaluate_page(
        self,
        vertical: str,
        website: str,
        page_id: str,
        agent_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a single page.

        Args:
            vertical: Vertical name
            website: Website name
            page_id: Page ID
            agent_output: Agent's extracted JSON

        Returns:
            Evaluation results for this page
        """
        attributes = self.gt_loader.get_attributes(vertical, website)
        field_metrics = {}
        field_details = {}

        for attribute in attributes:
            # Get groundtruth
            gt_values = self.gt_loader.get_groundtruth(vertical, website, page_id, attribute)

            # Extract from agent output
            extracted_values = self.extract_values_from_json(agent_output, attribute)

            # Compute metrics
            metrics = self.metrics_computer.compute_field_metrics(extracted_values, gt_values)
            field_metrics[attribute] = metrics

            # Store details
            field_details[attribute] = {
                'groundtruth': gt_values,
                'extracted': extracted_values,
                'match': metrics['true_positives'] > 0
            }

        return {
            'page_id': page_id,
            'field_metrics': field_metrics,
            'field_details': field_details
        }

    def evaluate_website(
        self,
        vertical: str,
        website: str,
        output_dir: Path
    ) -> Dict[str, Any]:
        """
        Evaluate all pages for a website.

        Args:
            vertical: Vertical name
            website: Website name
            output_dir: Directory containing agent output JSON files

        Returns:
            Evaluation results for this website
        """
        # Load groundtruth for this vertical
        self.gt_loader.load_vertical(vertical)

        page_ids = self.gt_loader.get_all_page_ids(vertical, website)
        page_results = []
        errors = []

        for page_id in sorted(page_ids):
            # Look for agent output file
            json_file = output_dir / f"{page_id}.json"

            if not json_file.exists():
                errors.append({
                    'page_id': page_id,
                    'error': 'Output file not found'
                })
                continue

            # Load agent output
            agent_output = self.load_agent_output(json_file)
            if agent_output is None:
                errors.append({
                    'page_id': page_id,
                    'error': 'Failed to parse JSON'
                })
                continue

            # Evaluate this page
            page_result = self.evaluate_page(vertical, website, page_id, agent_output)
            page_results.append(page_result)

        # Aggregate metrics
        attribute_metrics = self.metrics_computer.compute_attribute_level_metrics(page_results)

        # Overall metrics (average across attributes)
        overall_precision = sum(m['precision'] for m in attribute_metrics.values()) / len(attribute_metrics) if attribute_metrics else 0.0
        overall_recall = sum(m['recall'] for m in attribute_metrics.values()) / len(attribute_metrics) if attribute_metrics else 0.0
        overall_f1 = sum(m['f1'] for m in attribute_metrics.values()) / len(attribute_metrics) if attribute_metrics else 0.0

        return {
            'vertical': vertical,
            'website': website,
            'page_results': page_results,
            'attribute_metrics': attribute_metrics,
            'overall_metrics': {
                'precision': overall_precision,
                'recall': overall_recall,
                'f1': overall_f1
            },
            'statistics': {
                'total_pages': len(page_ids),
                'evaluated_pages': len(page_results),
                'errors': len(errors)
            },
            'errors': errors
        }
