"""
Selenium-based JSONv2 extractor for ServiceNow instances
"""
import json
import time
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .utils import get_date_ranges_monthly, build_complete_query


class JSONv2Extractor:
    """Extracts data from ServiceNow using JSONv2 and Selenium"""

    def __init__(self, driver: Optional[webdriver.Chrome] = None):
        """
        Initialize the extractor

        Args:
            driver: Selenium WebDriver instance (if already logged in)
        """
        self.driver = driver
        self.own_driver = False

        if self.driver is None:
            # Create a new driver if not provided
            self.driver = self._create_driver()
            self.own_driver = True

    def _create_driver(self) -> webdriver.Chrome:
        """Create a new Chrome WebDriver with appropriate options"""
        options = webdriver.ChromeOptions()
        # Keep browser open for manual login
        options.add_experimental_option("detach", True)
        # Disable automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        # Start maximized
        options.add_argument('--start-maximized')

        driver = webdriver.Chrome(options=options)
        return driver

    def wait_for_login(self, base_url: str, timeout: int = 300):
        """
        Navigate to ServiceNow and wait for manual login

        Args:
            base_url: Base URL of the ServiceNow instance
            timeout: Maximum time to wait for login (seconds)
        """
        print(f"\nOpening {base_url}")
        print("Please log in manually in the browser window...")
        print("The script will continue once you are logged in.\n")

        self.driver.get(base_url)

        # Wait for login - check if we're redirected away from login page
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_url = self.driver.current_url
            # Check if we're past the login page (contains service-now.com but not login)
            if 'service-now.com' in current_url and 'login' not in current_url.lower():
                print("Login detected! Proceeding with data extraction...\n")
                time.sleep(2)  # Brief pause to ensure session is stable
                return True
            time.sleep(2)

        raise TimeoutException("Login timeout - please try again")

    def extract_json_data(self, url: str, max_retries: int = 3) -> List[Dict]:
        """
        Extract JSON data from a ServiceNow JSONv2 URL

        Args:
            url: Complete JSONv2 URL
            max_retries: Maximum number of retry attempts

        Returns:
            List of records as dictionaries
        """
        for attempt in range(max_retries):
            try:
                print(f"  Fetching data from URL (attempt {attempt + 1}/{max_retries})...")

                # Navigate to the URL
                self.driver.get(url)

                # Wait for page to load
                time.sleep(3)

                # Get page source
                page_source = self.driver.page_source

                # Try to extract JSON from page
                # ServiceNow JSONv2 typically returns JSON in the page body or in a pre tag
                try:
                    # Look for JSON in pre tag
                    pre_element = self.driver.find_element(By.TAG_NAME, 'pre')
                    json_text = pre_element.text
                except:
                    # If no pre tag, get body text
                    json_text = self.driver.find_element(By.TAG_NAME, 'body').text

                # Parse JSON
                if json_text.strip():
                    data = json.loads(json_text)

                    # ServiceNow JSONv2 returns data in 'records' key
                    if isinstance(data, dict) and 'records' in data:
                        records = data['records']
                        print(f"  Retrieved {len(records)} records")
                        return records
                    elif isinstance(data, list):
                        print(f"  Retrieved {len(data)} records")
                        return data
                    else:
                        print("  Warning: Unexpected JSON structure")
                        return []
                else:
                    print("  Warning: Empty response")
                    return []

            except json.JSONDecodeError as e:
                print(f"  Error parsing JSON: {e}")
                if attempt < max_retries - 1:
                    print("  Retrying...")
                    time.sleep(5)
                else:
                    print("  Max retries reached. Skipping this query.")
                    return []

            except Exception as e:
                print(f"  Error extracting data: {e}")
                if attempt < max_retries - 1:
                    print("  Retrying...")
                    time.sleep(5)
                else:
                    print("  Max retries reached. Skipping this query.")
                    return []

        return []

    def extract_with_chunking(self,
                              base_url: str,
                              ticket_type: str,
                              assignment_groups: List[str],
                              use_parent_groups: bool = True,
                              months_back: int = 6,
                              last_extraction_time: Optional[datetime] = None) -> pd.DataFrame:
        """
        Extract data with monthly chunking to handle 10000 record limit

        Args:
            base_url: Base URL of ServiceNow instance
            ticket_type: Type of ticket (incident, sc_task, etc.)
            assignment_groups: List of assignment groups
            use_parent_groups: Use parent assignment groups
            months_back: Number of months to go back
            last_extraction_time: Last extraction time for delta extraction

        Returns:
            DataFrame with all extracted records
        """
        all_records = []

        if last_extraction_time:
            # Delta extraction - use last extraction time
            print(f"Performing delta extraction since {last_extraction_time}")
            query = build_complete_query(
                assignment_groups=assignment_groups,
                use_parent_groups=use_parent_groups,
                last_extraction_time=last_extraction_time
            )

            # Build URL based on ticket type
            if ticket_type == 'incident':
                url_template = '{base_url}/incident_list.do?JSONv2&sysparm_query={query}&displayvalue=true'
            elif ticket_type == 'sc_task':
                url_template = '{base_url}/sc_task.do?JSONv2&sysparm_query={query}&displayvalue=true'
            elif ticket_type == 'incident_task':
                url_template = '{base_url}/incident_task_list.do?JSONv2&sysparm_query={query}&displayvalue=true'
            elif ticket_type == 'problem':
                url_template = '{base_url}/problem_list.do?JSONv2&sysparm_query={query}&displayvalue=true'
            else:
                raise ValueError(f"Unknown ticket type: {ticket_type}")

            url = url_template.format(base_url=base_url, query=query)
            records = self.extract_json_data(url)
            all_records.extend(records)

        else:
            # Full extraction - chunk by month
            print(f"Extracting data for the last {months_back} months (chunked by month)...")
            date_ranges = get_date_ranges_monthly(months_back)

            for i, (start_date, end_date) in enumerate(date_ranges, 1):
                print(f"\nChunk {i}/{len(date_ranges)}: {start_date.strftime('%Y-%m')} to {end_date.strftime('%Y-%m')}")

                # Build query for this date range
                query = build_complete_query(
                    assignment_groups=assignment_groups,
                    use_parent_groups=use_parent_groups,
                    start_date=start_date,
                    end_date=end_date,
                    active_only=True  # Include active tickets
                )

                # Build URL
                if ticket_type == 'incident':
                    url_template = '{base_url}/incident_list.do?JSONv2&sysparm_query={query}&displayvalue=true'
                elif ticket_type == 'sc_task':
                    url_template = '{base_url}/sc_task.do?JSONv2&sysparm_query={query}&displayvalue=true'
                elif ticket_type == 'incident_task':
                    url_template = '{base_url}/incident_task_list.do?JSONv2&sysparm_query={query}&displayvalue=true'
                elif ticket_type == 'problem':
                    url_template = '{base_url}/problem_list.do?JSONv2&sysparm_query={query}&displayvalue=true'
                else:
                    raise ValueError(f"Unknown ticket type: {ticket_type}")

                url = url_template.format(base_url=base_url, query=query)

                # Extract data for this chunk
                records = self.extract_json_data(url)
                all_records.extend(records)

                # Brief pause between requests
                time.sleep(2)

        # Convert to DataFrame
        if all_records:
            df = pd.DataFrame(all_records)
            print(f"\nTotal records extracted: {len(df)}")
            # Remove duplicates based on number column if present, otherwise use sys_id
            if 'number' in df.columns:
                before_dedup = len(df)
                df = df.drop_duplicates(subset=['number'])
                after_dedup = len(df)
                if before_dedup != after_dedup:
                    print(f"Removed {before_dedup - after_dedup} duplicate records based on 'number' column")
            elif 'sys_id' in df.columns:
                before_dedup = len(df)
                df = df.drop_duplicates(subset=['sys_id'])
                after_dedup = len(df)
                if before_dedup != after_dedup:
                    print(f"Removed {before_dedup - after_dedup} duplicate records based on 'sys_id' column")
            return df
        else:
            print("\nNo records extracted")
            return pd.DataFrame()

    def close(self):
        """Close the browser if we created it"""
        if self.own_driver and self.driver:
            self.driver.quit()
