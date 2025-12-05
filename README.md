# Kantar Brand Lift Survey (BLS) Analysis

This project analyzes DoorDash's Kantar Brand Lift Survey data to identify patterns in brand lift across time, channel, and demographics.

## Overview

The analysis pipeline:
1. **Ingests** BLS data from CSV files (or Snowflake)
2. **Cleans and merges** metrics, answers, filters, and filter metadata
3. **Explores trends** across time, channel, and audience segments
4. **Separates signal from noise** using statistical significance and consistency checks
5. **Generates reports** with visualizations and key findings

## Project Structure

```
kantar bls/
├── data/                          # Data files (CSV)
│   ├── bls_metrics.csv
│   ├── bls_answers.csv
│   ├── bls_metrics_with_filters.csv
│   ├── kantar_bls_filters.csv
│   ├── kantar_bls_filter_ids.csv
│   └── kantar_codebook_mapping_table*.csv
├── scripts/                        # Analysis scripts
│   ├── analyze.py                 # Main analysis module
│   ├── example_usage.py           # Example usage scripts
│   └── test.py                    # Test/exploratory scripts
├── output/                         # Generated reports and visualizations
├── docs/                           # Documentation files
├── README.md                       # This file
└── requirements.txt                # Python dependencies
```

## Data Sources

The analysis uses the following data tables (located in `data/`):

### Required Files

- `bls_metrics.csv` - Aggregate lift results (control vs exposed, percent lifted) per filter_id
- `kantar_bls_filters.csv` - Metadata describing filters (month, channel, segment)
- `kantar_bls_filter_ids.csv` - Crosswalk between filters and surveys
- `kantar_codebook_mapping_table*.csv` - Mapping to decode Q# codes in bls_answers

### Optional Files

- `bls_metrics_with_filters.csv` - **Pre-merged file** (metrics + filters). If this file exists, the analyzer will use it automatically, skipping the merge step for faster processing. This is recommended if you have a pre-merged dataset.
- `bls_answers.csv` - Raw user-level survey responses (optional, used for detailed user-level analysis)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Analysis

Run the complete analysis pipeline:

```python
import sys
from pathlib import Path

# Add scripts directory to path if running from project root
sys.path.append(str(Path(__file__).parent / "scripts"))

from analyze import KantarBLSAnalyzer

# Initialize analyzer (defaults to ../data relative to script)
analyzer = KantarBLSAnalyzer()

# Or specify custom data directory
# analyzer = KantarBLSAnalyzer(data_dir="path/to/data")

# Load data from CSV files
analyzer.load_data(use_snowflake=False)

# Clean and merge data (automatically saves merged data to data/bls_metrics_merged.csv)
analyzer.clean_and_merge(save_merged=True)

# Or load previously saved merged data to skip merge step
# analyzer.load_merged_data()

# Analyze trends
trends = analyzer.analyze_trends(group_by=['CHANNEL', 'METRIC_NAME'])

# Detect significant results
significant = analyzer.detect_significance(alpha=0.05)

# Identify patterns
patterns = analyzer.identify_patterns(min_observations=3)

# Generate comprehensive report
report_path = analyzer.generate_report(output_dir="output")
```

### Command Line

Run the script directly from the project root:

```bash
# From project root directory
python scripts/analyze.py
```

Or from the scripts directory:

```bash
cd scripts
python analyze.py
```

This will:
- Load all CSV files from `data/` directory
- Clean and merge the data
- Perform trend analysis
- Detect significant results
- Identify patterns
- Generate a report with visualizations in the `output/` directory

### Custom Analysis

```python
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "scripts"))

from analyze import KantarBLSAnalyzer

# Initialize analyzer
analyzer = KantarBLSAnalyzer()
analyzer.load_data(use_snowflake=False)
analyzer.clean_and_merge()

# Analyze specific metric
trends = analyzer.analyze_trends(
    metric_name="Unaided Brand Awareness",
    group_by=['CHANNEL', 'TIME_PERIOD']
)

# Get channel consistency
patterns = analyzer.identify_patterns()
channel_consistency = patterns['channel_consistency']

# Filter significant results
significant = analyzer.detect_significance(alpha=0.05)
sig_results = significant[significant['IS_SIGNIFICANT']]

# Find consistent signals across filters
consistent_signals = analyzer.find_consistent_signals(min_filters=3, min_lift=0.0)
print(f"Found {len(consistent_signals)} metrics with consistent signal across filters")
```

### Find Consistent Signals

To identify metrics that show consistent performance across different filters:

```bash
python scripts/find_consistent_signals.py
```

This will:
- Identify metrics that perform reliably across multiple filters/channels
- Calculate consistency scores
- Generate detailed breakdowns
- Save results to CSV files

### Enrich Metrics with Human-Readable Filter Names

To join all three tables and create enriched metrics with readable filter names:

```bash
python scripts/enrich_metrics_with_filters.py
```

This will:
- Join `bls_metrics` with `kantar_bls_filter_ids` and `kantar_bls_filters` on `FILTER_ID`
- Create human-readable filter names like "TV - Hispanic, exposed" or "Gen Z, not exposed"
- Save enriched data to `output/bls_metrics_enriched.csv` and `data/bls_metrics_enriched.csv`

