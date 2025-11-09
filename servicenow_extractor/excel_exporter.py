"""
Excel exporter for ServiceNow data
"""
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Optional


class ExcelExporter:
    """Exports ServiceNow data to Excel files"""

    def __init__(self, output_folder: str):
        """
        Initialize the exporter

        Args:
            output_folder: Base folder for output files
        """
        self.output_folder = output_folder
        os.makedirs(self.output_folder, exist_ok=True)

    def generate_filename(self, ticket_type: str, timestamp: Optional[datetime] = None) -> str:
        """
        Generate filename for export

        Args:
            ticket_type: Type of ticket (incident, sc_task, etc.)
            timestamp: Timestamp to include in filename

        Returns:
            Generated filename
        """
        if timestamp is None:
            timestamp = datetime.now()

        date_str = timestamp.strftime('%Y%m%d_%H%M%S')
        filename = f"{ticket_type}_{date_str}.xlsx"
        return os.path.join(self.output_folder, filename)

    def export_to_excel(self, df: pd.DataFrame, ticket_type: str,
                        timestamp: Optional[datetime] = None,
                        include_metadata: bool = True) -> str:
        """
        Export DataFrame to Excel file

        Args:
            df: DataFrame to export
            ticket_type: Type of ticket
            timestamp: Timestamp for filename
            include_metadata: Include metadata sheet

        Returns:
            Path to exported file
        """
        if df.empty:
            print(f"  Warning: No data to export for {ticket_type}")
            return ""

        filename = self.generate_filename(ticket_type, timestamp)

        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Write main data
                df.to_excel(writer, sheet_name='Data', index=False)

                # Add metadata sheet
                if include_metadata:
                    metadata = {
                        'Field': ['Extraction Date', 'Record Count', 'Ticket Type'],
                        'Value': [
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            len(df),
                            ticket_type
                        ]
                    }
                    metadata_df = pd.DataFrame(metadata)
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)

            print(f"  Exported {len(df)} records to {filename}")
            return filename

        except Exception as e:
            print(f"  Error exporting to Excel: {e}")
            return ""

    def export_multiple_datasets(self, datasets: Dict[str, pd.DataFrame],
                                  timestamp: Optional[datetime] = None) -> Dict[str, str]:
        """
        Export multiple datasets to separate Excel files

        Args:
            datasets: Dictionary of {ticket_type: DataFrame}
            timestamp: Timestamp for filenames

        Returns:
            Dictionary of {ticket_type: filepath}
        """
        exported_files = {}

        for ticket_type, df in datasets.items():
            if not df.empty:
                filepath = self.export_to_excel(df, ticket_type, timestamp)
                if filepath:
                    exported_files[ticket_type] = filepath

        return exported_files

    def export_to_single_file(self, datasets: Dict[str, pd.DataFrame],
                              filename: Optional[str] = None,
                              timestamp: Optional[datetime] = None) -> str:
        """
        Export multiple datasets to a single Excel file with multiple sheets

        Args:
            datasets: Dictionary of {sheet_name: DataFrame}
            filename: Output filename (will be generated if not provided)
            timestamp: Timestamp for filename

        Returns:
            Path to exported file
        """
        if not datasets:
            print("  Warning: No datasets to export")
            return ""

        if filename is None:
            if timestamp is None:
                timestamp = datetime.now()
            date_str = timestamp.strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(self.output_folder, f"servicenow_data_{date_str}.xlsx")
        else:
            filename = os.path.join(self.output_folder, filename)

        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                total_records = 0

                # Write each dataset to a separate sheet
                for sheet_name, df in datasets.items():
                    if not df.empty:
                        # Truncate sheet name if too long (Excel limit is 31 chars)
                        sheet_name_truncated = sheet_name[:31]
                        df.to_excel(writer, sheet_name=sheet_name_truncated, index=False)
                        total_records += len(df)

                # Add summary sheet
                summary_data = {
                    'Sheet Name': [],
                    'Record Count': [],
                    'Columns': []
                }

                for sheet_name, df in datasets.items():
                    if not df.empty:
                        summary_data['Sheet Name'].append(sheet_name)
                        summary_data['Record Count'].append(len(df))
                        summary_data['Columns'].append(len(df.columns))

                summary_data['Sheet Name'].append('Total')
                summary_data['Record Count'].append(total_records)
                summary_data['Columns'].append('-')

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)

                # Add metadata sheet
                metadata = {
                    'Field': ['Extraction Date', 'Total Records', 'Number of Sheets'],
                    'Value': [
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        total_records,
                        len(datasets)
                    ]
                }
                metadata_df = pd.DataFrame(metadata)
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)

            print(f"  Exported {total_records} total records to {filename}")
            return filename

        except Exception as e:
            print(f"  Error exporting to Excel: {e}")
            return ""

    def append_to_existing(self, df: pd.DataFrame, existing_file: str,
                           sheet_name: str = 'Data') -> bool:
        """
        Append data to an existing Excel file

        Args:
            df: DataFrame to append
            existing_file: Path to existing Excel file
            sheet_name: Sheet name to append to

        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(existing_file):
                # Read existing data
                existing_df = pd.read_excel(existing_file, sheet_name=sheet_name)

                # Combine with new data - put new data last so it's kept during deduplication
                combined_df = pd.concat([existing_df, df], ignore_index=True)

                # Remove duplicates based on number column if present, otherwise use sys_id
                # Keep='last' ensures the most recent (newly extracted) record is retained
                if 'number' in combined_df.columns:
                    combined_df = combined_df.drop_duplicates(subset=['number'], keep='last')
                elif 'sys_id' in combined_df.columns:
                    combined_df = combined_df.drop_duplicates(subset=['sys_id'], keep='last')

                # Write back
                with pd.ExcelWriter(existing_file, engine='openpyxl', mode='w') as writer:
                    combined_df.to_excel(writer, sheet_name=sheet_name, index=False)

                print(f"  Appended {len(df)} records to {existing_file}")
                return True
            else:
                # File doesn't exist, create new
                return self.export_to_excel(df, sheet_name) != ""

        except Exception as e:
            print(f"  Error appending to Excel: {e}")
            return False
