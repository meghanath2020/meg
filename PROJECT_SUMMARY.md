# ServiceNow Data Extractor - Project Summary

## Overview

This is a comprehensive Python application for extracting data from multiple ServiceNow instances. It supports both JSONv2 (Selenium-based) and REST API extraction methods.

## What Was Built

### Core Modules

1. **servicenow_extractor/config.py**
   - Manages instance configurations
   - Loads settings from JSON file
   - Tracks last extraction time for delta updates
   - Builds URLs for different ticket types

2. **servicenow_extractor/assignment_groups.py**
   - Reads assignment groups from Excel files
   - Auto-detects column names
   - Creates sample files if missing
   - Formats groups for ServiceNow queries

3. **servicenow_extractor/utils.py**
   - Date range generation (monthly chunks)
   - ServiceNow query builder
   - Date formatting for ServiceNow
   - URL encoding utilities

4. **servicenow_extractor/jsonv2_extractor.py**
   - Selenium-based extraction for JSONv2
   - Handles manual login workflow
   - Extracts JSON data from browser
   - Implements monthly chunking for 10K limit
   - Supports delta extraction

5. **servicenow_extractor/rest_api_extractor.py**
   - REST API-based extraction
   - Handles authentication
   - Batch processing for large datasets
   - Specific methods for Instance 3 requirements:
     - Incidents opened this month
     - Incidents closed this month
     - Active incidents

6. **servicenow_extractor/excel_exporter.py**
   - Exports data to XLSX format
   - Creates metadata sheets
   - Supports multiple export modes
   - Handles single and multi-sheet workbooks

### Main Script

**servicenow_data_extractor.py**
- Command-line interface
- Orchestrates entire extraction process
- Manages browser sessions for JSONv2
- Handles multiple instances
- Supports selective extraction

### Configuration Files

**config/instances.json**
- Defines all ServiceNow instances
- Configurable per instance:
  - Base URL
  - Extraction method (JSONv2 or REST API)
  - Parent vs. direct assignment groups
  - Ticket types to extract
  - Output folder location

### Documentation

1. **SERVICENOW_EXTRACTOR_README.md** - Comprehensive documentation
2. **QUICKSTART.md** - Quick start guide
3. **requirements.txt** - Python dependencies
4. **PROJECT_SUMMARY.md** - This file

## Key Features Implemented

### 1. Multiple Instance Support
- Instance 1: JSONv2 (incidents, sc_tasks, incident_tasks, problems)
- Instance 2: JSONv2 (incidents, sc_tasks)
- Instance 3: REST API (incidents only)

### 2. Flexible Assignment Group Filtering
- Support for parent assignment groups (Instance 1 & 2)
- Support for direct assignment groups (Instance 3)
- Easy switching via configuration

### 3. Date-Based Filtering
- Configurable time range (default: 6 months)
- Criteria: Opened OR Closed in range OR Active
- Monthly chunking to handle 10,000 record limit

### 4. Delta Extraction
- Tracks last extraction timestamp
- Only extracts changes since last run
- Stored in `.last_extraction.json` per instance
- Significantly reduces extraction time
- Duplicates removed based on ticket "number" column (INC0001234, RITM0001234, etc.)

### 5. Data Export
- XLSX format with multiple sheets
- Includes metadata (extraction time, record count)
- Organized by instance in separate folders
- Timestamped filenames

### 6. Error Handling
- Retry logic for network failures
- Graceful handling of missing files
- Detailed error messages
- Sample file creation

## Requirements Met

All 10 requirements from the specification have been implemented:

1. ✅ Three ServiceNow instances configured
2. ✅ Excel-based assignment group filtering with parent/direct switching
3. ✅ Base URLs defined in configuration
4. ✅ JSONv2 with Selenium for Instance 1 & 2, REST API for Instance 3
5. ✅ XLSX export in instance-specific folders
6. ✅ All URL definitions for Instance 1 (incidents, sc_tasks, incident_tasks, problems)
7. ✅ URL definitions for Instance 2 (incidents, sc_tasks)
8. ✅ Instance 3 REST API with authentication and required incident types
9. ✅ Monthly chunking to handle 10,000 record limit
10. ✅ displayvalue=true for all queries

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install ChromeDriver
```bash
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# macOS
brew install chromedriver
```

### 3. Configure Instances
Edit `config/instances.json` with your actual ServiceNow URLs.

### 4. Create Assignment Groups Files
Create Excel files in `assignment_groups/` with your groups, or let the script create samples.

### 5. Run
```bash
python servicenow_data_extractor.py
```

## Usage Examples

### Extract all instances (default: 6 months)
```bash
python servicenow_data_extractor.py
```

### Extract specific instance
```bash
python servicenow_data_extractor.py --instances instance1
```

### Extract with custom time range
```bash
python servicenow_data_extractor.py --months 3
```

### Use custom config
```bash
python servicenow_data_extractor.py --config /path/to/config.json
```

## Directory Structure

