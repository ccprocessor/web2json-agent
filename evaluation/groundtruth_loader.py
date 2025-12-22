"""
Groundtruth Loader for SWDE Dataset

This module loads and parses groundtruth files from the SWDE dataset.
"""

import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class GroundtruthLoader:
    """Loads groundtruth data from SWDE dataset."""

    def __init__(self, groundtruth_dir: str):
        """
        Initialize the groundtruth loader.

        Args:
            groundtruth_dir: Path to the groundtruth directory
        """
        self.groundtruth_dir = Path(groundtruth_dir)
        self.data = defaultdict(lambda: defaultdict(dict))

    def load_groundtruth_file(self, filepath: Path) -> Dict[str, List[str]]:
        """
        Load a single groundtruth file.

        Args:
            filepath: Path to the groundtruth file

        Returns:
            Dictionary mapping page_id to list of attribute values
        """
        result = {}

        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if len(lines) < 3:
            return result

        # Skip first two lines (header and statistics)
        for line in lines[2:]:
            parts = line.strip().split('\t')
            if len(parts) < 2:
                continue

            page_id = parts[0]
            num_values = int(parts[1])

            if num_values == 0:
                values = []
            else:
                values = [v for v in parts[2:] if v != '<NULL>']

            result[page_id] = values

        return result

    def load_vertical(self, vertical: str) -> None:
        """
        Load all groundtruth files for a specific vertical.

        Args:
            vertical: Name of the vertical (e.g., 'book', 'movie')
        """
        vertical_dir = self.groundtruth_dir / vertical

        if not vertical_dir.exists():
            raise ValueError(f"Vertical directory not found: {vertical_dir}")

        # Find all groundtruth files for this vertical
        for gt_file in vertical_dir.glob(f"{vertical}-*.txt"):
            filename = gt_file.stem
            # Parse filename: <vertical>-<website>-<attribute>
            parts = filename.split('-')
            if len(parts) < 3:
                continue

            website = parts[1]
            attribute = '-'.join(parts[2:])  # Handle attributes with hyphens

            # Load the groundtruth data
            gt_data = self.load_groundtruth_file(gt_file)
            self.data[vertical][website][attribute] = gt_data

    def get_groundtruth(self, vertical: str, website: str, page_id: str, attribute: str) -> List[str]:
        """
        Get groundtruth values for a specific page and attribute.

        Args:
            vertical: Name of the vertical
            website: Name of the website
            page_id: Page ID (e.g., '0000')
            attribute: Attribute name

        Returns:
            List of groundtruth values
        """
        if vertical not in self.data:
            return []
        if website not in self.data[vertical]:
            return []
        if attribute not in self.data[vertical][website]:
            return []
        if page_id not in self.data[vertical][website][attribute]:
            return []

        return self.data[vertical][website][attribute][page_id]

    def get_all_page_ids(self, vertical: str, website: str) -> Set[str]:
        """
        Get all page IDs for a vertical-website combination.

        Args:
            vertical: Name of the vertical
            website: Name of the website

        Returns:
            Set of page IDs
        """
        if vertical not in self.data or website not in self.data[vertical]:
            return set()

        page_ids = set()
        for attribute_data in self.data[vertical][website].values():
            page_ids.update(attribute_data.keys())

        return page_ids

    def get_attributes(self, vertical: str, website: str) -> List[str]:
        """
        Get all attributes for a vertical-website combination.

        Args:
            vertical: Name of the vertical
            website: Name of the website

        Returns:
            List of attribute names
        """
        if vertical not in self.data or website not in self.data[vertical]:
            return []

        return list(self.data[vertical][website].keys())

    def get_statistics(self, vertical: str, website: str) -> Dict[str, int]:
        """
        Get statistics for a vertical-website combination.

        Args:
            vertical: Name of the vertical
            website: Name of the website

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_pages': len(self.get_all_page_ids(vertical, website)),
            'attributes': len(self.get_attributes(vertical, website))
        }
        return stats
