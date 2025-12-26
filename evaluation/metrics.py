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
        Normalize a value for comparison (SWDE standard).

        This function:
        1. Decodes HTML entities (&lt;, &gt;, &amp;, etc.)
        2. Removes ALL whitespace (spaces, tabs, newlines)
        3. Converts to lowercase
        4. Strips leading/trailing whitespace

        This follows the SWDE standard normalization approach.

        Args:
            value: Raw value string

        Returns:
            Normalized value
        """
        if value is None:
            return ""

        text = str(value)

        # HTML entity decoding (SWDE standard)
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'").replace('&apos;', "'")
        text = text.replace('&#150;', '\u2013')  # en dash
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&#160;', ' ')
        text = text.replace('&#039;', "'")
        text = text.replace('&#34;', '"')
        text = text.replace('&reg;', '\u00ae')  # registered symbol
        text = text.replace('&rsquo;', '\u2019')  # right single quote
        text = text.replace('&#8226;', '\u2022')  # bullet
        text = text.replace('&ndash;', '\u2013')  # en dash
        text = text.replace('&#x27;', "'")
        text = text.replace('&#40;', '(')
        text = text.replace('&#41;', ')')
        text = text.replace('&#47;','/')
        text = text.replace('&#43;','+')
        text = text.replace('&#035;','#')
        text = text.replace('&#38;', '&')
        text = text.replace('&eacute;', '\u00e9')  # e with acute
        text = text.replace('&frac12;', '\u00bd')  # 1/2
        text = text.replace('  ', ' ')

        # Remove ALL whitespace using regex (SWDE standard)
        import re
        text = re.sub(r"\s+", "", text)

        return text.strip().lower()

    @staticmethod
    def value_match(extracted: str, groundtruth: str) -> bool:
        """
        Check if extracted value matches groundtruth using exact matching (SWDE standard).

        Matching strategy:
        - Exact match: normalized values are identical

        This follows the SWDE standard evaluation approach which uses
        set-based exact matching after normalization.

        Args:
            extracted: Extracted value from parser
            groundtruth: Groundtruth value from dataset

        Returns:
            True if values match, False otherwise
        """
        if not groundtruth:
            return False

        norm_extracted = ExtractionMetrics.normalize_value(extracted)
        norm_groundtruth = ExtractionMetrics.normalize_value(groundtruth)

        if not norm_extracted or not norm_groundtruth:
            return False

        # SWDE standard: Exact match only
        return norm_extracted == norm_groundtruth

    @staticmethod
    def compute_field_metrics(extracted_values: List[str], groundtruth_values: List[str]) -> Dict[str, float]:
        """
        Compute metrics for a single field using set-based matching (SWDE standard).

        Uses set operations after normalization:
        - TP = |pred ∩ gt| (intersection)
        - FP = |pred - gt| (predicted but not in groundtruth)
        - FN = |gt - pred| (in groundtruth but not predicted)

        Args:
            extracted_values: List of extracted values
            groundtruth_values: List of groundtruth values

        Returns:
            Dictionary with precision, recall, F1 score, and counts
        """
        # Normalize all values and convert to sets
        def normalize_list(values):
            """Normalize and deduplicate values."""
            normalized = [ExtractionMetrics.normalize_value(v) for v in values]
            # Filter out empty strings and return as set
            return set(v for v in normalized if v)

        pred_set = normalize_list(extracted_values)
        gt_set = normalize_list(groundtruth_values)

        # SWDE standard: Set-based operations
        tp = len(pred_set & gt_set)  # Intersection
        fp = len(pred_set - gt_set)  # Predicted but not in GT
        fn = len(gt_set - pred_set)  # In GT but not predicted

        # Calculate metrics
        precision = (tp + 1e-12) / (tp + fp + 1e-12)
        recall = (tp + 1e-12) / (tp + fn + 1e-12)
        f1 = (2 * precision * recall) / (precision + recall + 1e-12)

        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'extracted_count': len(pred_set),
            'groundtruth_count': len(gt_set)
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
