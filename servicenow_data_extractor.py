#!/usr/bin/env python3
"""
ServiceNow Data Extractor - Main Script

This script extracts data from multiple ServiceNow instances using either
JSONv2 (with Selenium) or REST API methods.
"""
import sys
import argparse
from datetime import datetime
from selenium import webdriver

from servicenow_extractor.config import ServiceNowConfig
from servicenow_extractor.assignment_groups import AssignmentGroupReader
from servicenow_extractor.jsonv2_extractor import JSONv2Extractor
from servicenow_extractor.rest_api_extractor import RestAPIExtractor
from servicenow_extractor.excel_exporter import ExcelExporter


def extract_instance_jsonv2(instance_name: str, config: ServiceNowConfig,
                             driver: webdriver.Chrome, months_back: int = 6):
    """
    Extract data from an instance using JSONv2 method

    Args:
        instance_name: Name of the instance
        config: ServiceNow configuration
        driver: Selenium WebDriver
        months_back: Number of months to extract data for
    """
    print(f"\n{'=' * 80}")
    print(f"Processing Instance: {instance_name} (JSONv2 Method)")
    print(f"{'=' * 80}\n")

    instance = config.get_instance(instance_name)
    if not instance:
        print(f"Error: Instance {instance_name} not found in configuration")
        return

    # Read assignment groups
    try:
        ag_reader = AssignmentGroupReader(instance.assignment_groups_file)
        assignment_groups = ag_reader.read_groups()

        if not assignment_groups:
            print(f"Warning: No assignment groups found for {instance_name}")
            return

    except FileNotFoundError:
        print(f"Warning: Assignment groups file not found: {instance.assignment_groups_file}")
        print("Creating sample file...")
        ag_reader = AssignmentGroupReader(instance.assignment_groups_file)
        ag_reader.create_sample_file()
        print("Please update the file with actual assignment groups and run again.")
        return

    # Initialize extractor
    extractor = JSONv2Extractor(driver)

    # Get last extraction time
    last_extraction_time = instance.get_last_extraction_time()
    if last_extraction_time:
        print(f"Last extraction was on: {last_extraction_time}")
        print("Performing delta extraction (extracting only changes since last run)\n")

    # Initialize exporter
    exporter = ExcelExporter(instance.output_folder)

    # Extract data for each ticket type
    extraction_time = datetime.now()
    all_datasets = {}

    for ticket_type in instance.ticket_types:
        print(f"\nExtracting {ticket_type} tickets...")

        df = extractor.extract_with_chunking(
            base_url=instance.base_url,
            ticket_type=ticket_type,
            assignment_groups=assignment_groups,
            use_parent_groups=instance.use_parent_groups,
            months_back=months_back,
            last_extraction_time=last_extraction_time
        )

        if not df.empty:
            all_datasets[ticket_type] = df

    # Export data
    if all_datasets:
        print(f"\n{'-' * 80}")
        print("Exporting data to Excel...")
        print(f"{'-' * 80}\n")

        exporter.export_multiple_datasets(all_datasets, extraction_time)

        # Save extraction time
        instance.save_extraction_time(extraction_time)
        print(f"\nExtraction time saved for next delta extraction.")
    else:
        print("\nNo data extracted.")


def extract_instance_rest_api(instance_name: str, config: ServiceNowConfig):
    """
    Extract data from an instance using REST API method

    Args:
        instance_name: Name of the instance
        config: ServiceNow configuration
    """
    print(f"\n{'=' * 80}")
    print(f"Processing Instance: {instance_name} (REST API Method)")
    print(f"{'=' * 80}\n")

    instance = config.get_instance(instance_name)
    if not instance:
        print(f"Error: Instance {instance_name} not found in configuration")
        return

    # Read assignment groups
    try:
        ag_reader = AssignmentGroupReader(instance.assignment_groups_file)
        assignment_groups = ag_reader.read_groups()

        if not assignment_groups:
            print(f"Warning: No assignment groups found for {instance_name}")
            return

    except FileNotFoundError:
        print(f"Warning: Assignment groups file not found: {instance.assignment_groups_file}")
        print("Creating sample file...")
        ag_reader = AssignmentGroupReader(instance.assignment_groups_file)
        ag_reader.create_sample_file()
        print("Please update the file with actual assignment groups and run again.")
        return

    # Initialize REST API extractor
    print("Please provide credentials for REST API authentication:")
    extractor = RestAPIExtractor(instance.base_url)

    # Test connection
    if not extractor.test_connection():
        print("Failed to connect to API. Please check credentials and try again.")
        return

    # Extract data
    extraction_time = datetime.now()
    datasets = extractor.extract_all_instance3_data(assignment_groups)

    # Export data
    if datasets:
        print(f"\n{'-' * 80}")
        print("Exporting data to Excel...")
        print(f"{'-' * 80}\n")

        exporter = ExcelExporter(instance.output_folder)
        exporter.export_multiple_datasets(datasets, extraction_time)

        # Save extraction time
        instance.save_extraction_time(extraction_time)
        print(f"\nExtraction time saved.")
    else:
        print("\nNo data extracted.")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Extract data from ServiceNow instances',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--instances',
        nargs='+',
        help='Specific instances to extract (e.g., instance1 instance2)',
        default=None
    )
    parser.add_argument(
        '--months',
        type=int,
        default=6,
        help='Number of months to extract data for (default: 6)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/instances.json',
        help='Path to configuration file (default: config/instances.json)'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("ServiceNow Data Extractor")
    print("=" * 80)

    # Load configuration
    config = ServiceNowConfig(args.config)

    # Determine which instances to process
    if args.instances:
        instances_to_process = args.instances
    else:
        instances_to_process = config.get_all_instances()

    # Separate instances by extraction method
    jsonv2_instances = []
    rest_api_instances = []

    for instance_name in instances_to_process:
        instance = config.get_instance(instance_name)
        if instance:
            if instance.extraction_method == 'jsonv2':
                jsonv2_instances.append(instance_name)
            elif instance.extraction_method == 'rest_api':
                rest_api_instances.append(instance_name)

    # Process JSONv2 instances
    if jsonv2_instances:
        print(f"\n{len(jsonv2_instances)} instance(s) will use JSONv2 method (Selenium)")
        print(f"Instances: {', '.join(jsonv2_instances)}")
        print("\nA Chrome browser will open for each instance.")
        print("Please log in manually to each ServiceNow instance.")
        print("The script will wait for you to complete the login.\n")

        input("Press Enter to continue...")

        # Create a single driver for all JSONv2 instances
        driver = webdriver.Chrome()

        try:
            for instance_name in jsonv2_instances:
                instance = config.get_instance(instance_name)

                # Wait for manual login
                print(f"\n{'-' * 80}")
                print(f"Please log in to: {instance_name}")
                print(f"{'-' * 80}")

                extractor = JSONv2Extractor(driver)
                extractor.wait_for_login(instance.base_url)

                # Extract data
                extract_instance_jsonv2(instance_name, config, driver, args.months)

        finally:
            # Close browser when done
            print("\nClosing browser...")
            driver.quit()

    # Process REST API instances
    if rest_api_instances:
        print(f"\n{len(rest_api_instances)} instance(s) will use REST API method")
        print(f"Instances: {', '.join(rest_api_instances)}\n")

        for instance_name in rest_api_instances:
            extract_instance_rest_api(instance_name, config)

    print("\n" + "=" * 80)
    print("Data extraction complete!")
    print("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExtraction interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
