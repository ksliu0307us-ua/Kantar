# Kantar BLS Analysis System - Team Presentation Guide

## Quick Overview (2-minute version)

**What we built**: An automated analysis pipeline that transforms raw Kantar survey data into actionable brand lift insights.

**Why it matters**: Helps identify which marketing channels and messages actually move the needle, separating real patterns from statistical noise.

**How it works**: Loads data → Cleans & merges → Extracts dimensions → Analyzes patterns → Generates reports

---

## The Problem We Solved

### Before
- Data scattered across multiple CSV files and Snowflake tables
- Manual joining and cleaning required
- No systematic way to identify consistent patterns
- Hard to separate signal from noise

### After
- Automated pipeline from raw data to insights
- Consistent, reproducible analysis
- Clear classification of reliable vs. unreliable metrics
- Ready for weekly/biweekly reporting

---

## Architecture: The Big Picture

```
┌─────────────────┐
│  Raw Data       │  (CSV files or Snowflake)
│  - Metrics      │
│  - Filters      │
│  - Answers      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Data Loading   │  (Detects pre-merged files)
│  & Cleaning     │  (Standardizes formats)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Dimension      │  (Extracts: Channel, Time, Demographics)
│  Extraction     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Analysis       │  (Trends, Significance, Patterns)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Reporting      │  (Charts, Summary, Insights)
└─────────────────┘
```

---

## Key Design Decisions

### 1. Why One Class, Multiple Methods?

**Decision**: `KantarBLSAnalyzer` class with separate methods for each step.

**Reasoning**:
- ✅ Each step is testable independently
- ✅ Easy to extend with new analysis types
- ✅ Clear separation of concerns

**Example**:
```python
analyzer = KantarBLSAnalyzer()
analyzer.load_data()        # Step 1: Load
analyzer.clean_and_merge()  # Step 2: Prepare
analyzer.analyze_trends()   # Step 3: Analyze
```

### 2. Why Support Pre-merged Files?

**Decision**: Automatically use `bls_metrics_with_filters.csv` if available.

**Reasoning**:
- ⚡ **Performance**: Skips expensive merge operation (saves time)
- 🔄 **Flexibility**: Works with both raw and processed data
- 📊 **Real-world**: Often we get pre-merged exports from Snowflake

**How it works**:
```
If bls_metrics_with_filters.csv exists:
    → Use it directly (fast!)
Else:
    → Load individual files and merge (slower but works)
```

### 3. Why Keyword-Based Dimension Extraction?

**Decision**: Extract channel/demographics by matching keywords in filter names.

**Reasoning**:
- ✅ **Handles inconsistency**: Filter names vary ("TV", "Television", "Broadcast")
- ✅ **No schema dependency**: Works without requiring standardized naming
- ✅ **Easy to customize**: Add new keywords without code changes

**Example**:
```python
# Finds "TV" in filter name → Classifies as "TV" channel
# Finds "Social" → Classifies as "Social" channel
```

**Trade-off**: 
- ⚠️ Might misclassify if keywords overlap
- ✅ Can be refined with priority rules or explicit mapping

### 4. Why Separate Signal from Noise?

**Decision**: Explicitly classify metrics as "signal" (reliable) vs "noise" (unreliable).

**Reasoning**:
- 🎯 **Business need**: Moshe asked to "separate signal from noise"
- 📊 **Decision support**: Focus on actionable insights
- 🔍 **Transparency**: Shows which metrics are trustworthy

**Method**:
- **Signal**: Statistically significant AND consistent (low variance)
- **Noise**: High variance or insufficient data

**Metrics**:
- **Significance**: p-value ≤ 0.05 (from Kantar)
- **Consistency**: Coefficient of Variation < 50% (std/mean)
- **Sample Size**: Minimum 3 observations

---

## Data Flow Deep Dive

### Step 1: Data Loading
```
Input: CSV files in data/ directory
├── bls_metrics.csv (or bls_metrics_with_filters.csv)
├── kantar_bls_filters.csv
├── kantar_bls_filter_ids.csv
└── codebook_mapping.csv

Process:
1. Check for pre-merged file (fast path)
2. Load individual files if needed (slow path)
3. Handle large files with chunking
4. Validate required columns exist
```

### Step 2: Cleaning & Merging
```
Process:
1. Standardize data types (ensure numbers are numeric)
2. Calculate missing LIFT values
3. Merge metrics with filter metadata
4. Extract dimensions (Channel, Demographics, Time)
```

**Key Insight**: The merge step is expensive, so we skip it if pre-merged file exists.

### Step 3: Analysis
```
Three types of analysis:

1. Trend Analysis
   → Aggregates by dimensions (channel, metric, etc.)
   → Calculates mean, std dev, counts

2. Significance Detection
   → Flags statistically significant results
   → Calculates confidence intervals

3. Pattern Identification
   → Separates signal from noise
   → Identifies consistent metrics
```

### Step 4: Reporting
```
Outputs:
├── Text report (summary of findings)
├── Visualizations (bar charts, heatmaps)
└── Saved to output/ directory
```

---

## Example: How It Works in Practice

### Scenario: Analyzing TV vs Social Media Performance

