"""
Schema Generator from Groundtruth

This module generates predefined schema templates from SWDE groundtruth data.
"""

from pathlib import Path
from typing import Dict, List
import json
from .groundtruth_loader import GroundtruthLoader


class SchemaGenerator:
    """Generates schema templates from groundtruth data."""

    def __init__(self, groundtruth_dir: str):
        """
        Initialize the schema generator.

        Args:
            groundtruth_dir: Path to groundtruth directory
        """
        self.gt_loader = GroundtruthLoader(groundtruth_dir)

    def generate_schema_for_website(
        self,
        vertical: str,
        website: str,
        sample_count: int = 5
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate a schema template for a specific website based on groundtruth.

        Args:
            vertical: Vertical name (e.g., 'book', 'auto')
            website: Website name (e.g., 'amazon', 'autoweb')
            sample_count: Number of samples to analyze to determine list vs single value

        Returns:
            Schema template dictionary with field names and types
            Format: {
                field_name: {
                    "type": "string"|"list",
                    "description": "...",
                    "value_sample": [],
                    "xpath": ""
                }
            }
        """
        # Load groundtruth for this vertical
        self.gt_loader.load_vertical(vertical)

        # Get all attributes for this website
        attributes = self.gt_loader.get_attributes(vertical, website)
        if not attributes:
            raise ValueError(f"No attributes found for {vertical}/{website}")

        # Get page IDs to sample
        page_ids = sorted(self.gt_loader.get_all_page_ids(vertical, website))
        if not page_ids:
            raise ValueError(f"No pages found for {vertical}/{website}")

        # Use first N pages for sampling
        sample_page_ids = page_ids[:min(sample_count, len(page_ids))]

        schema = {}
        for attribute in attributes:
            # Analyze groundtruth values to determine type
            value_counts = []

            for page_id in sample_page_ids:
                gt_values = self.gt_loader.get_groundtruth(vertical, website, page_id, attribute)
                value_counts.append(len(gt_values))

            # Determine if this is typically a list or single value
            # If most pages have 0 or 1 values, treat as single value
            # If most pages have multiple values, treat as list
            avg_count = sum(value_counts) / len(value_counts) if value_counts else 0
            max_count = max(value_counts) if value_counts else 0

            if max_count > 1 and avg_count > 1.2:
                field_type = "list"
            else:
                field_type = "string"

            # Generate description based on field type
            if field_type == "list":
                description = f"List of {attribute} values (typically {int(avg_count)} items)"
            else:
                description = f"Single {attribute} value"

            schema[attribute] = {
                "type": field_type,
                "description": description,
                "value_sample": [],  # Empty
                "xpath": ""  # Empty
            }

        return schema

    def save_schema_template(
        self,
        schema: Dict[str, Dict[str, str]],
        output_path: Path
    ) -> None:
        """
        Save schema template to a JSON file.

        Args:
            schema: Schema template dictionary
            output_path: Path to output file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

    def generate_all_schemas(
        self,
        verticals: Dict[str, List[str]],
        output_dir: Path,
        sample_count: int = 5
    ) -> Dict[str, Dict[str, Path]]:
        """
        Generate schema templates for all verticals and websites.

        Args:
            verticals: Dictionary mapping vertical names to website lists
            output_dir: Output directory for schema files
            sample_count: Number of samples to analyze per website

        Returns:
            Dictionary mapping vertical-website to schema file path
        """
        schema_paths = {}

        for vertical, websites in verticals.items():
            schema_paths[vertical] = {}

            for website in websites:
                try:
                    # Generate schema
                    schema = self.generate_schema_for_website(vertical, website, sample_count)

                    # Save to file
                    schema_file = output_dir / vertical / f"{website}_schema.json"
                    self.save_schema_template(schema, schema_file)

                    schema_paths[vertical][website] = schema_file
                    print(f"✓ Generated schema for {vertical}/{website}: {schema_file}")

                except ValueError as e:
                    # Skip websites without groundtruth data (not an error)
                    print(f"⊘ Skipped {vertical}/{website}: {e}")

                except Exception as e:
                    print(f"✗ Failed to generate schema for {vertical}/{website}: {e}")

        return schema_paths
