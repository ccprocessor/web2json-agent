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

    def extract_all_values_from_json(self, json_data: Dict[str, Any]) -> List[str]:
        """
        Extract ALL values from JSON data (regardless of keys).
        Recursively traverses the entire JSON structure and collects all string/numeric values.

        Args:
            json_data: Parsed JSON data

        Returns:
            List of all values found in the JSON
        """
        values = []

        def collect_values(obj):
            """Recursively collect all values from nested dict/list."""
            if isinstance(obj, dict):
                for v in obj.values():
                    collect_values(v)
            elif isinstance(obj, list):
                for item in obj:
                    collect_values(item)
            elif obj is not None:
                # Convert to string and add to values list
                str_val = str(obj).strip()
                if str_val:  # Only add non-empty values
                    values.append(str_val)

        collect_values(json_data)
        return values

    def extract_matching_values(self, json_data: Dict[str, Any], groundtruth_values: List[str]) -> List[str]:
        """
        Extract values from JSON that match any of the groundtruth values.
        Uses value-based matching instead of key-based matching.

        Args:
            json_data: Parsed JSON data
            groundtruth_values: List of groundtruth values to search for

        Returns:
            List of unique values from JSON that match groundtruth (for precision calculation)
        """
        # Extract all values from JSON
        all_json_values = self.extract_all_values_from_json(json_data)

        # Find which JSON values match any groundtruth value
        from .metrics import ExtractionMetrics
        matching_values = []
        seen_values = set()  # Track seen values to avoid duplicates

        for json_val in all_json_values:
            # Normalize value for duplicate detection
            normalized = ExtractionMetrics.normalize_value(json_val)

            # Skip if we've already seen this value
            if normalized in seen_values:
                continue

            # Check if this value matches any groundtruth
            for gt_val in groundtruth_values:
                if ExtractionMetrics.value_match(json_val, gt_val):
                    matching_values.append(json_val)
                    seen_values.add(normalized)
                    break  # Don't check other groundtruth values

        return matching_values

    def extract_values_from_json(self, json_data: Dict[str, Any], attribute: str) -> List[str]:
        """
        Extract values for a specific attribute from JSON data.
        Uses VALUE-BASED matching instead of KEY-BASED matching.

        This method is now a placeholder - actual matching is done in evaluate_page()
        to avoid circular dependency with groundtruth values.

        Args:
            json_data: Parsed JSON data
            attribute: Attribute name (not used in value-based matching)

        Returns:
            Empty list (actual extraction happens in evaluate_page)
        """
        # Return empty list - we'll do the matching in evaluate_page
        # where we have access to groundtruth values
        return []

    def _key_matches(self, json_key: str, attribute: str) -> bool:
        """
        Check if JSON key matches attribute name.
        Handles variations like underscores, hyphens, case differences, and plurals.

        Args:
            json_key: Key from JSON
            attribute: Target attribute name

        Returns:
            True if they match
        """
        norm_key = json_key.lower().replace('_', '').replace('-', '').replace(' ', '')
        norm_attr = attribute.lower().replace('_', '').replace('-', '').replace(' ', '')

        # Exact match
        if norm_key == norm_attr:
            return True

        # Check plural forms (add/remove 's')
        if norm_key == norm_attr + 's' or norm_key + 's' == norm_attr:
            return True

        # Check 'es' plural (e.g., address/addresses)
        if norm_key == norm_attr + 'es' or norm_key + 'es' == norm_attr:
            return True

        return False

    def _extract_by_key(self, json_data: Dict[str, Any], attribute: str) -> List[str]:
        """
        Extract values from JSON by key matching (for display purposes).

        Args:
            json_data: Parsed JSON data
            attribute: Attribute name to look for

        Returns:
            List of values found under matching keys
        """
        values = []

        def extract_recursive(data, path=""):
            if isinstance(data, dict):
                for key, val in data.items():
                    if self._key_matches(key, attribute):
                        # Found matching key
                        if isinstance(val, list):
                            for item in val:
                                if isinstance(item, (str, int, float)) and item:
                                    values.append(str(item))
                        elif isinstance(val, (str, int, float)) and val:
                            values.append(str(val))
                    # Continue recursion
                    extract_recursive(val, f"{path}.{key}" if path else key)
            elif isinstance(data, list):
                for item in data:
                    extract_recursive(item, path)

        extract_recursive(json_data)
        return values

    def evaluate_page(
        self,
        vertical: str,
        website: str,
        page_id: str,
        agent_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate a single page using value-based matching.

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

            # Extract raw values from JSON based on key matching
            raw_extracted = self._extract_by_key(agent_output, attribute)

            # Extract matching values from agent output (value-based matching)
            extracted_values = self.extract_matching_values(agent_output, gt_values)

            # Compute metrics
            metrics = self.metrics_computer.compute_field_metrics(extracted_values, gt_values)
            field_metrics[attribute] = metrics

            # Determine if this is a match
            # Special case: Both GT and extracted are empty (all None/dash/N/A indicators)
            # This is a perfect match, not an error
            from evaluation.metrics import ExtractionMetrics
            is_both_empty = all(
                ExtractionMetrics.normalize_value(v) in ["none", "", "null", "na", "notfound"] or
                v in [None, "-", "N/A", "n/a", "(not found in JSON)"]
                for v in gt_values + extracted_values
            ) if (gt_values or extracted_values) else False

            # Match if: (1) has true positives, OR (2) both are empty indicators
            is_match = (metrics['true_positives'] > 0) or is_both_empty

            # Store details (include both raw and matched values)
            field_details[attribute] = {
                'groundtruth': gt_values,
                'extracted': extracted_values,  # Values that matched groundtruth
                'raw_extracted': raw_extracted,  # Raw values from JSON (by key)
                'match': is_match
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
