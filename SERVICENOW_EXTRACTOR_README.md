# ServiceNow Data Extractor

A comprehensive Python application for extracting data from multiple ServiceNow instances using either JSONv2 (with Selenium) or REST API methods.

## Features

- Extract data from multiple ServiceNow instances simultaneously
- Support for both JSONv2 (Selenium-based) and REST API methods
- Filter tickets by assignment groups (parent groups or direct groups)
- Date-based filtering with configurable time ranges
- Delta extraction - only extract changes since last run
- Automatic chunking to handle ServiceNow's 10,000 record limit
- Export data to Excel (XLSX) format with metadata
- Configurable via JSON configuration file
- Support for multiple ticket types:
  - Incidents
  - Service Catalog Tasks (sc_task)
  - Incident Tasks
  - Problems

## Architecture

```
servicenow_extractor/
├── config.py                 # Configuration management
├── assignment_groups.py      # Excel reader for assignment groups
├── jsonv2_extractor.py      # Selenium-based JSONv2 extractor
├── rest_api_extractor.py    # REST API extractor
├── excel_exporter.py        # XLSX export functionality
└── utils.py                 # Utility functions

servicenow_data_extractor.py # Main orchestration script

config/
└── instances.json           # Instance configuration

assignment_groups/
├── instance1_groups.xlsx    # Assignment groups for instance 1
├── instance2_groups.xlsx    # Assignment groups for instance 2
└── instance3_groups.xlsx    # Assignment groups for instance 3

output/
├── instance1/               # Output folder for instance 1
├── instance2/               # Output folder for instance 2
└── instance3/               # Output folder for instance 3
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Google Chrome browser
- ChromeDriver (for Selenium)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install ChromeDriver

**Option 1: Using package manager (recommended)**
```bash
# On Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# On macOS
brew install chromedriver
```

**Option 2: Manual installation**
1. Download ChromeDriver from https://chromedriver.chromium.org/
2. Extract and place in your PATH
3. Ensure version matches your Chrome browser version

## Configuration

### 1. Create Configuration File

The application will automatically create a default configuration file at `config/instances.json` on first run. Edit this file to match your ServiceNow instances:

```json
{
  "instance1": {
    "base_url": "https://your-instance1.service-now.com",
    "extraction_method": "jsonv2",
    "use_parent_groups": true,
    "assignment_groups_file": "assignment_groups/instance1_groups.xlsx",
    "ticket_types": ["incident", "sc_task", "incident_task", "problem"],
    "output_folder": "output/instance1"
  },
  "instance2": {
    "base_url": "https://your-instance2.service-now.com",
    "extraction_method": "jsonv2",
    "use_parent_groups": true,
    "assignment_groups_file": "assignment_groups/instance2_groups.xlsx",
    "ticket_types": ["incident", "sc_task"],
    "output_folder": "output/instance2"
  },
  "instance3": {
    "base_url": "https://your-instance3.service-now.com",
    "extraction_method": "rest_api",
    "use_parent_groups": false,
    "assignment_groups_file": "assignment_groups/instance3_groups.xlsx",
    "ticket_types": ["incident"],
    "output_folder": "output/instance3"
  }
}
```

#### Configuration Parameters:

- **base_url**: Base URL of your ServiceNow instance
- **extraction_method**: Either "jsonv2" or "rest_api"
- **use_parent_groups**:
  - `true` - Query by parent assignment groups
  - `false` - Query by direct assignment groups
- **assignment_groups_file**: Path to Excel file containing assignment groups
- **ticket_types**: List of ticket types to extract
- **output_folder**: Folder where extracted data will be saved

### 2. Create Assignment Groups Files

Create Excel files with assignment groups for each instance. The files should have a column named "assignment_group" containing the group names:

**Example: assignment_groups/instance1_groups.xlsx**

| assignment_group |
|------------------|
| IT Support       |
| Network Team     |
| Database Team    |
| App Support      |

You can also run the script once and it will create sample files for you.

## Usage

### Basic Usage

Extract data from all configured instances:

```bash
python servicenow_data_extractor.py
```

### Extract from Specific Instances

```bash
python servicenow_data_extractor.py --instances instance1 instance2
```

### Specify Time Range

Extract data for the last 3 months (default is 6 months):

```bash
python servicenow_data_extractor.py --months 3
```

### Use Custom Configuration File

```bash
python servicenow_data_extractor.py --config /path/to/custom_config.json
```

### Command Line Options

```
--instances INSTANCE1 INSTANCE2  Specific instances to extract
--months N                        Number of months to extract (default: 6)
--config FILE                     Path to configuration file
```

## How It Works

### JSONv2 Method (Instance 1 & 2)

1. **Manual Login**: A Chrome browser opens for each instance
2. **Login**: You manually log into ServiceNow
3. **Extraction**: Script detects successful login and begins extraction
4. **Chunking**: Data is extracted in monthly chunks to avoid 10,000 record limit
5. **Export**: Data is saved to Excel files in the instance's output folder

### REST API Method (Instance 3)

1. **Authentication**: Script prompts for username and password
2. **Connection Test**: Verifies API access
3. **Extraction**: Data is extracted via REST API calls
   - Incidents opened this month
   - Incidents closed this month
   - Active incidents
4. **Export**: Data is saved to Excel files

### Delta Extraction

After the first run, the script saves a timestamp of the extraction. On subsequent runs:
- Only records modified or created since the last extraction are downloaded
- This significantly reduces extraction time for regular updates
- The timestamp is stored in `.last_extraction.json` in each output folder

## Date Filtering Logic

### For Instance 1 & 2 (JSONv2):

Tickets are extracted if they meet ANY of these criteria:
- Opened in the last N months
- Closed in the last N months
- Currently active

### For Instance 3 (REST API):

Three separate extracts:
- Incidents opened in current month
- Incidents closed in current month
- All active incidents

## Output

### File Structure

```
output/
├── instance1/
│   ├── incident_20250109_143022.xlsx
│   ├── sc_task_20250109_143045.xlsx
│   ├── incident_task_20250109_143108.xlsx
│   ├── problem_20250109_143131.xlsx
│   └── .last_extraction.json
├── instance2/
│   ├── incident_20250109_143200.xlsx
│   ├── sc_task_20250109_143223.xlsx
│   └── .last_extraction.json
└── instance3/
    ├── incidents_opened_current_month_20250109_143300.xlsx
    ├── incidents_closed_current_month_20250109_143315.xlsx
    ├── incidents_active_20250109_143330.xlsx
    └── .last_extraction.json
