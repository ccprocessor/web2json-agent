"""
Visualization and Reporting for SWDE Evaluation

This module generates visual reports and detailed logs of evaluation results.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend


class EvaluationReporter:
    """Generates evaluation reports and visualizations."""

    def __init__(self, output_dir: Path):
        """
        Initialize the reporter.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_html_report(self, results: Dict[str, Any], output_file: str = "report.html") -> None:
        """
        Generate an HTML report with visualizations.

        Args:
            results: Evaluation results
            output_file: Output filename
        """
        html_path = self.output_dir / output_file
        vertical = results['vertical']
        website = results['website']

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SWDE Evaluation Report - {vertical}/{website}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .metric-box {{
            display: inline-block;
            padding: 20px;
            margin: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            min-width: 150px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .error {{ color: #e74c3c; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background-color: #ecf0f1;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #3498db 0%, #2ecc71 100%);
            text-align: center;
            line-height: 30px;
            color: white;
            font-weight: bold;
        }}
        .chart-container {{
            margin: 20px 0;
            text-align: center;
        }}
        .detail-section {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>SWDE Evaluation Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="detail-section">
            <h3>Dataset Information</h3>
            <p><strong>Vertical:</strong> {vertical}</p>
            <p><strong>Website:</strong> {website}</p>
            <p><strong>Total Pages:</strong> {results['statistics']['total_pages']}</p>
            <p><strong>Evaluated Pages:</strong> {results['statistics']['evaluated_pages']}</p>
            <p><strong>Errors:</strong> <span class="{'error' if results['statistics']['errors'] > 0 else 'success'}">{results['statistics']['errors']}</span></p>
        </div>

        <h2>Overall Performance</h2>
        <div style="text-align: center;">
            <div class="metric-box">
                <div class="metric-value">{results['overall_metrics']['precision']:.2%}</div>
                <div class="metric-label">Precision</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{results['overall_metrics']['recall']:.2%}</div>
                <div class="metric-label">Recall</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{results['overall_metrics']['f1']:.2%}</div>
                <div class="metric-label">F1 Score</div>
            </div>
        </div>

        <h2>Per-Attribute Performance</h2>
        <table>
            <thead>
                <tr>
                    <th>Attribute</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1 Score</th>
                    <th>True Positives</th>
                    <th>False Positives</th>
                    <th>False Negatives</th>
                </tr>
            </thead>
            <tbody>
"""

        for attr, metrics in results['attribute_metrics'].items():
            html_content += f"""
                <tr>
                    <td><strong>{attr}</strong></td>
                    <td>{metrics['precision']:.2%}</td>
                    <td>{metrics['recall']:.2%}</td>
                    <td>{metrics['f1']:.2%}</td>
                    <td class="success">{metrics['total_true_positives']}</td>
                    <td class="error">{metrics['total_false_positives']}</td>
                    <td class="warning">{metrics['total_false_negatives']}</td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>

        <h2>Error Samples by Attribute</h2>
        <p>Showing up to 3 error samples per attribute (samples where extraction did not match groundtruth)</p>
"""

        # Collect error samples by attribute
        error_samples_by_attr = {}
        for page_result in results['page_results']:
            for attr, details in page_result['field_details'].items():
                # Only collect samples where match is False
                if not details['match']:
                    if attr not in error_samples_by_attr:
                        error_samples_by_attr[attr] = []

                    error_samples_by_attr[attr].append({
                        'page_id': page_result['page_id'],
                        'details': details
                    })

        # Display error samples grouped by attribute
        if error_samples_by_attr:
            for attr, error_samples in error_samples_by_attr.items():
                html_content += f"""
        <div class="detail-section">
            <h3>{attr}</h3>
            <p>Total errors: <span class="error">{len(error_samples)}</span></p>
"""
                # Show first 3 error samples for this attribute
                for sample in error_samples[:3]:
                    page_id = sample['page_id']
                    details = sample['details']

                    raw_values = details.get('raw_extracted', [])
                    matched_values = details.get('extracted', [])
                    gt_values = details.get('groundtruth', [])

                    html_content += f"""
            <div style="margin-left: 20px; margin-bottom: 15px; padding: 10px; border-left: 3px solid #e74c3c; background-color: #fff5f5;">
                <p><strong>Page ID:</strong> {page_id}</p>
                <p style="margin-left: 10px;">
                    <strong>Groundtruth:</strong> {', '.join(gt_values) if gt_values else '<em>None</em>'}<br>
                    <strong>JSON Value:</strong> {', '.join(raw_values) if raw_values else '<em>(not found in JSON)</em>'}<br>
"""

                    # Show matched values if different from raw
                    if matched_values != raw_values:
                        html_content += f"""                    <strong>Matched Values:</strong> {', '.join(matched_values) if matched_values else '<em>(no match with groundtruth)</em>'}<br>
"""

                    # Add explanation
                    if raw_values:
                        html_content += f"""                    <em style="color: #e74c3c;">⚠️ Extracted value does not match groundtruth (precision matching required)</em>
"""
                    else:
                        html_content += f"""                    <em style="color: #f39c12;">⚠️ Field not found in extracted JSON</em>
"""

                    html_content += """                </p>
            </div>
"""

                # Show hint if there are more than 3 errors
                if len(error_samples) > 3:
                    html_content += f"""
            <p style="margin-left: 20px;"><em>... and {len(error_samples) - 3} more error samples for this attribute</em></p>
"""

                html_content += """
        </div>
"""
        else:
            html_content += """
        <div class="detail-section">
            <p class="success">No errors found! All extractions match groundtruth perfectly.</p>
        </div>
"""

        if results['errors']:
            html_content += f"""
        <h2>Errors ({len(results['errors'])})</h2>
        <table>
            <thead>
                <tr>
                    <th>Page ID</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
"""
            for error in results['errors'][:20]:
                html_content += f"""
                <tr>
                    <td>{error['page_id']}</td>
                    <td class="error">{error['error']}</td>
                </tr>
"""
            html_content += """
            </tbody>
        </table>
"""

        html_content += """
    </div>
</body>
</html>
"""

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML report saved to: {html_path}")

    def generate_charts(self, results: Dict[str, Any]) -> None:
        """
        Generate visualization charts.

        Args:
            results: Evaluation results
        """
        # Extract data
        attributes = list(results['attribute_metrics'].keys())
        precisions = [results['attribute_metrics'][attr]['precision'] for attr in attributes]
        recalls = [results['attribute_metrics'][attr]['recall'] for attr in attributes]
        f1_scores = [results['attribute_metrics'][attr]['f1'] for attr in attributes]

        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f"SWDE Evaluation: {results['vertical']} - {results['website']}", fontsize=16, fontweight='bold')

        # 1. Bar chart of metrics per attribute
        ax1 = axes[0, 0]
        x = range(len(attributes))
        width = 0.25
        ax1.bar([i - width for i in x], precisions, width, label='Precision', color='#3498db')
        ax1.bar(x, recalls, width, label='Recall', color='#2ecc71')
        ax1.bar([i + width for i in x], f1_scores, width, label='F1 Score', color='#9b59b6')
        ax1.set_xlabel('Attribute')
        ax1.set_ylabel('Score')
        ax1.set_title('Metrics per Attribute')
        ax1.set_xticks(x)
        ax1.set_xticklabels(attributes, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        ax1.set_ylim([0, 1.1])

        # 2. Overall metrics pie chart
        ax2 = axes[0, 1]
        overall_data = [
            results['overall_metrics']['precision'],
            results['overall_metrics']['recall'],
            results['overall_metrics']['f1']
        ]
        colors = ['#3498db', '#2ecc71', '#9b59b6']

        # Handle edge case: all metrics are 0 (cannot draw pie chart with all zeros)
        if all(x == 0 for x in overall_data):
            ax2.text(0.5, 0.5, 'No Data\n(All metrics are 0)',
                    ha='center', va='center', fontsize=14, color='red',
                    transform=ax2.transAxes)
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)
            ax2.axis('off')
        else:
            ax2.pie(overall_data, labels=['Precision', 'Recall', 'F1'], autopct='%1.1f%%',
                    colors=colors, startangle=90)
        ax2.set_title('Overall Performance')

        # 3. True Positives vs False Positives/Negatives
        ax3 = axes[1, 0]
        tp = [results['attribute_metrics'][attr]['total_true_positives'] for attr in attributes]
        fp = [results['attribute_metrics'][attr]['total_false_positives'] for attr in attributes]
        fn = [results['attribute_metrics'][attr]['total_false_negatives'] for attr in attributes]

        x = range(len(attributes))
        ax3.bar(x, tp, label='True Positives', color='#2ecc71', alpha=0.8)
        ax3.bar(x, fp, bottom=tp, label='False Positives', color='#e74c3c', alpha=0.8)
        ax3.bar(x, fn, bottom=[tp[i] + fp[i] for i in range(len(tp))],
                label='False Negatives', color='#f39c12', alpha=0.8)
        ax3.set_xlabel('Attribute')
        ax3.set_ylabel('Count')
        ax3.set_title('Extraction Statistics')
        ax3.set_xticks(x)
        ax3.set_xticklabels(attributes, rotation=45, ha='right')
        ax3.legend()
        ax3.grid(axis='y', alpha=0.3)

        # 4. F1 Score comparison
        ax4 = axes[1, 1]
        colors_f1 = ['#2ecc71' if f1 >= 0.7 else '#f39c12' if f1 >= 0.4 else '#e74c3c' for f1 in f1_scores]
        ax4.barh(attributes, f1_scores, color=colors_f1, alpha=0.8)
        ax4.set_xlabel('F1 Score')
        ax4.set_title('F1 Score by Attribute')
        ax4.set_xlim([0, 1])
        ax4.grid(axis='x', alpha=0.3)

        plt.tight_layout()
        chart_path = self.output_dir / 'evaluation_charts.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Charts saved to: {chart_path}")

    def save_json_report(self, results: Dict[str, Any], output_file: str = "results.json") -> None:
        """
        Save detailed results as JSON.

        Args:
            results: Evaluation results
            output_file: Output filename
        """
        json_path = self.output_dir / output_file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"JSON results saved to: {json_path}")

    def save_csv_summary(self, results: Dict[str, Any], output_file: str = "summary.csv") -> None:
        """
        Save summary as CSV for easy analysis.

        Args:
            results: Evaluation results
            output_file: Output filename
        """
        csv_path = self.output_dir / output_file
        with open(csv_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("Attribute,Precision,Recall,F1,TruePositives,FalsePositives,FalseNegatives,Extracted,Groundtruth\n")

            # Write per-attribute data
            for attr, metrics in results['attribute_metrics'].items():
                f.write(f"{attr},"
                       f"{metrics['precision']:.4f},"
                       f"{metrics['recall']:.4f},"
                       f"{metrics['f1']:.4f},"
                       f"{metrics['total_true_positives']},"
                       f"{metrics['total_false_positives']},"
                       f"{metrics['total_false_negatives']},"
                       f"{metrics['total_extracted']},"
                       f"{metrics['total_groundtruth']}\n")

        print(f"CSV summary saved to: {csv_path}")

    def generate_full_report(self, results: Dict[str, Any]) -> None:
        """
        Generate all report formats.

        Args:
            results: Evaluation results
        """
        print(f"\nGenerating reports for {results['vertical']}/{results['website']}...")
        self.generate_html_report(results)
        self.generate_charts(results)
        self.save_json_report(results)
        self.save_csv_summary(results)
        print("All reports generated successfully!")

    @staticmethod
    def generate_integrated_report(results_list: List[Dict[str, Any]], output_path: Path) -> None:
        """
        Generate an integrated HTML report combining error samples from all websites.

        Args:
            results_list: List of evaluation results from all websites
            output_path: Path to save the integrated report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Collect overall statistics
        total_websites = len(results_list)
        total_pages = sum(r['statistics']['evaluated_pages'] for r in results_list)
        total_errors = sum(r['statistics']['errors'] for r in results_list)

        # Calculate overall metrics
        if results_list:
            avg_precision = sum(r['overall_metrics']['precision'] for r in results_list) / len(results_list)
            avg_recall = sum(r['overall_metrics']['recall'] for r in results_list) / len(results_list)
            avg_f1 = sum(r['overall_metrics']['f1'] for r in results_list) / len(results_list)
        else:
            avg_precision = avg_recall = avg_f1 = 0.0

        # Start HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Integrated SWDE Evaluation Report - All Error Samples</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #34495e;
            margin-top: 20px;
        }}
        h4 {{
            color: #7f8c8d;
            margin-top: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .metric-box {{
            display: inline-block;
            padding: 20px;
            margin: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            min-width: 150px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .error {{ color: #e74c3c; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
        .detail-section {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
        }}
        .website-section {{
            margin: 30px 0;
            padding: 20px;
            background-color: #ecf0f1;
            border-left: 5px solid #2c3e50;
        }}
        .error-sample {{
            margin-left: 20px;
            margin-bottom: 15px;
            padding: 10px;
            border-left: 3px solid #e74c3c;
            background-color: #fff5f5;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Integrated SWDE Evaluation Report</h1>
        <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="detail-section">
            <h3>Overall Statistics</h3>
            <p><strong>Total Websites:</strong> {total_websites}</p>
            <p><strong>Total Pages Evaluated:</strong> {total_pages}</p>
            <p><strong>Total Errors:</strong> <span class="{'error' if total_errors > 0 else 'success'}">{total_errors}</span></p>
        </div>

        <h2>Overall Performance</h2>
        <div style="text-align: center;">
            <div class="metric-box">
                <div class="metric-value">{avg_precision:.2%}</div>
                <div class="metric-label">Average Precision</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{avg_recall:.2%}</div>
                <div class="metric-label">Average Recall</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{avg_f1:.2%}</div>
                <div class="metric-label">Average F1 Score</div>
            </div>
        </div>

        <h2>Error Samples by Website and Attribute</h2>
        <p>Showing up to 3 error samples per attribute for each website</p>
"""

        # Process each website's results
        for results in results_list:
            vertical = results['vertical']
            website = results['website']

            html_content += f"""
        <div class="website-section">
            <h3>{vertical}/{website}</h3>
            <p><strong>Precision:</strong> {results['overall_metrics']['precision']:.2%} |
               <strong>Recall:</strong> {results['overall_metrics']['recall']:.2%} |
               <strong>F1:</strong> {results['overall_metrics']['f1']:.2%}</p>
            <p><strong>Evaluated Pages:</strong> {results['statistics']['evaluated_pages']}</p>
"""

            # Collect error samples by attribute for this website
            error_samples_by_attr = {}
            for page_result in results['page_results']:
                for attr, details in page_result['field_details'].items():
                    if not details['match']:
                        if attr not in error_samples_by_attr:
                            error_samples_by_attr[attr] = []

                        error_samples_by_attr[attr].append({
                            'page_id': page_result['page_id'],
                            'details': details
                        })

            # Display error samples by attribute
            if error_samples_by_attr:
                for attr, error_samples in error_samples_by_attr.items():
                    # Get attribute metrics if available
                    attr_metrics = results['attribute_metrics'].get(attr, {})
                    attr_f1 = attr_metrics.get('f1', 0.0)

                    html_content += f"""
            <h4>{attr} <span class="{'error' if attr_f1 < 0.5 else 'warning' if attr_f1 < 0.8 else 'success'}">(F1: {attr_f1:.2%})</span></h4>
            <p>Total errors: <span class="error">{len(error_samples)}</span></p>
"""

                    # Show first 3 error samples
                    for sample in error_samples[:3]:
                        page_id = sample['page_id']
                        details = sample['details']

                        raw_values = details.get('raw_extracted', [])
                        matched_values = details.get('extracted', [])
                        gt_values = details.get('groundtruth', [])

                        html_content += f"""
            <div class="error-sample">
                <p><strong>Page ID:</strong> {page_id}</p>
                <p style="margin-left: 10px;">
                    <strong>Groundtruth:</strong> {', '.join(gt_values) if gt_values else '<em>None</em>'}<br>
                    <strong>JSON Value:</strong> {', '.join(raw_values) if raw_values else '<em>(not found in JSON)</em>'}<br>
"""

                        if matched_values != raw_values:
                            html_content += f"""                    <strong>Matched Values:</strong> {', '.join(matched_values) if matched_values else '<em>(no match with groundtruth)</em>'}<br>
"""

                        if raw_values:
                            html_content += f"""                    <em style="color: #e74c3c;">⚠️ Extracted value does not match groundtruth</em>
"""
                        else:
                            html_content += f"""                    <em style="color: #f39c12;">⚠️ Field not found in extracted JSON</em>
"""

                        html_content += """                </p>
            </div>
"""

                    if len(error_samples) > 3:
                        html_content += f"""
            <p style="margin-left: 20px;"><em>... and {len(error_samples) - 3} more error samples for this attribute</em></p>
"""
            else:
                html_content += """
            <p class="success">✓ No errors for this website - all extractions match groundtruth!</p>
"""

            html_content += """
        </div>
"""

        # Add website performance summary table
        html_content += """
        <h2>Website Performance Summary</h2>
        <table>
            <thead>
                <tr>
                    <th>Vertical/Website</th>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1 Score</th>
                    <th>Pages</th>
                    <th>Errors</th>
                </tr>
            </thead>
            <tbody>
"""

        for results in results_list:
            html_content += f"""
                <tr>
                    <td><strong>{results['vertical']}/{results['website']}</strong></td>
                    <td>{results['overall_metrics']['precision']:.2%}</td>
                    <td>{results['overall_metrics']['recall']:.2%}</td>
                    <td>{results['overall_metrics']['f1']:.2%}</td>
                    <td>{results['statistics']['evaluated_pages']}</td>
                    <td class="{'error' if results['statistics']['errors'] > 0 else 'success'}">{results['statistics']['errors']}</td>
                </tr>
"""

        html_content += """
            </tbody>
        </table>

    </div>
</body>
</html>
"""

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ Integrated error report saved to: {output_path}")
