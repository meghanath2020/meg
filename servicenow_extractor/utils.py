"""
Utility functions for ServiceNow data extraction
"""
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from dateutil.relativedelta import relativedelta
import urllib.parse


def get_date_ranges_monthly(months: int = 6) -> List[Tuple[datetime, datetime]]:
    """
    Generate monthly date ranges for the past N months

    Args:
        months: Number of months to go back

    Returns:
        List of tuples containing (start_date, end_date) for each month
    """
    date_ranges = []
    current_date = datetime.now()

    for i in range(months):
        # Calculate the start of each month
        month_start = current_date - relativedelta(months=i)
        month_start = month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Calculate the end of each month
        month_end = month_start + relativedelta(months=1) - timedelta(seconds=1)

        date_ranges.append((month_start, month_end))

    # Reverse to get chronological order
    date_ranges.reverse()
    return date_ranges


def format_servicenow_date(dt: datetime) -> str:
    """
    Format datetime for ServiceNow query

    Args:
        dt: datetime object

    Returns:
        Formatted date string for ServiceNow (YYYY-MM-DD HH:MM:SS)
    """
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def build_date_query(start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      active_only: bool = False) -> str:
    """
    Build date-based query criteria for ServiceNow

    Args:
        start_date: Start date for filtering
        end_date: End date for filtering
        active_only: Include only active tickets

    Returns:
        Query string for ServiceNow
    """
    query_parts = []

    if start_date and end_date:
        # Tickets opened in date range OR closed in date range OR active
        start_str = format_servicenow_date(start_date)
        end_str = format_servicenow_date(end_date)

        date_query = (
            f"(opened_atBETWEENjavascript:gs.dateGenerate('{start_str}')@"
            f"javascript:gs.dateGenerate('{end_str}')^"
            f"ORclosed_atBETWEENjavascript:gs.dateGenerate('{start_str}')@"
            f"javascript:gs.dateGenerate('{end_str}')"
        )

        if active_only:
            date_query += "^ORactive=true)"
        else:
            date_query += ")"

        query_parts.append(date_query)

    elif active_only:
        query_parts.append("active=true")

    return '^'.join(query_parts) if query_parts else ''


def build_assignment_group_query(assignment_groups: List[str],
                                  use_parent_groups: bool = True) -> str:
    """
    Build assignment group query

    Args:
        assignment_groups: List of assignment group names
        use_parent_groups: Use parent assignment groups or direct groups

    Returns:
        Query string for ServiceNow
    """
    groups_str = ','.join(assignment_groups)

    if use_parent_groups:
        return f"assignment_group.parent.nameIN{groups_str}"
    else:
        return f"assignment_groupIN{groups_str}"


def build_complete_query(assignment_groups: List[str],
                         use_parent_groups: bool = True,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         active_only: bool = False,
                         last_extraction_time: Optional[datetime] = None) -> str:
    """
    Build complete query combining assignment groups and date filters

    Args:
        assignment_groups: List of assignment group names
        use_parent_groups: Use parent assignment groups or direct groups
        start_date: Start date for filtering
        end_date: End date for filtering
        active_only: Include only active tickets
        last_extraction_time: Last extraction time for delta extraction

    Returns:
        Complete query string for ServiceNow
    """
    query_parts = []

    # Add assignment group query
    if assignment_groups:
        ag_query = build_assignment_group_query(assignment_groups, use_parent_groups)
        query_parts.append(ag_query)

    # For delta extraction, use last extraction time
    if last_extraction_time:
        last_update_str = format_servicenow_date(last_extraction_time)
        delta_query = (
            f"(sys_updated_on>{last_update_str}^"
            f"ORsys_created_on>{last_update_str})"
        )
        query_parts.append(delta_query)
    else:
        # Use date range filtering
        date_query = build_date_query(start_date, end_date, active_only)
        if date_query:
            query_parts.append(date_query)

    return '^'.join(query_parts)


def encode_query_for_url(query: str) -> str:
    """
    URL encode the query string

    Args:
        query: Query string

    Returns:
        URL encoded query string
    """
    return urllib.parse.quote(query, safe='')


def chunk_date_range(start_date: datetime, end_date: datetime, months: int = 1) -> List[Tuple[datetime, datetime]]:
    """
    Split a date range into smaller chunks to avoid the 10000 record limit

    Args:
        start_date: Start date
        end_date: End date
        months: Chunk size in months

    Returns:
        List of date range tuples
    """
    chunks = []
    current_start = start_date

    while current_start < end_date:
        current_end = min(current_start + relativedelta(months=months), end_date)
        chunks.append((current_start, current_end))
        current_start = current_end + timedelta(seconds=1)

    return chunks
