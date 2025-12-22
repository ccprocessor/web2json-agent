"""
Evaluation Metrics for SWDE Dataset

This module computes various metrics for evaluating extraction quality.
"""

from typing import List, Dict, Any
from collections import defaultdict


class ExtractionMetrics:
    """Computes extraction metrics."""

    @staticmethod
    def normalize_value(value: str) -> str:
        """
        Normalize a value for comparison.

        Args:
            value: Raw value string

        Returns:
            Normalized value
        """
        if value is None:
            return ""
        # Remove extra whitespace, convert to lowercase for comparison
        return ' '.join(str(value).split()).strip().lower()

    @staticmethod
    def value_match(extracted: str, groundtruth: str) -> bool:
        """
        Check if extracted value matches groundtruth.
        Uses substring matching: if groundtruth is contained in extracted value, it's a match.

        Args:
            extracted: Extracted value
            groundtruth: Groundtruth value

        Returns:
            True if match, False otherwise
        """
        if not groundtruth:
            return False

        norm_extracted = ExtractionMetrics.normalize_value(extracted)
        norm_groundtruth = ExtractionMetrics.normalize_value(groundtruth)

        if not norm_extracted or not norm_groundtruth:
            return False

        # Check if groundtruth is contained in extracted
        return norm_groundtruth in norm_extracted

    @staticmethod
    def compute_field_metrics(extracted_values: List[str], groundtruth_values: List[str]) -> Dict[str, float]:
        """
        Compute metrics for a single field.

        Args:
            extracted_values: List of extracted values
            groundtruth_values: List of groundtruth values

        Returns:
            Dictionary with precision, recall, and F1 score
        """
        if not groundtruth_values:
            # No groundtruth values - if we extracted nothing, that's correct
            precision = 1.0 if not extracted_values else 0.0
            recall = 1.0
            f1 = 1.0 if precision == 1.0 else 0.0
            return {
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'true_positives': 0,
                'false_positives': len(extracted_values),
                'false_negatives': 0,
                'extracted_count': len(extracted_values),
                'groundtruth_count': 0
            }

        # Find matches
        true_positives = 0
        matched_gt = set()

        for ext_val in extracted_values:
            for i, gt_val in enumerate(groundtruth_values):
                if i not in matched_gt and ExtractionMetrics.value_match(ext_val, gt_val):
                    true_positives += 1
                    matched_gt.add(i)
                    break

        false_positives = len(extracted_values) - true_positives
        false_negatives = len(groundtruth_values) - true_positives

        # Calculate metrics
        precision = true_positives / len(extracted_values) if extracted_values else 0.0
        recall = true_positives / len(groundtruth_values) if groundtruth_values else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'extracted_count': len(extracted_values),
            'groundtruth_count': len(groundtruth_values)
        }

    @staticmethod
    def aggregate_metrics(metrics_list: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Aggregate metrics across multiple pages.

        Args:
            metrics_list: List of metrics dictionaries

        Returns:
            Aggregated metrics
        """
        if not metrics_list:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'total_true_positives': 0,
                'total_false_positives': 0,
                'total_false_negatives': 0,
                'total_extracted': 0,
                'total_groundtruth': 0,
                'page_count': 0
            }

        total_tp = sum(m['true_positives'] for m in metrics_list)
        total_fp = sum(m['false_positives'] for m in metrics_list)
        total_fn = sum(m['false_negatives'] for m in metrics_list)
        total_extracted = sum(m['extracted_count'] for m in metrics_list)
        total_groundtruth = sum(m['groundtruth_count'] for m in metrics_list)

        # Micro-averaged metrics
        precision = total_tp / total_extracted if total_extracted > 0 else 0.0
        recall = total_tp / total_groundtruth if total_groundtruth > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'total_true_positives': total_tp,
            'total_false_positives': total_fp,
            'total_false_negatives': total_fn,
            'total_extracted': total_extracted,
            'total_groundtruth': total_groundtruth,
            'page_count': len(metrics_list)
        }

    @staticmethod
    def compute_attribute_level_metrics(page_results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """
        Compute per-attribute metrics across all pages.

        Args:
            page_results: List of page-level results

        Returns:
            Dictionary mapping attribute names to their metrics
        """
        attribute_metrics = defaultdict(list)

        for page_result in page_results:
            for attr, metrics in page_result.get('field_metrics', {}).items():
                attribute_metrics[attr].append(metrics)

        # Aggregate per attribute
        aggregated = {}
        for attr, metrics_list in attribute_metrics.items():
            aggregated[attr] = ExtractionMetrics.aggregate_metrics(metrics_list)

        return aggregated
