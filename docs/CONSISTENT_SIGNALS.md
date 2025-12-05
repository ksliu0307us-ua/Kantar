# Finding Consistent Signals Across Filters and Brand Metrics

## Overview

This analysis identifies brand metrics that show **consistent performance across different filters** (channels, demographics, time periods, etc.). These are metrics you can trust because they perform reliably regardless of the specific filter/segment.

## What Are Consistent Signals?

A **consistent signal** is a brand metric that:
- Shows reliable lift across **multiple different filters**
- Has **low variance** (doesn't bounce around randomly)
- Appears in **multiple channels, demographics, or time periods**
- Can be **trusted** for decision-making

### Example

**Consistent Signal**:
- "Unaided Brand Awareness" shows 10-15% lift across:
  - TV channel
  - Social channel
  - Digital channel
  - Multiple demographics
  - Multiple time periods
- **This is reliable** - you can trust this metric

**Inconsistent Signal**:
- "Brand Attribute X" shows:
  - 25% lift in one filter
  - -5% lift in another filter
  - 2% lift in a third filter
- **This is unreliable** - high variance, can't trust it

## How It Works

### Consistency Score Calculation

The system calculates a **Consistency Score** for each metric based on:

1. **Number of Unique Filters** (40% weight)
   - More filters = more reliable
   - Metric appearing in 10 filters is more trustworthy than one in 2 filters

2. **Coefficient of Variation** (40% weight)
   - Lower CV = more consistent
   - CV < 50% = consistent, CV > 100% = noisy

3. **Positive Lift Ratio** (20% weight)
   - Percentage of filters showing positive lift
   - Higher ratio = more reliable

**Formula**:
```
Consistency Score = 
  (Unique Filters / Max Filters) × 0.4 +
  (1 / (1 + CV)) × 0.4 +
  (Positive Lift Count / Total Observations) × 0.2
```

### Consistency Levels

Metrics are classified as:
- **High Consistency** (Score > 0.7): Very reliable, trust these
- **Medium Consistency** (Score 0.4-0.7): Moderately reliable
- **Low Consistency** (Score < 0.4): Less reliable, use with caution

## Usage

### Method 1: Using the Analyzer Class

```python
from analyze import KantarBLSAnalyzer

analyzer = KantarBLSAnalyzer()
analyzer.load_data()
analyzer.clean_and_merge()

# Find consistent signals
consistent_signals = analyzer.find_consistent_signals(
    min_filters=3,      # Must appear in at least 3 filters
    min_lift=0.0        # Minimum average lift (can be negative)
)

# View top consistent metrics
print(consistent_signals.head(10))
```

### Method 2: Using the Standalone Script

```bash
python scripts/find_consistent_signals.py
```

This will:
- Load and process data
- Find consistent signals
- Display top 20 metrics
- Show detailed breakdown for top 5
- Save results to CSV files

### Method 3: As Part of Pattern Identification

```python
patterns = analyzer.identify_patterns()
consistent_signals = patterns['consistent_signals']
```

## Output

### Consistent Signals DataFrame

Columns:
- **METRIC_NAME**: Name of the brand metric
- **AVG_LIFT**: Average lift across all filters
- **STD_LIFT**: Standard deviation of lift
- **TOTAL_OBSERVATIONS**: Total number of observations
- **POSITIVE_LIFT_COUNT**: Number of filters with positive lift
- **UNIQUE_FILTERS**: Number of different filters this metric appears in
- **CV**: Coefficient of variation (lower = more consistent)
- **CONSISTENCY_SCORE**: Overall consistency score (0-1)
- **CONSISTENCY_LEVEL**: High/Medium/Low classification

### Saved Files

1. **`output/consistent_signals_across_filters.csv`**
   - All metrics with consistency scores
   - Sorted by consistency score

2. **`output/metric_filter_consistency_breakdown.csv`**
   - Detailed breakdown by metric and filter
   - Shows lift per filter for each metric

## Interpreting Results

### High Consistency Score (> 0.7)

**What it means**: This metric performs reliably across many filters.

**Example**:
```
Metric: Unaided Brand Awareness
Consistency Score: 0.85
Unique Filters: 15
Average Lift: 12.5%
CV: 25%
```

**Interpretation**: 
- ✅ This metric is very reliable
- ✅ Shows consistent lift across 15 different filters
- ✅ Low variance (CV = 25%)
- ✅ **Trust this metric for decision-making**

### Medium Consistency Score (0.4 - 0.7)

**What it means**: This metric shows some consistency but with variation.

**Example**:
```
Metric: Brand Favorability
Consistency Score: 0.55
Unique Filters: 8
Average Lift: 8.3%
CV: 65%
```

**Interpretation**:
- ⚠️ Moderately reliable
- ⚠️ Shows lift but with more variation
- ⚠️ **Use with caution, look for patterns**

### Low Consistency Score (< 0.4)

**What it means**: This metric is inconsistent across filters.

**Example**:
```
Metric: Brand Attribute X
Consistency Score: 0.25
Unique Filters: 4
Average Lift: 5.2%
CV: 150%
```

**Interpretation**:
- ❌ Not reliable
- ❌ High variance (CV = 150%)
- ❌ **Don't make decisions based on this**

## Use Cases

### 1. Identify Reliable Metrics

Find which brand metrics you can trust:

```python
consistent_signals = analyzer.find_consistent_signals(min_filters=5)
high_consistency = consistent_signals[consistent_signals['CONSISTENCY_LEVEL'] == 'High']
print(f"Found {len(high_consistency)} highly consistent metrics")
```

### 2. Compare Metric Performance Across Filters

See how a specific metric performs across different filters:

```python
breakdown = analyzer.analyze_metric_filter_consistency(
    metric_name="Unaided Brand Awareness"
)
print(breakdown[['FILTER_NAME', 'CHANNEL', 'LIFT_MEAN', 'IS_CONSISTENT']])
```

### 3. Find Universal Metrics

Metrics that work across all channels:

```python
consistent_signals = analyzer.find_consistent_signals(min_filters=10)
universal_metrics = consistent_signals[
    (consistent_signals['CONSISTENCY_SCORE'] > 0.7) &
    (consistent_signals['AVG_LIFT'] > 5.0)
]
```

### 4. Identify Channel-Specific Metrics

Metrics that only work in specific channels:

```python
# Low consistency but high lift in some filters
inconsistent_but_strong = consistent_signals[
    (consistent_signals['CONSISTENCY_SCORE'] < 0.4) &
    (consistent_signals['AVG_LIFT'] > 10.0)
]
```

## Visualizations

The system automatically generates:

1. **Consistent Signals Scatter Plot**
   - X-axis: Average Lift
   - Y-axis: Consistency Score
   - Bubble size: Number of filters
   - Color: Number of filters
   - Shows which metrics are both strong AND consistent

2. **Top Consistent Metrics Bar Chart**
   - Top 15 metrics by consistency score
   - Shows lift and filter count for each

## Decision-Making Framework

### For Strategic Decisions

**Use High Consistency Metrics** (Score > 0.7):
- These are your most reliable metrics
- Safe to base strategic decisions on
- Work across multiple channels/segments

### For Tactical Decisions

**Use Medium Consistency Metrics** (Score 0.4-0.7):
- Can be useful for specific channels/segments
- Look at filter-level breakdown
- Test before scaling

### For Exploration

**Investigate Low Consistency Metrics** (Score < 0.4):
- May indicate channel-specific opportunities
- Could be worth testing in specific contexts
- Don't rely on for major decisions

## Example Analysis

```python
# Find consistent signals
consistent = analyzer.find_consistent_signals(min_filters=3)

# Top 10 most consistent
top_10 = consistent.head(10)

# Metrics that are both consistent AND strong
best_metrics = consistent[
    (consistent['CONSISTENCY_SCORE'] > 0.7) &
    (consistent['AVG_LIFT'] > 10.0)
]

print(f"Found {len(best_metrics)} metrics that are both consistent and strong")
print(best_metrics[['METRIC_NAME', 'AVG_LIFT', 'CONSISTENCY_SCORE', 'UNIQUE_FILTERS']])
```

## Key Insights

### What Consistent Signals Tell You

1. **Reliable Brand Metrics**
   - Metrics that consistently respond to advertising
   - Safe to track and report on
   - Good for executive dashboards

2. **Universal Messaging**
   - Metrics that work across all channels suggest universal messaging
   - Can scale these messages broadly

3. **Channel Opportunities**
   - Low consistency but high lift in some filters = channel-specific opportunity
   - Worth testing in those specific channels

4. **Data Quality**
   - High consistency = good data quality
   - Low consistency = may indicate measurement issues or real variation

## Best Practices

1. **Focus on High Consistency Metrics**
   - Use these for strategic reporting
   - Track these over time
   - Base decisions on these

2. **Investigate Medium Consistency**
   - Look at filter-level breakdown
   - Identify which filters work best
   - Test and refine

3. **Understand Low Consistency**
   - May be channel-specific
   - Could indicate measurement issues
   - Don't ignore, but don't rely on

4. **Regular Updates**
   - Re-run analysis as new data comes in
   - Consistency may improve with more data
   - Track changes over time

---

*Document Version: 1.0*  
*Last Updated: November 2025*