## Output

The analysis generates files in the `output/` directory:

1. **Text Report** (`kantar_bls_report_YYYYMMDD.txt`)
   - Executive summary
   - Top performing metrics
   - Channel performance
   - Signal vs noise assessment

2. **Visualizations**:
   - `lift_by_channel.png` - Average lift by channel
   - `top_metrics.png` - Top 15 metrics by average lift
   - `lift_heatmap.png` - Heatmap of lift by metric and channel

## Key Features

### Data Cleaning
- Automatically detects and uses pre-merged files (`bls_metrics_with_filters.csv`) if available
- Standardizes column names and data types
- Extracts time, channel, and demographic dimensions
- Handles missing values and edge cases
- Falls back to individual file loading and merging if pre-merged file not found

### Trend Analysis
- Aggregates lift metrics across dimensions
- Calculates mean, std dev, and counts
- Groups by channel, time period, demographics

### Signal Detection
- Statistical significance testing
- Confidence interval calculation
- Consistency checks (coefficient of variation)

### Pattern Identification
- Channel consistency analysis
- Time trend detection
- Metric performance ranking
- Signal vs noise separation

## Data Dimensions

The analysis extracts the following dimensions:

- **Channel**: TV, OTT, Social, Digital, Podcast, Radio, CTV, Other
- **Time Period**: Extracted from survey labels (may need customization)
- **Demographics**: Hispanic, Core, Age groups, Gender, Income, General

*Note: Dimension extraction uses keyword matching. You may need to adjust the extraction logic based on your specific filter naming conventions.*

## Snowflake Integration (Future)

To load data from Snowflake instead of CSV files:

```python
snowflake_config = {
    'user': 'your_user',
    'password': 'your_password',
    'account': 'your_account',
    'warehouse': 'your_warehouse',
    'database': 'marketing',
    'schema': 'kantar'
}

analyzer.load_data(use_snowflake=True, snowflake_config=snowflake_config)
```

*Note: Snowflake integration is not yet implemented. Use CSV files for now.*

## Customization

### Adjusting Channel Detection

Edit the `channel_keywords` dictionary in `_extract_dimensions()`:

```python
channel_keywords = {
    'TV': ['TV', 'television', 'broadcast'],
    'OTT': ['OTT', 'streaming', 'hulu', 'netflix'],
    # Add your custom channels...
}
```

### Adjusting Time Extraction

Modify the `_extract_dimensions()` method to extract time periods from your specific data format.

### Adding Custom Metrics

The analysis works with any metrics in the `METRIC_NAME` column. No code changes needed.

## Troubleshooting

### Memory Issues

If `data/bls_answers.csv` is too large, the script automatically uses chunking. For very large files, consider:
- Filtering data before loading
- Using Snowflake for on-demand queries
- Processing in batches

### Import Errors

If you get import errors when running scripts, make sure you're either:
- Running from the project root: `python scripts/analyze.py`
- Or adding the scripts directory to your Python path
- Or running from within the scripts directory: `cd scripts && python analyze.py`

### Missing Dimensions

If channels or demographics aren't being extracted correctly:
- Check the `GROUP_NAME` and `NAME` columns in your filter files
- Adjust keyword matching in `_extract_dimensions()`
- Manually add mappings for specific filter IDs

## Next Steps

1. **Refine dimension extraction** based on actual filter naming conventions
2. **Add time series analysis** for trend detection over time
3. **Implement Snowflake connectivity** for direct database queries
4. **Add dashboard export** (e.g., to Tableau, Looker)
5. **Build automated reporting** for weekly/biweekly updates

## Web UI (Streamlit)

For non-technical users, we've built an interactive web interface:

```bash
# Install Streamlit (if not already installed)
pip install streamlit

# Run the web UI
streamlit run scripts/app.py
```

The UI provides:
- 📁 One-click data loading
- 🔍 Interactive analysis
- 📊 Built-in visualizations
- 📈 Results exploration
- 📄 Report generation

See **docs/UI_GUIDE.md** for detailed instructions.

## Documentation

- **README.md** (this file) - Quick start guide
- **PROJECT_STRUCTURE.md** - Directory organization
- **docs/DESIGN_DOCUMENTATION.md** - Detailed design decisions and architecture
- **docs/TEAM_PRESENTATION.md** - Presentation guide for team meetings
- **docs/UI_GUIDE.md** - Web UI usage guide
- **docs/RESULTS_INTERPRETATION.md** - How to interpret and use the analysis results
- **docs/STANDUP_REPORT.md** - Current status and findings summary
- **docs/MEDIA_CHANNELS.md** - Media channels used in brand marketing campaigns
- **docs/TIME_EXTRACTION.md** - How time periods are extracted and parsed from filter names
- **docs/SAVED_DATA.md** - How saved merged data works and how to use it
- **docs/CONSISTENT_SIGNALS.md** - How to find consistent signals across filters and metrics
- **docs/ENRICHMENT_SCRIPT.md** - How to enrich metrics with human-readable filter names

## Support

For questions or issues, contact the DoorDash Brand Measurement Team.

