# Enrich Metrics with Human-Readable Filter Names

## Overview

This script joins the three main Kantar BLS tables using `FILTER_ID` as the join key to create enriched metrics with human-readable filter names.

## Tables Joined

1. **bls_metrics** - Core lift metrics
2. **kantar_bls_filter_ids** - Filter metadata (GROUP_NAME, NAME, SURVEY_LABEL)
3. **kantar_bls_filters** - Additional filter details

**Join Key**: `FILTER_ID` (unique identifier linking all tables)

## Usage

### Basic Usage

```bash
python scripts/enrich_metrics_with_filters.py
```

### What It Does

1. **Loads all three tables** from the `data/` directory
2. **Joins tables** on `FILTER_ID`:
   - First: `bls_metrics` + `kantar_bls_filter_ids`
   - Then: Result + `kantar_bls_filters`
3. **Creates human-readable filter names** by combining:
   - Channel information (TV, Social, Digital, etc.)
   - Demographics (Hispanic, Gen Z, etc.)
   - Survey labels
   - Filter names
4. **Saves enriched data** to:
   - `output/bls_metrics_enriched.csv`
   - `data/bls_metrics_enriched.csv`

## Output

### New Column: `FILTER_NAME_READABLE`

This column contains human-readable filter names like:

- **"TV - Hispanic"** - TV channel, Hispanic demographic
- **"Social - Gen Z"** - Social media, Gen Z demographic
- **"Digital - The Trade Desk"** - Digital channel, specific publisher
- **"Podcast - iHeart"** - Podcast channel, iHeart platform
- **"OTT - Amazon CTV"** - OTT channel, Amazon CTV platform
- **"Creative - Placement Location - Stories"** - Creative placement

### Example Output

| METRIC_NAME | LIFT | FILTER_ID | FILTER_NAME_READABLE | GROUP_NAME | SURVEY_LABEL |
|-------------|------|-----------|---------------------|------------|--------------|
| Unaided Brand Awareness | 10.5% | 24968925 | Digital - The Trade Desk | Creative | CORE |
| Brand Favorability | 8.2% | 23589201 | Digital - Realm | Site All Hits | CORE |
| Consideration | 12.1% | 23150189 | Podcast - iHeart | Site All Hits | CORE |

## How Human-Readable Names Are Created

The script intelligently combines information from:

1. **GROUP_NAME** - Category (Creative, Site All Hits, TV Network, etc.)
2. **FILTER_NAME** - Specific filter name
3. **NAME** - Alternative name field
4. **SURVEY_LABEL** - Survey segment (CORE, HISPANIC, etc.)

**Logic**:
- Extracts channel (TV, Social, Digital, Podcast, OTT, etc.)
- Extracts demographics (Hispanic, Gen Z, Millennial, etc.)
- Combines into readable format: "Channel - Demographic - Details"

## Use Cases

### 1. Quick Analysis in Excel

```python
# Run the script
python scripts/enrich_metrics_with_filters.py

# Open in Excel
# File: output/bls_metrics_enriched.csv
```

Now you can:
- Filter by readable filter names
- Sort by channel or demographic
- Create pivot tables easily

### 2. Reporting

```python
import pandas as pd

# Load enriched data
df = pd.read_csv('output/bls_metrics_enriched.csv')

# Group by readable filter names
summary = df.groupby('FILTER_NAME_READABLE')['LIFT'].mean()
print(summary)
```

### 3. Visualization

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('output/bls_metrics_enriched.csv')

# Group by readable filter name
by_filter = df.groupby('FILTER_NAME_READABLE')['LIFT'].mean().sort_values()

# Create chart
by_filter.plot(kind='barh', figsize=(12, 8))
plt.title('Average Lift by Filter (Human-Readable Names)')
plt.show()
```

## File Structure

### Input Files (in `data/`)

- `bls_metrics.csv` - Core metrics
- `kantar_bls_filter_ids.csv` - Filter metadata
- `kantar_bls_filters.csv` - Additional filter details

### Output Files

- `output/bls_metrics_enriched.csv` - Enriched metrics (for analysis)
- `data/bls_metrics_enriched.csv` - Same file in data directory (for easy access)

## Column Mapping

### From bls_metrics
- All original columns (LIFT, METRIC_NAME, etc.)
- `FILTER_ID` (join key)

### From kantar_bls_filter_ids
- `GROUP_NAME` - Filter category
- `NAME` - Filter name
- `SURVEY_ID` - Survey identifier
- `SURVEY_LABEL` - Survey segment (CORE, HISPANIC, etc.)

### From kantar_bls_filters
- Additional `GROUP_NAME` and `NAME` (if different)
- Additional metadata

### New Column
- `FILTER_NAME_READABLE` - Human-readable filter name

## Examples of Human-Readable Names

Based on the data structure, you might see names like:

- **"TV - CORE"** - TV channel, Core survey
- **"Social - Facebook - CORE"** - Social media, Facebook, Core survey
- **"Digital - The Trade Desk - CORE"** - Digital, The Trade Desk, Core survey
- **"Podcast - iHeart - CORE"** - Podcast, iHeart, Core survey
- **"OTT - Amazon CTV - HISPANIC"** - OTT, Amazon CTV, Hispanic survey
- **"Creative - Placement Location - Stories"** - Creative, Stories placement

## Customization

To customize how human-readable names are created, edit the `create_human_readable_filter_name()` function in the script:

```python
def create_human_readable_filter_name(row):
    # Your custom logic here
    # Combine GROUP_NAME, FILTER_NAME, NAME, SURVEY_LABEL
    # Return readable string
    pass
```

## Integration with Main Analyzer

The main `KantarBLSAnalyzer` class already does this joining, but this script:

- ✅ Focuses specifically on creating readable names
- ✅ Can be run standalone
- ✅ Useful for quick enrichment without full analysis
- ✅ Good for sharing with non-technical team members

## Troubleshooting

### Missing Filter Names

If some rows have "Filter {ID}" as the name:
- The filter metadata might be missing
- Check that all three CSV files are present
- Verify FILTER_ID values match across tables

### Duplicate Rows

If you see duplicate rows after joining:
- This can happen if filter_ids table has multiple rows per FILTER_ID
- The script handles this by using `drop_duplicates()`
- If issues persist, check the source data

### Performance

For very large files:
- The script loads everything into memory
- For files > 1GB, consider chunking
- Processing time: ~10-30 seconds for typical files

---

*Document Version: 1.0*  
*Last Updated: November 2025*

