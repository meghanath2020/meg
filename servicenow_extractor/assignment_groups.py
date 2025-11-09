"""
Module for reading assignment groups from Excel files
"""
import pandas as pd
import os
from typing import List


class AssignmentGroupReader:
    """Reads assignment groups from Excel files"""

    def __init__(self, file_path: str, column_name: str = 'assignment_group'):
        """
        Initialize the reader

        Args:
            file_path: Path to the Excel file
            column_name: Name of the column containing assignment groups
        """
        self.file_path = file_path
        self.column_name = column_name
        self.groups = []

    def read_groups(self) -> List[str]:
        """
        Read assignment groups from Excel file

        Returns:
            List of assignment group names
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Assignment groups file not found: {self.file_path}")

        try:
            # Read Excel file
            df = pd.read_excel(self.file_path)

            # Check if column exists
            if self.column_name not in df.columns:
                # Try to find a similar column
                possible_columns = [col for col in df.columns if 'group' in col.lower()]
                if possible_columns:
                    print(f"Column '{self.column_name}' not found. Using '{possible_columns[0]}' instead.")
                    self.column_name = possible_columns[0]
                else:
                    # Use the first column
                    print(f"Column '{self.column_name}' not found. Using first column: '{df.columns[0]}'")
                    self.column_name = df.columns[0]

            # Extract groups and remove NaN values
            self.groups = df[self.column_name].dropna().astype(str).tolist()

            # Remove empty strings and duplicates
            self.groups = list(set([g.strip() for g in self.groups if g.strip()]))

            print(f"Read {len(self.groups)} assignment groups from {self.file_path}")
            return self.groups

        except Exception as e:
            raise Exception(f"Error reading assignment groups from {self.file_path}: {str(e)}")

    def get_groups_as_query_string(self) -> str:
        """
        Get assignment groups as a comma-separated string for queries

        Returns:
            Comma-separated string of assignment groups
        """
        if not self.groups:
            self.read_groups()

        # Join groups with commas for ServiceNow query
        return ','.join(self.groups)

    def create_sample_file(self):
        """Create a sample Excel file with assignment groups"""
        sample_data = {
            'assignment_group': [
                'IT Support',
                'Network Team',
                'Database Team',
                'Application Support',
                'Infrastructure Team'
            ]
        }

        df = pd.DataFrame(sample_data)
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        df.to_excel(self.file_path, index=False)
        print(f"Sample assignment groups file created at {self.file_path}")
