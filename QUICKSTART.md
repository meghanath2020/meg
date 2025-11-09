# Quick Start Guide - ServiceNow Data Extractor

## 5-Minute Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Your Instances

Edit `config/instances.json` and update:
- `base_url` for each instance
- Keep or modify `ticket_types` as needed

```json
{
  "instance1": {
    "base_url": "https://YOUR-INSTANCE1.service-now.com",
    ...
  }
}
```

### Step 3: Create Assignment Groups Files

Create Excel files in the `assignment_groups/` folder with your groups:

**assignment_groups/instance1_groups.xlsx**

| assignment_group      |
|-----------------------|
| Your Team Name 1      |
| Your Team Name 2      |
| Your Team Name 3      |

Or let the script create sample files for you (run once, then update the files).

### Step 4: Run the Extractor

```bash
python servicenow_data_extractor.py
```

### Step 5: Login to ServiceNow

- Chrome browser will open
- Log in manually to each ServiceNow instance
- Script will automatically detect login and continue

### Step 6: Find Your Data

Check the `output/` folder for your Excel files:

```
output/
├── instance1/
│   ├── incident_20250109_143022.xlsx
│   ├── sc_task_20250109_143045.xlsx
│   └── ...
└── instance2/
    └── ...
```

## Common Commands

### Extract from specific instance only
```bash
python servicenow_data_extractor.py --instances instance1
```

### Extract last 3 months instead of 6
```bash
python servicenow_data_extractor.py --months 3
```

### Extract specific instances for specific time range
```bash
python servicenow_data_extractor.py --instances instance1 instance2 --months 3
```

## Important Notes

### For JSONv2 Method (Instance 1 & 2):
- Requires manual login
- Chrome browser will open
- Data extracted in monthly chunks
- Handles 10,000 record limit automatically

### For REST API Method (Instance 3):
- You'll be prompted for username/password
- No browser required
- Faster extraction
- Only extracts incidents:
  - Opened this month
  - Closed this month
  - Currently active

## Delta Extraction

After the first run:
- Subsequent runs only download changes
- Much faster!
- Automatic - no configuration needed

## Troubleshooting

### "Assignment groups file not found"
- Run the script once - it creates sample files
- Update the sample files with your actual groups
- Run again

### "ChromeDriver not found"
```bash
# Install ChromeDriver
# Ubuntu/Debian:
sudo apt-get install chromium-chromedriver

# macOS:
brew install chromedriver
```

### "No data extracted"
- Check assignment groups are correct
- Verify date range has data
- Ensure you're logged into correct instance

## Need Help?

See the full documentation in `SERVICENOW_EXTRACTOR_README.md`

## Configuration Examples

### Switch to Direct Assignment Groups (not parent)

In `config/instances.json`:
```json
{
  "instance1": {
    ...
    "use_parent_groups": false
  }
}
```

### Change Ticket Types

In `config/instances.json`:
```json
{
  "instance1": {
    ...
    "ticket_types": ["incident", "problem"]
  }
}
```

### Switch to REST API (if available)

In `config/instances.json`:
```json
{
  "instance1": {
    ...
    "extraction_method": "rest_api"
  }
}
```

## What Gets Extracted?

### Default Criteria (6 months):
- Tickets opened in last 6 months, OR
- Tickets closed in last 6 months, OR
- Tickets that are currently active

### Instance 3 (REST API):
- Incidents opened this month
- Incidents closed this month
- All active incidents

## File Naming

Files are named with timestamp:
- Format: `{ticket_type}_{YYYYMMDD}_{HHMMSS}.xlsx`
- Example: `incident_20250109_143022.xlsx`

## Next Steps

1. Review the full README for advanced features
2. Set up a scheduled task/cron job for regular extraction
3. Consider implementing data validation
4. Back up your output folder regularly

Enjoy using the ServiceNow Data Extractor!
