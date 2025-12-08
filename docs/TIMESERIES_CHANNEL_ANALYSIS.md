# Time Series and Channel Analysis

## Overview

Based on the Kantar API structure and conversation with Keith, the analysis system now supports:

1. **Time Series Analysis** - Track brand lift metrics over time
2. **Channel Analysis** - Analyze performance by media channel
3. **Multiple Filter ID Aggregation** - Combine results from multiple filters

## Kantar API Structure

### Time/Date Information
- **Location**: Filters call (not metrics call)
- **Group Name**: "timestamp" (this is the GROUP_NAME for time filters)
- **Date Range**: Contained in the NAME field when GROUP_NAME is "timestamp"
- **Usage**: Use filter IDs from timestamp group to get time-specific metrics

### Channel Information
- **Location**: Filters call (not metrics call)
- **Prefix/Folder**: "XM" prefix/folder structure (Kantar's channel folder naming)
- **Usage**: Channels are identified from GROUP_NAME, FILTER_NAME, or NAME fields
- **Note**: The metrics call uses default digital control/exposed definitions, so non-digital channels may look different

### Multiple Filter IDs
- **Capability**: You can pass multiple filter IDs to the metrics call
- **Use Case**: Combine filters like "last 7 days" + "last 3 months" for aggregated analysis
- **Method**: Pass list of filter IDs, system aggregates results

## Usage Examples

### 1. Time Series Analysis

```python
from analyze import KantarBLSAnalyzer

analyzer = KantarBLSAnalyzer()
analyzer.load_data()
analyzer.clean_and_merge()

# Analyze all metrics over time
time_series = analyzer.analyze_time_series()
print(time_series)

# Analyze specific metric over time
dashpass_ts = analyzer.analyze_time_series(metric_name="DashPass")

# Analyze specific channel over time
social_ts = analyzer.analyze_time_series(channel="Social")
```

**Output**: DataFrame with columns:
- `TIME_DATE` or `TIME_PERIOD` - Time dimension
- `METRIC_NAME` - Brand metric
- `LIFT_mean` - Average lift
- `LIFT_std` - Standard deviation
- `LIFT_count` - Number of observations
- `EXPOSED_POPULATION_sum` - Total exposed population
- `CONTROL_POPULATION_sum` - Total control population

### 2. Channel Analysis

```python
# Analyze all metrics by channel
channel_analysis = analyzer.analyze_by_channel()
print(channel_analysis)

# Analyze specific metric by channel
affinity_channels = analyzer.analyze_by_channel(metric_name="Affinity")

# Analyze channels for specific time period
q4_channels = analyzer.analyze_by_channel(time_period="Q4 2025")
```

**Output**: DataFrame with columns:
- `CHANNEL` - Media channel
- `METRIC_NAME` - Brand metric
- `LIFT_mean` - Average lift
- `LIFT_std` - Standard deviation
- `LIFT_count` - Number of observations
- `CV` - Coefficient of variation (consistency measure)
- `IS_CONSISTENT` - Boolean indicating if metric is consistent (CV < 0.5)

### 3. Multiple Filter ID Aggregation

```python
# Aggregate results from multiple filter IDs
# Example: Combine "last 7 days" + "last 3 months" filters
filter_ids = [12345, 12346, 12347]  # Your filter IDs

# Weighted mean (by population size) - recommended
aggregated = analyzer.aggregate_filter_ids(
    filter_ids=filter_ids,
    method='weighted_mean'
)

# Simple mean
aggregated = analyzer.aggregate_filter_ids(
    filter_ids=filter_ids,
    method='mean'
)

# For specific metric
dashpass_agg = analyzer.aggregate_filter_ids(
    filter_ids=filter_ids,
    metric_name="DashPass Worth",
    method='weighted_mean'
)
```

**Output**: DataFrame with columns:
- `METRIC_NAME` - Brand metric
- `AGGREGATED_LIFT` or `LIFT_mean` - Aggregated lift value
- `LIFT_std` - Standard deviation across filters
- `LIFT_count` - Number of filter/metric combinations
- `EXPOSED_POPULATION_sum` - Total exposed population
- `CONTROL_POPULATION_sum` - Total control population
- `FILTER_IDS` - String of filter IDs used
- `NUM_FILTERS` - Number of filters aggregated

## Aggregation Methods

### Weighted Mean (Recommended)
- **Method**: `'weighted_mean'`
- **How it works**: Weights lift values by total population size
- **Use when**: You want to account for different sample sizes across filters
- **Formula**: `weighted_lift = sum(lift * population) / sum(population)`

### Simple Mean
- **Method**: `'mean'`
- **How it works**: Simple average of lift values
- **Use when**: All filters have similar sample sizes
- **Formula**: `mean_lift = mean(lift_values)`

### Sum
- **Method**: `'sum'`
- **How it works**: Sums lift values and populations
- **Use when**: You want cumulative totals
- **Note**: Less common for lift analysis

## Finding Filter IDs

To find filter IDs for time periods or channels:

```python
# After loading and merging data
df = analyzer.merged_data

# Find timestamp filters (time periods)
timestamp_filters = df[df['GROUP_NAME'].str.lower() == 'timestamp']
print("Time period filters:")
print(timestamp_filters[['FILTER_ID', 'NAME', 'FILTER_NAME']].head())

# Find channel filters (look for XM prefix or channel keywords)
channel_filters = df[df['GROUP_NAME'].str.contains('XM', case=False, na=False)]
print("\nChannel filters:")
print(channel_filters[['FILTER_ID', 'GROUP_NAME', 'FILTER_NAME']].head())

# Find filters for specific time range
# Example: "last 7 days" to "last 3 months"
time_range_filters = df[
    df['FILTER_NAME'].str.contains('7 days|3 months', case=False, na=False)
]
print("\nTime range filters:")
print(time_range_filters[['FILTER_ID', 'FILTER_NAME']].head())
```

## Best Practices

1. **Time Series Analysis**
   - Use `TIME_DATE` when available (standardized dates)
   - Filter by specific metrics or channels for focused analysis
   - Set `min_observations` to filter out sparse time periods

2. **Channel Analysis**
   - Use `min_observations=3` or higher for reliable channel comparisons
   - Check `IS_CONSISTENT` flag to identify reliable channel signals
   - Compare CV (coefficient of variation) across channels

3. **Filter ID Aggregation**
   - Use `weighted_mean` when filters have different sample sizes
   - Only aggregate filters that make logical sense together
   - Document which filter IDs were used for reproducibility

4. **Data Quality**
   - Verify that time filters have GROUP_NAME = "timestamp"
   - Check that channel filters are correctly identified
   - Ensure filter IDs exist in your data before aggregating

## Limitations & Notes

1. **Non-Digital Channels**: The metrics call uses default digital control/exposed definitions, so non-digital channels may show different results than expected. This is a known Kantar API limitation.

2. **Time Period Extraction**: The system extracts time periods from filter names. If Kantar's naming conventions change, you may need to update the extraction logic.

3. **Channel Identification**: Channels are identified using keyword matching. If Kantar uses new channel names, update the `channel_keywords` dictionary in `_extract_dimensions()`.

4. **Filter Aggregation**: Aggregating filters assumes they can be logically combined. Be careful when combining filters that might overlap or conflict.

## Example Workflow

```python
# 1. Load and process data
analyzer = KantarBLSAnalyzer()
analyzer.load_data()
analyzer.clean_and_merge()

# 2. Time series analysis for key metrics
key_metrics = ["DashPass Worth", "Brand Affinity", "Unaided Awareness"]
for metric in key_metrics:
    ts = analyzer.analyze_time_series(metric_name=metric)
    print(f"\n{metric} over time:")
    print(ts)

# 3. Channel comparison for current period
current_channels = analyzer.analyze_by_channel(
    time_period="December 2025",
    min_observations=5
)
print("\nChannel performance (December 2025):")
print(current_channels.sort_values('LIFT_mean', ascending=False))

# 4. Aggregate recent time periods
# Find filter IDs for "last 7 days" and "last 3 months"
recent_filters = [12345, 12346]  # Replace with actual filter IDs
recent_metrics = analyzer.aggregate_filter_ids(
    filter_ids=recent_filters,
    method='weighted_mean'
)
print("\nAggregated recent period metrics:")
print(recent_metrics.sort_values('AGGREGATED_LIFT', ascending=False))
```

## Related Documentation

- `DESIGN_DOCUMENTATION.md` - Overall system architecture
- `TIME_EXTRACTION.md` - How time periods are extracted
- `CONSISTENT_SIGNALS.md` - Signal detection methodology
- `RESULTS_INTERPRETATION.md` - How to interpret analysis results

