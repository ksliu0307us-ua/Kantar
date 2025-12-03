# Saved Merged Data

## Overview

The analysis system automatically saves the joined/merged tables after processing. This allows you to skip the merge step in future runs, significantly speeding up analysis.

## How It Works

### Automatic Saving

When you run `clean_and_merge()`, the system automatically saves the merged dataset:

```python
analyzer = KantarBLSAnalyzer()
analyzer.load_data()
analyzer.clean_and_merge(save_merged=True)  # Default is True
```

**Output**: `data/bls_metrics_merged.csv`

This file contains:
- All columns from `bls_metrics`
- All columns from `kantar_bls_filter_ids` (joined on `FILTER_ID`)
- All columns from `kantar_bls_filters` (joined on `FILTER_ID`)
- Extracted dimensions: `CHANNEL`, `DEMOGRAPHIC`, `TIME_PERIOD`, `TIME_DATE`
- Cleaned and standardized data

### Loading Saved Data

To skip the merge step and load previously saved data:

```python
analyzer = KantarBLSAnalyzer()
analyzer.load_merged_data()  # Loads data/bls_metrics_merged.csv
# Now you can directly run analysis without merging
analyzer.analyze_trends()
```

### File Priority

The system checks for merged files in this order:

1. **`bls_metrics_merged.csv`** (our saved version with all processing)
   - If found, uses this directly
   - Includes all extracted dimensions

2. **`bls_metrics_with_filters.csv`** (Kantar's pre-merged version)
   - If found, uses this but still runs dimension extraction
   - May not have all extracted dimensions

3. **Individual files** (fallback)
   - Loads and merges individual CSV files
   - Full processing pipeline

## Benefits

### Performance

- **First run**: Loads and merges files (~30-60 seconds)
- **Subsequent runs**: Loads saved file (~5-10 seconds)
- **Time savings**: 80-90% faster on subsequent runs

### Consistency

- Same merged data every time
- No risk of merge errors
- Reproducible results

### Convenience

- Share merged file with team
- Use in other tools (Excel, Tableau, etc.)
- Backup for analysis

## File Details

### Location

```
data/bls_metrics_merged.csv
```

### Size

Typically 50-200 MB depending on data volume.

### Columns Included

- All original metric columns
- `FILTER_ID`, `FILTER_NAME`, `GROUP_NAME`
- `SURVEY_ID`, `SURVEY_LABEL`
- `CHANNEL` (extracted)
- `DEMOGRAPHIC` (extracted)
- `TIME_PERIOD` (extracted, e.g., "April 2025")
- `TIME_DATE` (extracted, standardized format "YYYY-MM-DD")

## Usage Examples

### Example 1: Save After Merge

```python
analyzer = KantarBLSAnalyzer()
analyzer.load_data()
analyzer.clean_and_merge(save_merged=True)  # Saves automatically
```

### Example 2: Load Saved Data

```python
analyzer = KantarBLSAnalyzer()
analyzer.load_merged_data()  # Fast - skips merge step
analyzer.analyze_trends()
```

### Example 3: Use in Other Tools

```python
# Save merged data
analyzer.clean_and_merge(save_merged=True)

# Now you can load it in pandas directly
import pandas as pd
df = pd.read_csv('data/bls_metrics_merged.csv')

# Or use in Excel, Tableau, etc.
```

### Example 4: Skip Saving

```python
# If you don't want to save (e.g., testing)
analyzer.clean_and_merge(save_merged=False)
```

## When to Re-save

You should re-save the merged data when:

- ✅ New data files are added
- ✅ Data files are updated
- ✅ You want to refresh the merged dataset
- ✅ After modifying the merge logic

**How to re-save**:
```python
analyzer.clean_and_merge(save_merged=True)  # Overwrites existing file
```

## File Management

### Backup

The saved file is valuable - consider backing it up:
- Version control (if file size allows)
- Shared drive
- Cloud storage

### Sharing

You can share `bls_metrics_merged.csv` with team members:
- They can load it directly without running merge
- Ensures everyone uses the same processed data
- Faster onboarding for new team members

### Cleanup

If you want to force a fresh merge:
```bash
# Delete the saved file
rm data/bls_metrics_merged.csv

# Next run will merge from scratch
```

## Integration with Other Tools

### Excel

```python
# Save merged data
analyzer.clean_and_merge(save_merged=True)

# Open in Excel
# File: data/bls_metrics_merged.csv
```

### Tableau/Looker

```python
# Use the saved CSV as a data source
# Connect Tableau/Looker to: data/bls_metrics_merged.csv
```

### Python Scripts

```python
import pandas as pd

# Load saved merged data
df = pd.read_csv('data/bls_metrics_merged.csv')

# Use for custom analysis
# All dimensions already extracted
```

## Troubleshooting

### File Not Found

If `load_merged_data()` fails:
- Check that `clean_and_merge()` was run first
- Verify file exists: `data/bls_metrics_merged.csv`
- Run `clean_and_merge(save_merged=True)` to create it

### Outdated Data

If saved data seems outdated:
- Delete `data/bls_metrics_merged.csv`
- Run `clean_and_merge(save_merged=True)` again
- Or just run it - it will overwrite the old file

### File Too Large

If the file is very large:
- Consider filtering before saving
- Use compression (future enhancement)
- Split by time period or channel

## Best Practices

1. **Save after merge**: Always use `save_merged=True` (default)
2. **Version control**: Consider adding timestamp to filename for versioning
3. **Regular updates**: Re-save when source data changes
4. **Share with team**: Use saved file for consistency across team
5. **Backup**: Keep backups of important merged datasets

---

*Document Version: 1.0*  
*Last Updated: November 2025*


