"""
REST API extractor for ServiceNow instances
"""
import requests
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta
import getpass
import urllib.parse


class RestAPIExtractor:
    """Extracts data from ServiceNow using REST API"""

    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize the REST API extractor

        Args:
            base_url: Base URL of the ServiceNow instance
            username: Username for authentication (will prompt if not provided)
            password: Password for authentication (will prompt if not provided)
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()

        # Prompt for credentials if not provided
        if not self.username:
            self.username = input("Enter ServiceNow username: ")
        if not self.password:
            self.password = getpass.getpass("Enter ServiceNow password: ")

        # Set up authentication
        self.session.auth = (self.username, self.password)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def test_connection(self) -> bool:
        """
        Test the API connection

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/now/table/incident"
            params = {
                'sysparm_limit': 1,
                'sysparm_display_value': 'true'
            }
            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                print("API connection successful!")
                return True
            else:
                print(f"API connection failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"API connection error: {e}")
            return False

    def extract_data(self, table: str, query: str, limit: int = 10000) -> List[Dict]:
        """
        Extract data from a ServiceNow table using REST API

        Args:
            table: Table name (incident, sc_task, etc.)
            query: Query string
            limit: Maximum number of records to retrieve

        Returns:
            List of records as dictionaries
        """
        all_records = []
        offset = 0
        batch_size = 1000  # Fetch in batches

        print(f"  Extracting data from {table} table...")

        while True:
            try:
                url = f"{self.base_url}/api/now/table/{table}"
                params = {
                    'sysparm_query': query,
                    'sysparm_limit': batch_size,
                    'sysparm_offset': offset,
                    'sysparm_display_value': 'true'
                }

                response = self.session.get(url, params=params, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    records = data.get('result', [])

                    if not records:
                        # No more records
                        break

                    all_records.extend(records)
                    print(f"    Retrieved {len(all_records)} records so far...")

                    # Check if we've reached the limit or got fewer records than batch size
                    if len(records) < batch_size or len(all_records) >= limit:
                        break

                    offset += batch_size

                else:
                    print(f"  Error: {response.status_code} - {response.text}")
                    break

            except Exception as e:
                print(f"  Error extracting data: {e}")
                break

        print(f"  Total records extracted: {len(all_records)}")
        return all_records

    def extract_incidents_current_month(self, assignment_groups: List[str]) -> pd.DataFrame:
        """
        Extract incidents opened this month

        Args:
            assignment_groups: List of assignment groups

        Returns:
            DataFrame with incident records
        """
        print("\nExtracting incidents opened this month...")

        # Get current month start
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start_str = month_start.strftime('%Y-%m-%d %H:%M:%S')

        # Build query
        groups_query = ','.join(assignment_groups)
        query = f"assignment_groupIN{groups_query}^opened_at>={month_start_str}"

        # Extract data
        records = self.extract_data('incident', query)

        if records:
            df = pd.DataFrame(records)
            return df
        else:
            return pd.DataFrame()

    def extract_incidents_closed_current_month(self, assignment_groups: List[str]) -> pd.DataFrame:
        """
        Extract incidents closed this month

        Args:
            assignment_groups: List of assignment groups

        Returns:
            DataFrame with incident records
        """
        print("\nExtracting incidents closed this month...")

        # Get current month start
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_start_str = month_start.strftime('%Y-%m-%d %H:%M:%S')

        # Build query
        groups_query = ','.join(assignment_groups)
        query = f"assignment_groupIN{groups_query}^closed_at>={month_start_str}"

        # Extract data
        records = self.extract_data('incident', query)

        if records:
            df = pd.DataFrame(records)
            return df
        else:
            return pd.DataFrame()

    def extract_incidents_active(self, assignment_groups: List[str]) -> pd.DataFrame:
        """
        Extract active incidents

        Args:
            assignment_groups: List of assignment groups

        Returns:
            DataFrame with incident records
        """
        print("\nExtracting active incidents...")

        # Build query
        groups_query = ','.join(assignment_groups)
        query = f"assignment_groupIN{groups_query}^active=true"

        # Extract data
        records = self.extract_data('incident', query)

        if records:
            df = pd.DataFrame(records)
            return df
        else:
            return pd.DataFrame()

    def extract_all_instance3_data(self, assignment_groups: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Extract all required data for Instance 3

        Args:
            assignment_groups: List of assignment groups

        Returns:
            Dictionary with DataFrames for each category
        """
        datasets = {}

        # Extract opened this month
        df_opened = self.extract_incidents_current_month(assignment_groups)
        if not df_opened.empty:
            datasets['incidents_opened_current_month'] = df_opened

        # Extract closed this month
        df_closed = self.extract_incidents_closed_current_month(assignment_groups)
        if not df_closed.empty:
            datasets['incidents_closed_current_month'] = df_closed

        # Extract active
        df_active = self.extract_incidents_active(assignment_groups)
        if not df_active.empty:
            datasets['incidents_active'] = df_active

        return datasets

    def extract_with_query(self, table: str, assignment_groups: List[str],
                           custom_query: Optional[str] = None) -> pd.DataFrame:
        """
        Extract data with custom query

        Args:
            table: Table name
            assignment_groups: List of assignment groups
            custom_query: Additional query parameters

        Returns:
            DataFrame with records
        """
        groups_query = ','.join(assignment_groups)
        query = f"assignment_groupIN{groups_query}"

        if custom_query:
            query += f"^{custom_query}"

        records = self.extract_data(table, query)

        if records:
            return pd.DataFrame(records)
        else:
            return pd.DataFrame()