```python
# 1. Initialize
analyzer = KantarBLSAnalyzer()

# 2. Load data (automatically uses pre-merged file if available)
analyzer.load_data()

# 3. Clean and prepare
analyzer.clean_and_merge()
# → Extracts CHANNEL dimension from filter names
# → Classifies as "TV" or "Social" based on keywords

# 4. Analyze
trends = analyzer.analyze_trends(group_by=['CHANNEL', 'METRIC_NAME'])
# → Groups by channel and metric
# → Calculates average lift for each combination

# 5. Identify patterns
patterns = analyzer.identify_patterns()
# → Separates reliable metrics (signal) from unreliable (noise)

# 6. Generate report
analyzer.generate_report()
# → Creates charts and summary
```

**Output**:
- Chart showing average lift by channel
- List of top-performing metrics
- Classification of signal vs noise metrics

---

## Key Metrics Explained

### LIFT
**Formula**: `(Exposed% - Control%) / Control% × 100`

**Meaning**: Percentage point increase in metric for exposed vs control group.

**Example**: 
- Control: 20% aware
- Exposed: 25% aware
- Lift: (25-20)/20 × 100 = **25% lift**

### Coefficient of Variation (CV)
**Formula**: `Standard Deviation / Mean`

**Meaning**: How consistent a metric is across observations.

**Interpretation**:
- CV < 50% → Consistent (signal)
- CV > 100% → High variance (noise)

**Example**:
- Metric has mean lift of 10% with std dev of 3%
- CV = 3/10 = 30% → **Consistent signal**

### Statistical Significance
**Source**: Provided by Kantar (p-value)

**Meaning**: Likelihood that observed difference is real (not random).

**Threshold**: p ≤ 0.05 (95% confidence)

---

## Directory Structure: Why It Matters

```
kantar bls/
├── data/          → Input files (CSV)
├── scripts/       → Analysis code
├── output/        → Generated reports
└── docs/          → Documentation
```

**Benefits**:
- ✅ Clear separation of concerns
- ✅ Easy to find things
- ✅ Can ignore output/ in version control
- ✅ Scales as project grows

**Path Resolution**:
- Scripts automatically find `../data/` relative to their location
- Works whether run from root or scripts directory

---

## Performance Optimizations

### 1. Pre-merged File Detection
**Impact**: Saves 10-30 seconds per run (skips merge operation)

**How**: Automatically detects `bls_metrics_with_filters.csv` and uses it if available.

### 2. Chunked Loading
**Impact**: Handles files too large for memory

**How**: Loads `bls_answers.csv` in 100k-row chunks if needed.

### 3. Lazy Loading
**Impact**: Only loads what's needed

**How**: Optional files (like `bls_answers.csv`) are skipped if not present.

---

## Extensibility: How to Add New Features

### Adding a New Analysis Type

```python
# In analyze.py, add new method:
def analyze_by_campaign(self):
    """New analysis method."""
    df = self.merged_data.copy()
    # Your analysis logic here
    return results
```

### Adding a New Dimension

```python
# In _extract_dimensions(), add:
df['NEW_DIMENSION'] = df.apply(
    lambda row: extract_new_dimension(row),
    axis=1
)
```

### Customizing Channel Detection

```python
# In _extract_dimensions(), modify:
channel_keywords = {
    'TV': ['TV', 'television', 'broadcast'],
    'YourNewChannel': ['keyword1', 'keyword2'],
    # ...
}
```

---

## Common Questions

### Q: Why not use SQL for everything?

**A**: SQL is great for data extraction, but Python provides:
- Better statistical libraries (scipy, statsmodels)
- Easier visualization (matplotlib, seaborn)
- More flexible analysis (can add ML models later)
- Better for ad-hoc exploration

### Q: What if filter names change?

**A**: The keyword-based approach is flexible, but you can:
1. Update keywords in `_extract_dimensions()`
2. Add explicit mapping table (future enhancement)
3. Use filter_id mapping for 100% accuracy

### Q: Can this connect to Snowflake directly?

**A**: The structure is ready (see `_load_from_snowflake()` method), but not yet implemented. It's designed to be a drop-in replacement for CSV loading.

### Q: How do I customize for my use case?

**A**: Three main customization points:
1. **Keywords**: Adjust channel/demographic keywords
2. **Thresholds**: Tune significance levels and CV thresholds
3. **Analysis**: Add new analysis methods as needed

---

## Next Steps & Future Enhancements

### Short Term
- ✅ System is ready to use
- 🔄 Customize dimension extraction for your data
- 📊 Review initial reports and refine

### Medium Term
- 🔌 Implement Snowflake direct connection
- 📈 Add time series trend analysis
- 🎨 Customize visualizations for brand guidelines

### Long Term
- 🤖 Add ML models for attribution
- 📱 Dashboard integration (Tableau/Looker)
- 🔄 Automated weekly/biweekly reporting

---

## Key Takeaways

1. **Modular Design**: Easy to understand, test, and extend
2. **Flexible Input**: Works with various data formats
3. **Clear Output**: Reports are self-explanatory
4. **Performance**: Optimized for speed (pre-merged files, chunking)
5. **Extensible**: Ready for future enhancements

---

## Resources

- **Main Documentation**: `README.md`
- **Design Details**: `docs/DESIGN_DOCUMENTATION.md`
- **Project Structure**: `PROJECT_STRUCTURE.md`
- **Example Usage**: `scripts/example_usage.py`

---

*Use this guide to explain the system to your team. Focus on the "why" behind decisions, not just the "what".*

