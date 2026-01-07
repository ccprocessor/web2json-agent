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
        Normalize a value for comparison (Enhanced SWDE standard).

        This function:
        1. Decodes HTML entities (&lt;, &gt;, &amp;, etc.)
        2. Converts to lowercase
        3. Keeps ONLY alphanumeric characters (letters and numbers)
        4. Removes all special characters, punctuation, and whitespace

        This enhanced approach improves matching by focusing on content only.

        Examples:
            "$32,520 – $34,520" -> "3252034520"
            "$32,520  $34,520" -> "3252034520"
            "iPhone 15 Pro" -> "iphone15pro"

        Args:
            value: Raw value string

        Returns:
            Normalized value (alphanumeric only, lowercase)
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

        # Convert to lowercase first
        text = text.lower()

        # Keep ONLY alphanumeric characters (letters and numbers)
        import re
        text = re.sub(r'[^a-z0-9]', '', text)

        return text

    @staticmethod
    def value_match(extracted: str, groundtruth: str) -> bool:
        """
        Check if extracted value matches groundtruth using flexible matching (Enhanced SWDE standard).

        Matching strategy (in order):
        1. Both empty/None/dash: If both are empty, "None", "-", or "(not found)", they match
        2. Groundtruth is None: If GT is "None" and extracted is empty/missing, they match
        3. Exact match: Normalized values are identical (alphanumeric only)
        4. Substring match: Normalized GT is contained in normalized extracted value

        This enhanced approach improves matching accuracy by:
        - Treating empty values, "None", and "-" as equivalent "no data" indicators
        - Allowing extracted values to contain additional context beyond the GT value
        - Focusing on alphanumeric content only

        Examples:
            # Empty/None matching
            GT: "None", Extracted: "(not found in JSON)" -> Match ✓
            GT: "-", Extracted: "-" -> Match ✓
            GT: "None", Extracted: "" -> Match ✓

            # Exact matching
            GT: "$32,520 – $34,520", Extracted: "$32,520  $34,520" -> Match ✓
            GT: "9780312605391", Extracted: "9780312605391" -> Match ✓

            # Substring matching
            GT: "9780312605391", Extracted: "9780312605391 ISBN: 0312605390..." -> Match ✓
            GT: "iPhone 15", Extracted: "iPhone 15 Pro Max" -> Match ✓

        Args:
            extracted: Extracted value from parser
            groundtruth: Groundtruth value from dataset

        Returns:
            True if values match, False otherwise
        """
        # Normalize both values
        norm_extracted = ExtractionMetrics.normalize_value(extracted) if extracted else ""
        norm_groundtruth = ExtractionMetrics.normalize_value(groundtruth) if groundtruth else ""

        # Rule 1: Both are empty/None/dash indicators
        # Check if both represent "no value"
        empty_indicators = ["none", "", "-", "null", "n/a", "na", "notfound"]
        is_gt_empty = (
            not groundtruth or
            norm_groundtruth in empty_indicators or
            groundtruth in [None, "(not found in JSON)", "-", "None", "N/A", "n/a"]
        )
        is_extracted_empty = (
            not extracted or
            norm_extracted in empty_indicators or
            extracted in [None, "(not found in JSON)", "-", "None", "N/A", "n/a"]
        )

        if is_gt_empty and is_extracted_empty:
            return True

        # Rule 2: Groundtruth is "None" but extracted has a value - no match
        if is_gt_empty and not is_extracted_empty:
            return False

        # Rule 3: Groundtruth has value but extracted is empty - no match
        if not is_gt_empty and is_extracted_empty:
            return False

        # Both have actual values, proceed with matching

        # Rule 4: Exact match after normalization
        if norm_extracted == norm_groundtruth:
            return True

        # Rule 5: Substring match - GT is contained in extracted value
        # This handles cases where JSON has extra context
        # e.g., GT: "9780312605391", Extracted: "9780312605391 ISBN: 0312605390..."
        if norm_groundtruth in norm_extracted:
            return True

        # No match
        return False

    @staticmethod
    def compute_field_metrics(extracted_values: List[str], groundtruth_values: List[str]) -> Dict[str, float]:
        """
        Compute metrics for a single field using flexible matching (Enhanced SWDE standard).

        Uses value_match logic for each comparison:
        - TP: Number of GT values that have at least one matching extracted value
        - FP: Number of extracted values that don't match any GT value
        - FN: Number of GT values that have no matching extracted value

        This is consistent with the value_match function which supports:
        - Empty value matching (None, -, N/A all equivalent)
        - Substring matching (GT in extracted)
        - Alphanumeric-only comparison

        Args:
            extracted_values: List of extracted values
            groundtruth_values: List of groundtruth values

        Returns:
            Dictionary with precision, recall, F1 score, and counts
        """
        # Normalize all values to filter out empty ones
        def normalize_list(values):
            """Keep all values as-is for matching."""
            return [v for v in values]

        pred_list = normalize_list(extracted_values)
        gt_list = normalize_list(groundtruth_values)

        # Special case: Both lists are empty or contain only empty indicators
        pred_all_empty = all(
            not v or
            ExtractionMetrics.normalize_value(v) in ["none", "", "null", "na", "notfound"] or
            v in [None, "(not found in JSON)", "-", "None", "N/A", "n/a"]
            for v in pred_list
        ) if pred_list else True

        gt_all_empty = all(
            not v or
            ExtractionMetrics.normalize_value(v) in ["none", "", "null", "na", "notfound"] or
            v in [None, "(not found in JSON)", "-", "None", "N/A", "n/a"]
            for v in gt_list
        ) if gt_list else True

        if pred_all_empty and gt_all_empty:
            # Both are empty - perfect match, but don't count in aggregation
            # Return 100% metrics but with 0 counts to avoid inflating aggregated stats
            return {
                'precision': 1.0,
                'recall': 1.0,
                'f1': 1.0,
                'true_positives': 0,  # Don't count empty matches in TP
                'false_positives': 0,
                'false_negatives': 0,
                'extracted_count': 0,
                'groundtruth_count': 0
            }

        # Count matches using value_match logic
        matched_gt_indices = set()  # Track which GT values have been matched
        matched_pred_indices = set()  # Track which pred values have matched something

        for i, gt_val in enumerate(gt_list):
            for j, pred_val in enumerate(pred_list):
                if ExtractionMetrics.value_match(pred_val, gt_val):
                    matched_gt_indices.add(i)
                    matched_pred_indices.add(j)

        # Calculate TP, FP, FN
        tp = len(matched_gt_indices)  # Number of GT values that were matched
        fn = len(gt_list) - tp  # Number of GT values that were not matched
        fp = len(pred_list) - len(matched_pred_indices)  # Number of pred values that matched nothing

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
            'extracted_count': len(pred_list),
            'groundtruth_count': len(gt_list)
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
