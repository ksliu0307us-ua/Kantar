# New Time Series Analysis - Martech Data Format

## Overview

This document describes the new time series analysis implementation using the timestamp-aggregated data format provided by the Martech team. The new data structure is cleaner and more direct than the previous format, making time series analysis more straightforward.

## Data Source

**Table**: `marketing_fivetran.google_sheets.kantar_bls_sample_data`  
**File**: `data/kantar_bls_sample_data.csv`

## Data Structure

The new data format includes:

- **`LIMITING_FILTER`**: Contains timestamp information in format "Timestamp: M/D/YY-M/D/YY"
  - Example: "Timestamp: 3/1/25-3/31/25" → March 2025
  - Example: "Timestamp: 4/1/25-6/30/25" → Q2 2025 (April-June)

- **`EXPOSED_FILTER` / `WEIGHT_SET`**: Contains channel information
  - Example: "XM: 2. Social" → Social channel
  - Example: "XM: 3. TV" → TV channel
  - Example: "XM: 4. Digital" → Digital channel
  - Example: "XM: 0. ANY" → All channels combined

- **`METRIC`**: Direct brand metric name (no decoding needed)

- **`LIFT`, `DELTA`, `CONTROL_`, `EXPOSED_`**: Pre-calculated lift metrics

- **`STATISTICAL_SIGNIFICANCE`**: P-values for significance testing

## Implementation

### Script: `scripts/analyze_timeseries_new.py`

A new standalone analyzer class `KantarBLSTimeSeriesAnalyzer` that:

1. **Loads data** from the new CSV format
2. **Extracts timestamps** from `LIMITING_FILTER` column
3. **Extracts channels** from `EXPOSED_FILTER` or `WEIGHT_SET` columns
4. **Performs time series analysis** - tracks metrics over time
5. **Performs channel analysis** - compares performance across channels
6. **Generates visualizations** - time series plots and channel comparisons
7. **Saves results** - CSV files and PNG plots

### Key Methods

#### `extract_timestamp(limiting_filter)`
- Parses "Timestamp: M/D/YY-M/D/YY" format
- Returns standardized date format (YYYY-MM-DD)
- Uses first day of the period for consistency

#### `extract_channel(exposed_filter, weight_set)`
- Prioritizes `WEIGHT_SET` over `EXPOSED_FILTER` (more reliable)
- Extracts channel from "XM: N. Channel" pattern
- Handles special cases: "Any", "Digital ONLY", combo filters

#### `analyze_time_series(metric_name, channel, min_observations)`
- Groups data by timestamp and metric
- Calculates mean, std, count, min, max for lift metrics
- Filters by minimum observations threshold
- Returns aggregated time series DataFrame

#### `analyze_by_channel(metric_name, min_observations)`
- Groups data by channel and metric
- Calculates channel-level statistics
- Sorts by average lift (highest first)
- Returns channel comparison DataFrame

## Results Summary

### Data Coverage
- **Total rows**: 47,616
- **Time periods**: 3 months (Feb, Mar, Apr 2025)
- **Channels**: 4 (TV, Social, Digital, Any)
- **Metrics**: 62 unique brand metrics

### Time Series Analysis
- **186 time series data points** (metric × time period combinations)
- Date range: 2025-02-01 to 2025-04-01
- Each data point includes:
  - Mean lift and standard deviation
  - Sample sizes (control and exposed)
  - Statistical significance

### Channel Analysis
- **248 channel-metric combinations**
- Channel performance ranking (by average lift):
  1. **TV**: 0.109 (10.9% average lift)
  2. **Any**: 0.092 (9.2% average lift)
  3. **Social**: 0.062 (6.2% average lift)
  4. **Digital**: 0.025 (2.5% average lift)

## Usage

### Basic Usage

```python
from scripts.analyze_timeseries_new import KantarBLSTimeSeriesAnalyzer

# Initialize
analyzer = KantarBLSTimeSeriesAnalyzer()

# Load and process data
analyzer.load_data()
analyzer.process_data()

# Analyze time series for all metrics
time_series = analyzer.analyze_time_series()

# Analyze by channel
channel_analysis = analyzer.analyze_by_channel()

# Save results
analyzer.save_results(time_series, channel_analysis)
```