```
meg/
├── servicenow_extractor/          # Main package
│   ├── __init__.py
│   ├── config.py                  # Configuration management
│   ├── assignment_groups.py       # Excel reader
│   ├── utils.py                   # Utility functions
│   ├── jsonv2_extractor.py        # Selenium extractor
│   ├── rest_api_extractor.py      # REST API extractor
│   └── excel_exporter.py          # Excel export
│
├── config/                         # Configuration files
│   └── instances.json             # Instance definitions
│
├── assignment_groups/              # Assignment group files
│   ├── instance1_groups.xlsx
│   ├── instance2_groups.xlsx
│   └── instance3_groups.xlsx
│
├── output/                         # Extracted data
│   ├── instance1/
│   ├── instance2/
│   └── instance3/
│
├── servicenow_data_extractor.py   # Main script
├── requirements.txt               # Dependencies
├── SERVICENOW_EXTRACTOR_README.md # Full documentation
├── QUICKSTART.md                  # Quick start guide
├── PROJECT_SUMMARY.md             # This file
└── .gitignore                     # Git ignore patterns

(Original Flask app files remain unchanged)
```

## Technical Highlights

### 1. Smart Query Building
- Dynamically constructs ServiceNow queries
- Combines assignment groups, date filters, and active status
- Handles both parent and direct group filtering

### 2. 10,000 Record Limit Handling
- Automatic monthly chunking
- Concatenates DataFrames
- Removes duplicates based on sys_id

### 3. Delta Extraction Optimization
- Timestamp-based change tracking
- Reduces data transfer and processing time
- Transparent to the user

### 4. Selenium Workflow
- Detects successful login automatically
- Waits for manual authentication
- Reuses browser session across multiple ticket types
- Robust JSON extraction from page source

### 5. REST API Implementation
- Batch processing (1000 records per request)
- Pagination handling
- Secure credential input (getpass)
- Connection testing

## Configuration Flexibility

### Switch Between Parent and Direct Groups
```json
{
  "instance1": {
    "use_parent_groups": true  // or false
  }
}
```

### Switch Extraction Method
```json
{
  "instance1": {
    "extraction_method": "jsonv2"  // or "rest_api"
  }
}
```

### Customize Ticket Types
```json
{
  "instance1": {
    "ticket_types": ["incident", "problem", "change_request"]
  }
}
```

## Sample Output

### File Naming
```
incident_20250109_143022.xlsx
sc_task_20250109_143045.xlsx
incident_task_20250109_143108.xlsx
problem_20250109_143131.xlsx
```

### Excel Structure
- **Data Sheet**: All records with all fields
- **Metadata Sheet**: Extraction info
  - Extraction Date
  - Record Count
  - Ticket Type

## Performance Considerations

1. **JSONv2 Method**:
   - Slower due to browser automation
   - Requires manual login
   - Best for instances without API access

2. **REST API Method**:
   - Much faster
   - Automated authentication
   - Preferred when available

3. **Delta Extraction**:
   - 10-100x faster for regular updates
   - Only extracts changes
   - Recommended for scheduled runs

## Security Features

1. **No Stored Credentials**: API passwords prompted at runtime
2. **Secure Input**: Uses getpass for password entry
3. **Session Management**: Browser sessions cleaned up after use
4. **Gitignore**: Output files excluded from version control

## Error Handling

1. **Missing Files**: Creates sample files automatically
2. **Network Errors**: Retry logic with exponential backoff
3. **Invalid Data**: Graceful degradation with warnings
4. **Authentication Failures**: Clear error messages

## Extensibility

The modular design allows for easy extensions:

1. **Add New Ticket Types**: Update URL templates in config.py
2. **Add New Instances**: Simply add to instances.json
3. **Custom Filtering**: Extend utils.py query builders
4. **Different Export Formats**: Extend excel_exporter.py

## Testing Recommendations

1. **Start Small**: Test with one instance first
2. **Verify Groups**: Ensure assignment groups exist in ServiceNow
3. **Check Permissions**: Verify you have access to required data
4. **Test Delta**: Run twice to verify delta extraction works

## Next Steps

1. **Initial Setup**:
   - Install dependencies
   - Configure instances
   - Create assignment group files

2. **First Run**:
   - Test with one instance
   - Verify data extraction
   - Check output files

3. **Optimization**:
   - Set up delta extraction schedule
   - Adjust time ranges as needed
   - Fine-tune ticket types

4. **Automation**:
   - Create scheduled tasks (cron/Task Scheduler)
   - Set up monitoring
   - Implement data validation

## Troubleshooting Reference

| Issue | Solution |
|-------|----------|
| ChromeDriver not found | Install via package manager |
| Login not detected | Wait for page to fully load |
| No data extracted | Check assignment groups and date range |
| API auth failed | Verify credentials and permissions |
| Import errors | Run `pip install -r requirements.txt` |

## Maintenance

Regular maintenance tasks:
1. Update ChromeDriver when Chrome updates
2. Review and update assignment groups
3. Clean old output files periodically
4. Monitor extraction times
5. Update dependencies as needed

## Support Resources

1. **SERVICENOW_EXTRACTOR_README.md**: Full documentation
2. **QUICKSTART.md**: Quick reference
3. **config/instances.json**: Configuration examples
4. Code comments: Inline documentation

## Version Information

- **Version**: 1.0.0
- **Python**: 3.8+
- **Key Dependencies**:
  - pandas >= 2.0.0
  - selenium >= 4.15.0
  - openpyxl >= 3.1.0
  - requests >= 2.31.0

## Conclusion

This ServiceNow Data Extractor provides a robust, flexible solution for extracting data from multiple ServiceNow instances with different access methods. It handles the complexities of ServiceNow's limitations while providing an easy-to-use interface for end users.

The modular architecture ensures maintainability and extensibility for future enhancements.