```

### Excel File Format

Each Excel file contains:
- **Data** sheet: All extracted records with all fields
- **Metadata** sheet: Extraction timestamp, record count, ticket type

## Troubleshooting

### ChromeDriver Issues

**Error**: "ChromeDriver version doesn't match Chrome"
- Solution: Update ChromeDriver to match your Chrome version

**Error**: "ChromeDriver not found"
- Solution: Install ChromeDriver and ensure it's in your PATH

### Login Issues

**Problem**: Script doesn't detect login
- Solution: Ensure you're fully logged in and on a ServiceNow page
- Wait for the page to fully load before moving on

### No Data Extracted

**Check**:
1. Assignment groups file exists and has valid data
2. Assignment groups actually exist in ServiceNow
3. There are tickets matching your criteria
4. Date range is appropriate

### API Authentication Failed

**Check**:
1. Username and password are correct
2. User has API access permissions
3. Base URL is correct (should not include /api/now)

## Advanced Configuration

### Switching Between Parent and Direct Assignment Groups

Edit `config/instances.json`:

```json
{
  "instance1": {
    ...
    "use_parent_groups": false  // Change to false for direct groups
  }
}
```

### Switching from JSONv2 to REST API

If REST API becomes available for Instance 1 or 2:

```json
{
  "instance1": {
    ...
    "extraction_method": "rest_api"  // Change from "jsonv2"
  }
}
```

### Custom Ticket Types

Add or remove ticket types in the configuration:

```json
{
  "instance1": {
    ...
    "ticket_types": ["incident", "change_request", "problem"]
  }
}
```

Note: You'll need to ensure the corresponding URL templates exist in the code.

## Performance Tips

1. **Use Delta Extraction**: Run regularly to take advantage of delta extraction
2. **Limit Time Range**: Use `--months 3` instead of 6 if you don't need older data
3. **Process Instances Separately**: Use `--instances` to process one at a time
4. **Close Unnecessary Applications**: Chrome with Selenium can be resource-intensive

## Security Notes

1. **Credentials**: REST API credentials are prompted at runtime and not stored
2. **Session Cookies**: Selenium maintains browser session only during execution
3. **Output Files**: Contain sensitive ServiceNow data - protect appropriately
4. **Configuration Files**: Store securely, especially if URLs are sensitive

## Limitations

1. **10,000 Record Limit**: ServiceNow limits queries to 10,000 records
   - Mitigated by monthly chunking
   - If a single month has >10,000 records, consider further chunking
2. **Manual Login**: JSONv2 method requires manual login for each instance
3. **Browser Requirement**: JSONv2 method requires Chrome browser to be installed

## Future Enhancements

Potential improvements:
- Support for additional ticket types
- Automated login for JSONv2
- Support for other browsers (Firefox, Edge)
- Parallel extraction for multiple instances
- Email notifications on completion
- Data validation and quality checks
- Incremental backup of previous extractions

## License

This tool is provided as-is for extracting data from ServiceNow instances you have authorization to access.

## Support

For issues or questions:
1. Check this README
2. Review error messages carefully
3. Verify configuration files
4. Test with a single instance first
