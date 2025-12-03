# Time Period Extraction from Filter Names

## Overview

The analysis system now extracts time periods from filter names and converts them to standardized date formats. This enables time-based analysis and trend tracking.

## How It Works

### Step 1: Join Tables

The system performs the following joins:

1. **bls_metrics** → **kantar_bls_filter_ids** (on `FILTER_ID`)
   - Gets: `GROUP_NAME`, `NAME`, `SURVEY_ID`, `SURVEY_LABEL`

2. **Result** → **kantar_bls_filters** (on `FILTER_ID`)
   - Gets: Additional `FILTER_NAME` and `GROUP_NAME` details
   - Consolidates overlapping columns intelligently

### Step 2: Extract Time Periods

The system searches for time information in this order:
1. `FILTER_NAME` (primary source)
2. `NAME` (fallback)
3. `SURVEY_LABEL` (fallback)
4. `GROUP_NAME` (last resort)

### Step 3: Parse Time to Date

Converts time period strings to standardized `YYYY-MM-DD` format.

## Supported Time Formats

The parser recognizes multiple time formats:

### Month-Year Formats

- **"April 2025"** → `TIME_PERIOD`: "April 2025", `TIME_DATE`: "2025-04-01"
- **"Apr 2025"** → `TIME_PERIOD`: "April 2025", `TIME_DATE`: "2025-04-01"
- **"April, 2025"** → `TIME_PERIOD`: "April 2025", `TIME_DATE`: "2025-04-01"

### Quarter Formats

- **"Q2 2025"** → `TIME_PERIOD`: "Q2 2025", `TIME_DATE`: "2025-04-01"
- **"2025 Q2"** → `TIME_PERIOD`: "Q2 2025", `TIME_DATE`: "2025-04-01"
- **"Q2-2025"** → `TIME_PERIOD`: "Q2 2025", `TIME_DATE`: "2025-04-01"

### Date Formats

- **"2025-04"** → `TIME_PERIOD`: "April 2025", `TIME_DATE`: "2025-04-01"
- **"2025/04"** → `TIME_PERIOD`: "April 2025", `TIME_DATE`: "2025-04-01"
- **"2025-04-15"** → `TIME_PERIOD`: "2025-04-15", `TIME_DATE`: "2025-04-15"

### Year-Only Formats

- **"2025"** → `TIME_PERIOD`: "2025", `TIME_DATE`: "2025-01-01"

## Output Columns

After processing, the merged dataset includes:

- **`TIME_PERIOD`**: Human-readable time period (e.g., "April 2025", "Q2 2025")
- **`TIME_DATE`**: Standardized date format `YYYY-MM-DD` (e.g., "2025-04-01")

## Usage in Analysis

### Time-Based Grouping

```python
# Group by time period
trends = analyzer.analyze_trends(group_by=['TIME_PERIOD', 'CHANNEL'])

# Group by date for time series
trends = analyzer.analyze_trends(group_by=['TIME_DATE', 'METRIC_NAME'])
```

### Time Series Analysis

```python
# Filter by date range
from datetime import datetime
df = analyzer.merged_data
df['TIME_DATE'] = pd.to_datetime(df['TIME_DATE'])
recent_data = df[df['TIME_DATE'] >= datetime(2025, 1, 1)]
```

## Examples

### Example 1: Month Extraction

**Input Filter Name**: "Amazon CTV Campaign - April 2025"

**Output**:
- `TIME_PERIOD`: "April 2025"
- `TIME_DATE`: "2025-04-01"

### Example 2: Quarter Extraction

**Input Filter Name**: "Q2 2025 Brand Campaign"

**Output**:
- `TIME_PERIOD`: "Q2 2025"
- `TIME_DATE`: "2025-04-01" (first month of Q2)

### Example 3: Date Format

**Input Filter Name**: "Campaign 2025-04-15"

**Output**:
- `TIME_PERIOD`: "2025-04-15"
- `TIME_DATE`: "2025-04-15"

## Handling Missing Time Information

If time information cannot be extracted:
- `TIME_PERIOD`: "Unknown"
- `TIME_DATE`: `None`

You can filter these out:
```python
df_with_time = df[df['TIME_PERIOD'] != 'Unknown']
```

## Customization

To add support for additional time formats, modify the `_parse_time_from_text()` and `_parse_time_to_date()` methods in `scripts/analyze.py`.

### Adding New Patterns

```python
# In _parse_time_from_text(), add new pattern:
# Pattern X: Your custom format
pattern = r'your_regex_pattern'
match = re.search(pattern, text, re.IGNORECASE)
if match:
    # Extract and format
    return formatted_time_string
```

## Benefits

1. **Standardized Dates**: All time periods converted to `YYYY-MM-DD` format
2. **Flexible Parsing**: Handles multiple input formats
3. **Time Series Ready**: Dates can be used for time series analysis
4. **Trend Analysis**: Enables month-over-month and quarter-over-quarter comparisons

## Troubleshooting

### No Time Extracted

If `TIME_PERIOD` shows "Unknown" for many rows:
- Check if filter names contain time information
- Verify the format matches supported patterns
- Consider adding custom patterns for your specific naming conventions

### Incorrect Dates

If dates are parsed incorrectly:
- Review the filter names to understand the format
- Add custom parsing logic for your specific format
- Check for typos or unusual date formats in the source data

---

*Document Version: 1.0*  
*Last Updated: November 2025*