### Analyze Specific Metric

```python
# Time series for DashPass metrics
dashpass_ts = analyzer.analyze_time_series(metric_name="DashPass")

# Channel comparison for DashPass
dashpass_channels = analyzer.analyze_by_channel(metric_name="DashPass")

# Plot time series
analyzer.plot_time_series(
    metric_name="DashPass Aided Awareness",
    save_path="output/dashpass_timeseries.png"
)

# Plot channel comparison
analyzer.plot_channel_comparison(
    metric_name="DashPass Aided Awareness",
    save_path="output/dashpass_channels.png"
)
```

### Analyze Specific Channel

```python
# Time series for TV channel only
tv_ts = analyzer.analyze_time_series(channel="TV")

# Plot TV performance over time
analyzer.plot_time_series(
    metric_name="Brand Favorability",
    channel="TV",
    save_path="output/tv_favorability.png"
)
```

## Output Files

### CSV Files
- `timeseries_analysis_time_series_YYYYMMDD_HHMMSS.csv`
  - Time series data with aggregated lift metrics by time period
  - Columns: TIMESTAMP, TIMESTAMP_DATE, METRIC_CLEAN, LIFT_mean, LIFT_std, LIFT_count, etc.

- `timeseries_analysis_channels_YYYYMMDD_HHMMSS.csv`
  - Channel comparison data with aggregated lift metrics by channel
  - Columns: CHANNEL, METRIC_CLEAN, LIFT_mean, LIFT_std, LIFT_count, etc.

### Plot Files
- `timeseries_{metric_name}_{date}.png`
  - Time series line plot with error bars
  - Shows lift trend over time for specific metric

- `channels_{metric_name}_{date}.png`
  - Horizontal bar chart comparing channels
  - Shows average lift by channel for specific metric

## Key Findings

1. **TV Channel Performance**: TV shows the highest average brand lift (10.9%), suggesting strong effectiveness for brand awareness campaigns.

2. **Digital Channel Performance**: Digital shows the lowest average lift (2.5%), which may indicate:
   - Different campaign objectives (lower-funnel vs. upper-funnel)
   - Different audience targeting
   - Need for more data points

3. **Time Coverage**: Currently have 3 months of data (Feb-Apr 2025). As more monthly data becomes available, trends will become clearer.

4. **Metric Diversity**: 62 unique metrics provide comprehensive brand measurement coverage across:
   - Awareness (Unaided, Aided)
   - Consideration
   - Favorability
   - DashPass-specific metrics
   - Category-specific awareness

## Next Steps

1. **Monthly Data Ingestion**: Set up automated monthly processing as new data arrives
2. **Trend Analysis**: With more data points, identify seasonal patterns and trends
3. **Statistical Testing**: Use statistical significance values to filter reliable signals
4. **Channel Attribution**: Deeper analysis of channel interactions and overlaps
5. **Demographic Analysis**: Break down by FOLDER_NAME and FILTER for demographic insights

## Differences from Previous Analysis

| Aspect | Previous Format | New Format |
|--------|----------------|------------|
| **Time Extraction** | Parsed from filter names | Direct from LIMITING_FILTER column |
| **Channel Extraction** | Complex joins with filter tables | Direct from EXPOSED_FILTER/WEIGHT_SET |
| **Data Structure** | Multiple joined tables | Single aggregated table |
| **Processing** | Complex merge logic | Direct column extraction |
| **Performance** | Slower (multiple joins) | Faster (direct access) |

## Validation with Martech Team

Please review the following with Celine:

1. **Column Mapping**: Verify that our interpretation of columns matches their intended use
2. **Timestamp Format**: Confirm that "Timestamp: M/D/YY-M/D/YY" format is consistent
3. **Channel Naming**: Verify channel extraction logic matches their naming conventions
4. **Monthly Cadence**: Confirm process for receiving new monthly data

## Questions for Martech Team

1. Will the column structure remain consistent in future monthly drops?
2. Are there any transformations needed before analysis?
3. Should we filter out any specific rows (e.g., test data, invalid filters)?
4. How should we handle quarterly aggregations (e.g., "4/1/25-6/30/25")?

