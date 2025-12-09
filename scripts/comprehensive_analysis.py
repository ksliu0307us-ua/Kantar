"""
Comprehensive Kantar BLS Analysis - From Scratch

This script performs a complete analysis using ALL available data sources:
- kantar_bls_transformed_data.csv (primary - has extracted time fields)
- bls_metrics.csv
- kantar_bls_filter_ids.csv
- kantar_bls_filters.csv
- bls_answers.csv (optional)

Tasks:
1. Load and inspect all data
2. Validate dataset structure
3. Clean and standardize
4. Time-series analysis (month-over-month trends)
5. Signal vs Noise evaluation (using month-over-month variation)
6. Filter-level insights (channels, demos)
7. Export all outputs
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import sys
from typing import Optional, Dict, List
import warnings
warnings.filterwarnings('ignore')

# Add scripts directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)


class ComprehensiveBLSAnalyzer:
    """Comprehensive analyzer using all available data sources."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize analyzer."""
        if data_dir is None:
            data_dir = script_dir.parent / "data"
        self.data_dir = Path(data_dir)
        self.output_dir = script_dir.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        self.transformed_data = None
        self.metrics = None
        self.filter_ids = None
        self.filters = None
        self.answers = None
        self.merged_data = None
        
    def load_all_data(self):
        """Load all available data sources."""
        print("=" * 80)
        print("TASK 1: LOADING AND INSPECTING ALL DATA")
        print("=" * 80)
        print()
        
        # 1. Load transformed data (primary source with extracted time fields)
        transformed_file = self.data_dir / "kantar_bls_transformed_data.csv"
        if transformed_file.exists():
            print(f"Loading transformed data: {transformed_file.name}")
            self.transformed_data = pd.read_csv(transformed_file, low_memory=False)
            print(f"  ✓ Loaded {len(self.transformed_data):,} rows")
            print(f"  Columns: {list(self.transformed_data.columns)}")
            print()
        else:
            print(f"  ⚠ Warning: {transformed_file.name} not found")
            print()
        
        # 2. Load main metrics table
        metrics_file = self.data_dir / "bls_metrics.csv"
        if metrics_file.exists():
            print(f"Loading metrics: {metrics_file.name}")
            self.metrics = pd.read_csv(metrics_file, low_memory=False)
            print(f"  ✓ Loaded {len(self.metrics):,} rows")
            print()
        else:
            print(f"  ⚠ Warning: {metrics_file.name} not found")
            print()
        
        # 3. Load filter_ids
        filter_ids_file = self.data_dir / "kantar_bls_filter_ids.csv"
        if filter_ids_file.exists():
            print(f"Loading filter IDs: {filter_ids_file.name}")
            self.filter_ids = pd.read_csv(filter_ids_file, low_memory=False)
            print(f"  ✓ Loaded {len(self.filter_ids):,} rows")
            print()
        else:
            print(f"  ⚠ Warning: {filter_ids_file.name} not found")
            print()
        
        # 4. Load filters
        filters_file = self.data_dir / "kantar_bls_filters.csv"
        if filters_file.exists():
            print(f"Loading filters: {filters_file.name}")
            self.filters = pd.read_csv(filters_file, low_memory=False)
            print(f"  ✓ Loaded {len(self.filters):,} rows")
            print()
        else:
            print(f"  ⚠ Warning: {filters_file.name} not found")
            print()
        
        # 5. Load answers (optional, may be large)
        answers_file = self.data_dir / "bls_answers.csv"
        if answers_file.exists():
            print(f"Loading answers: {answers_file.name}")
            try:
                self.answers = pd.read_csv(answers_file, low_memory=False, nrows=10000)  # Sample for now
                print(f"  ✓ Loaded {len(self.answers):,} rows (sampled)")
                print()
            except Exception as e:
                print(f"  ⚠ Could not load answers: {str(e)}")
                self.answers = None
                print()
        else:
            print(f"  ℹ Note: {answers_file.name} not found (optional)")
            print()
        
        # Display data summary
        print("DATA SUMMARY")
        print("-" * 80)
        if self.transformed_data is not None:
            print(f"Transformed Data: {len(self.transformed_data):,} rows, {len(self.transformed_data.columns)} columns")
            print(f"  First 5 rows:")
            print(self.transformed_data.head())
            print()
            # In transformed data, metrics are FOLDER_NAME + FILTER combinations
            if 'FOLDER_NAME' in self.transformed_data.columns and 'FILTER' in self.transformed_data.columns:
                unique_metrics = self.transformed_data.groupby(['FOLDER_NAME', 'FILTER']).size().shape[0]
                print(f"  Unique metric combinations (FOLDER_NAME × FILTER): {unique_metrics}")
                print(f"  Unique FOLDER_NAME categories: {self.transformed_data['FOLDER_NAME'].nunique()}")
            print(f"  Date range: {self.transformed_data['SURVEY_MONTH_START'].min() if 'SURVEY_MONTH_START' in self.transformed_data.columns else 'N/A'} to {self.transformed_data['SURVEY_MONTH_END'].max() if 'SURVEY_MONTH_END' in self.transformed_data.columns else 'N/A'}")
        print()
    
    def validate_structure(self):
        """Validate dataset structure."""
        print("=" * 80)
        print("TASK 2: VALIDATING DATASET STRUCTURE")
        print("=" * 80)
        print()
        
        if self.transformed_data is None:
            print("  ⚠ Error: No transformed data available")
            return False
        
        df = self.transformed_data.copy()
        
        # Check required columns (for transformed data structure)
        required_cols = {
            'timestamp': ['SURVEY_MONTH_START', 'SURVEY_MONTH_END', 'SURVEY_MONTH', 'start', 'end', 'month', 'TIMESTAMP', 'TIME_DATE', 'TIME_PERIOD'],
            'metrics': ['EXPOSED_', 'CONTROL_', 'exposed_pct', 'EXPOSED_PERCENT', 'control_pct', 'CONTROL_PERCENT'],
            'lift': ['LIFT', 'lift', 'DELTA', 'delta'],
            'counts': ['EXPOSED_N', 'CONTROL_N', 'exposed_count', 'EXPOSED_POPULATION', 'control_count', 'CONTROL_POPULATION'],
            'filters': ['FOLDER_NAME', 'FILTER', 'WEIGHT_SET', 'EXPOSED_FILTER', 'filter_name', 'FILTER_NAME', 'channel', 'CHANNEL', 'GROUP_NAME', 'NAME']
        }
        
        found_cols = {}
        for category, possible_names in required_cols.items():
            found = [col for col in df.columns if col in possible_names]
            found_cols[category] = found[0] if found else None
        
        print("Column Validation:")
        print("-" * 80)
        all_present = True
        for category, col_name in found_cols.items():
            status = "✓" if col_name else "✗"
            print(f"  {status} {category}: {col_name if col_name else 'NOT FOUND'}")
            if not col_name:
                all_present = False
        
        print()
        
        # Check data grain
        print("Data Grain Analysis:")
        print("-" * 80)
        if found_cols['timestamp']:
            # For transformed data, metric is FOLDER_NAME + FILTER
            grain_cols = [found_cols['timestamp']]
            if 'FOLDER_NAME' in df.columns and 'FILTER' in df.columns:
                grain_cols.extend(['FOLDER_NAME', 'FILTER'])
            elif 'METRIC' in df.columns:
                grain_cols.append('METRIC')
            elif 'METRIC_NAME' in df.columns:
                grain_cols.append('METRIC_NAME')
            
            if found_cols['filters']:
                grain_cols.append(found_cols['filters'])
            
            unique_combinations = df[grain_cols].drop_duplicates()
            print(f"  Unique combinations: {len(unique_combinations):,}")
            grain_desc = " × ".join(grain_cols)
            print(f"  Grain: {grain_desc}")
            print(f"  Total rows: {len(df):,}")
            print(f"  Average rows per combination: {len(df) / len(unique_combinations):.1f}")
        
        print()
        print("Validation Result:")
        print("-" * 80)
        if all_present:
            print("  ✓ Dataset structure is valid for analysis")
        else:
            print("  ⚠ Some required columns missing - may need transformations")
        
        print()
        return all_present
    
    def clean_and_standardize(self):
        """Clean and standardize data."""
        print("=" * 80)
        print("TASK 3: CLEANING AND STANDARDIZING DATA")
        print("=" * 80)
        print()
        
        if self.transformed_data is None:
            print("  ⚠ Error: No transformed data available")
            return None
        
        df = self.transformed_data.copy()
        
        # Standardize column names (snake_case)
        print("Standardizing column names...")
        column_mapping = {}
        for col in df.columns:
            # Convert to snake_case if needed
            new_col = col.lower().replace(' ', '_').replace('-', '_')
            if new_col != col.lower():
                column_mapping[col] = new_col
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
            print(f"  Renamed {len(column_mapping)} columns")
        
        # Convert timestamps to datetime
        print("Converting timestamps...")
        time_cols = ['start', 'end', 'month', 'timestamp', 'time_date', 'time_period']
        for col in time_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    print(f"  ✓ Converted {col} to datetime")
                except:
                    pass
        
        # Use SURVEY_MONTH_START as primary timestamp if available (transformed data)
        if 'SURVEY_MONTH_START' in df.columns:
            df['timestamp'] = pd.to_datetime(df['SURVEY_MONTH_START'], errors='coerce')
        elif 'SURVEY_MONTH' in df.columns:
            df['timestamp'] = pd.to_datetime(df['SURVEY_MONTH'], errors='coerce')
        elif 'start' in df.columns:
            df['timestamp'] = df['start']
        elif 'month' in df.columns:
            df['timestamp'] = df['month']
        elif 'time_date' in df.columns:
            df['timestamp'] = df['time_date']
        
        # Create metric name from FOLDER_NAME + FILTER if needed
        if 'FOLDER_NAME' in df.columns and 'FILTER' in df.columns:
            df['METRIC_NAME'] = df['FOLDER_NAME'] + ' - ' + df['FILTER'].astype(str)
        elif 'METRIC' in df.columns:
            df['METRIC_NAME'] = df['METRIC']
        elif 'metric_name' in df.columns:
            df['METRIC_NAME'] = df['metric_name']
        
        # Convert percentages to numeric
        print("Converting percentages to numeric...")
        pct_cols = [col for col in df.columns if 'pct' in col.lower() or 'percent' in col.lower() or col in ['EXPOSED_', 'CONTROL_', 'LIFT', 'DELTA', 'exposed_', 'control_', 'lift', 'delta']]
        for col in pct_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                print(f"  ✓ Converted {col} to numeric")
        
        # Extract channel from WEIGHT_SET or EXPOSED_FILTER
        if 'WEIGHT_SET' in df.columns or 'EXPOSED_FILTER' in df.columns:
            print("Extracting channel information...")
            def extract_channel(row):
                text = str(row.get('WEIGHT_SET', '')) + ' ' + str(row.get('EXPOSED_FILTER', ''))
                import re
                # Pattern: "XM: N. Channel" or "XM: Channel"
                patterns = [
                    r'XM:\s*\d+\.\s*(\w+)',  # "XM: 2. Social"
                    r'XM:\s*(\w+)',  # "XM: Social"
                ]
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        channel = match.group(1).strip()
                        if channel.lower() in ['any', 'all']:
                            return "Any"
                        if channel.lower().startswith('digital'):
                            return "Digital"
                        return channel.title()
                return "Other"
            
            df['CHANNEL'] = df.apply(extract_channel, axis=1)
            print(f"  ✓ Extracted channels: {df['CHANNEL'].value_counts().to_dict()}")
        
        # Handle missing values
        print("Handling missing values...")
        before = len(df)
        # Drop rows with missing critical fields
        critical_cols = ['timestamp', 'METRIC' if 'METRIC' in df.columns else 'metric_name']
        df = df.dropna(subset=[col for col in critical_cols if col in df.columns])
        after = len(df)
        print(f"  Removed {before - after:,} rows with missing critical data")
        
        # Create unique key
        print("Creating unique key...")
        key_parts = ['timestamp', 'METRIC_NAME']
        if 'CHANNEL' in df.columns:
            key_parts.append('CHANNEL')
        elif 'filter_name' in df.columns:
            key_parts.append('filter_name')
        
        if len(key_parts) > 1:
            df['unique_key'] = df[key_parts].apply(lambda x: '_'.join(x.astype(str)), axis=1)
            print(f"  ✓ Created unique key: {' × '.join(key_parts)}")
        
        print()
        print(f"Cleaned data: {len(df):,} rows, {len(df.columns)} columns")
        print()
        
        self.merged_data = df
        return df
    
    def time_series_analysis(self):
        """Perform time-series analysis for each metric."""
        print("=" * 80)
        print("TASK 4: TIME-SERIES ANALYSIS")
        print("=" * 80)
        print()
        
        if self.merged_data is None:
            print("  ⚠ Error: Data not cleaned. Run clean_and_standardize() first.")
            return None
        
        df = self.merged_data.copy()
        
        # Identify metric and timestamp columns
        metric_col = 'METRIC_NAME' if 'METRIC_NAME' in df.columns else ('METRIC' if 'METRIC' in df.columns else ('metric_name' if 'metric_name' in df.columns else None))
        time_col = 'timestamp' if 'timestamp' in df.columns else None
        lift_col = 'LIFT' if 'LIFT' in df.columns else ('lift' if 'lift' in df.columns else None)
        
        if not all([metric_col, time_col, lift_col]):
            print(f"  ⚠ Error: Missing required columns. Metric: {metric_col}, Time: {time_col}, Lift: {lift_col}")
            return None
        
        print(f"Analyzing time series for {df[metric_col].nunique()} metrics...")
        print()
        
        # Group by metric and time
        ts_data = df.groupby([time_col, metric_col]).agg({
            lift_col: ['mean', 'std', 'count', 'min', 'max'],
        }).reset_index()
        
        ts_data.columns = [time_col, metric_col, 'lift_mean', 'lift_std', 'lift_count', 'lift_min', 'lift_max']
        
        # Calculate month-over-month changes
        print("Computing month-over-month trends...")
        ts_data = ts_data.sort_values([metric_col, time_col])
        ts_data['mom_change'] = ts_data.groupby(metric_col)['lift_mean'].diff()
        ts_data['mom_pct_change'] = ts_data.groupby(metric_col)['lift_mean'].pct_change() * 100
        
        # Calculate stability metrics
        print("Computing stability metrics...")
        stability = ts_data.groupby(metric_col).agg({
            'lift_mean': ['mean', 'std'],
            'lift_std': 'mean',
            'mom_change': ['std', lambda x: x.abs().mean()],
            'lift_count': 'sum'
        }).reset_index()
        
        stability.columns = [
            metric_col, 'avg_lift', 'lift_std_across_time', 'avg_lift_std',
            'mom_change_std', 'avg_abs_mom_change', 'total_observations'
        ]
        
        # Coefficient of Variation (lower = more stable)
        stability['cv'] = stability['lift_std_across_time'] / stability['avg_lift'].abs().replace(0, np.nan)
        
        # Z-score normalization for stability
        stability['stability_score'] = 1 / (1 + stability['cv'].fillna(999))
        
        # Rank by stability
        stability = stability.sort_values('stability_score', ascending=False)
        
        print(f"  ✓ Analyzed {len(stability)} metrics")
        print()
        
        # Classify as signal vs noise
        stability['signal_type'] = pd.cut(
            stability['stability_score'],
            bins=[0, 0.3, 0.7, 1.0],
            labels=['Noise', 'Uncertain', 'Signal']
        )
        
        signal_count = (stability['signal_type'] == 'Signal').sum()
        noise_count = (stability['signal_type'] == 'Noise').sum()
        
        print("Signal vs Noise Classification:")
        print("-" * 80)
        print(f"  Signal (stable): {signal_count} metrics")
        print(f"  Uncertain: {(stability['signal_type'] == 'Uncertain').sum()} metrics")
        print(f"  Noise (unstable): {noise_count} metrics")
        print()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stability_file = self.output_dir / f"metric_stability_{timestamp}.csv"
        stability.to_csv(stability_file, index=False)
        print(f"  ✓ Saved stability analysis: {stability_file.name}")
        
        ts_file = self.output_dir / f"time_series_data_{timestamp}.csv"
        ts_data.to_csv(ts_file, index=False)
        print(f"  ✓ Saved time series data: {ts_file.name}")
        print()
        
        return stability, ts_data
    
    def filter_level_analysis(self):
        """Analyze by filters (channels, demos, etc.)."""
        print("=" * 80)
        print("TASK 5: FILTER-LEVEL INSIGHTS")
        print("=" * 80)
        print()
        
        if self.merged_data is None:
            print("  ⚠ Error: Data not cleaned. Run clean_and_standardize() first.")
            return None
        
        df = self.merged_data.copy()
        
        # Identify filter columns
        filter_cols = []
        for col in ['channel', 'CHANNEL', 'filter_name', 'FILTER_NAME', 'GROUP_NAME', 'demographic', 'DEMOGRAPHIC']:
            if col in df.columns:
                filter_cols.append(col)
        
        if not filter_cols:
            print("  ⚠ No filter columns found")
            return None
        
        metric_col = 'METRIC_NAME' if 'METRIC_NAME' in df.columns else ('METRIC' if 'METRIC' in df.columns else 'metric_name')
        lift_col = 'LIFT' if 'LIFT' in df.columns else ('lift' if 'lift' in df.columns else None)
        time_col = 'timestamp' if 'timestamp' in df.columns else None
        
        if metric_col not in df.columns:
            print(f"  ⚠ Error: Metric column '{metric_col}' not found. Available columns: {list(df.columns)}")
            return None
        if lift_col is None or lift_col not in df.columns:
            print(f"  ⚠ Error: Lift column not found. Available columns: {list(df.columns)}")
            return None
        
        print(f"Analyzing by filters: {', '.join(filter_cols)}")
        print()
        
        results = {}
        
        # Analyze by each filter dimension
        for filter_col in filter_cols:
            print(f"Analyzing by {filter_col}...")
            
            # Group by filter and metric
            filter_analysis = df.groupby([filter_col, metric_col]).agg({
                lift_col: ['mean', 'std', 'count'],
            }).reset_index()
            
            filter_analysis.columns = [filter_col, metric_col, 'avg_lift', 'lift_std', 'count']
            
            # Calculate stability by filter
            filter_stability = filter_analysis.groupby(filter_col).agg({
                'avg_lift': ['mean', 'std'],
                'lift_std': 'mean',
                'count': 'sum'
            }).reset_index()
            
            filter_stability.columns = [filter_col, 'avg_lift', 'lift_std_across_metrics', 'avg_metric_std', 'total_observations']
            filter_stability['cv'] = filter_stability['lift_std_across_metrics'] / filter_stability['avg_lift'].abs().replace(0, np.nan)
            filter_stability['stability_score'] = 1 / (1 + filter_stability['cv'].fillna(999))
            filter_stability = filter_stability.sort_values('stability_score', ascending=False)
            
            results[filter_col] = {
                'by_filter': filter_analysis,
                'stability': filter_stability
            }
            
            print(f"  ✓ Analyzed {filter_analysis[filter_col].nunique()} unique {filter_col} values")
            
            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filter_file = self.output_dir / f"filter_analysis_{filter_col}_{timestamp}.csv"
            filter_analysis.to_csv(filter_file, index=False)
            stability_file = self.output_dir / f"filter_stability_{filter_col}_{timestamp}.csv"
            filter_stability.to_csv(stability_file, index=False)
            print(f"  ✓ Saved results for {filter_col}")
            print()
        
        # Time series by filter (if timestamp available)
        if time_col and filter_cols:
            print("Analyzing time series trends by filter...")
            for filter_col in filter_cols[:2]:  # Limit to first 2 filters to avoid too many files
                ts_by_filter = df.groupby([time_col, filter_col, metric_col]).agg({
                    lift_col: 'mean'
                }).reset_index()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ts_file = self.output_dir / f"time_series_by_{filter_col}_{timestamp}.csv"
                ts_by_filter.to_csv(ts_file, index=False)
                print(f"  ✓ Saved time series by {filter_col}")
            print()
        
        return results
    
    def generate_visualizations(self, stability: pd.DataFrame = None, ts_data: pd.DataFrame = None):
        """Generate all visualizations."""
        print("=" * 80)
        print("GENERATING VISUALIZATIONS")
        print("=" * 80)
        print()
        
        if self.merged_data is None:
            print("  ⚠ Error: Data not available")
            return
        
        df = self.merged_data.copy()
        metric_col = 'METRIC_NAME' if 'METRIC_NAME' in df.columns else ('METRIC' if 'METRIC' in df.columns else 'metric_name')
        lift_col = 'LIFT' if 'LIFT' in df.columns else ('lift' if 'lift' in df.columns else None)
        time_col = 'timestamp' if 'timestamp' in df.columns else None
        
        # 1. Top metrics by stability
        if stability is not None and len(stability) > 0:
            print("1. Top Stable Metrics (Signal)...")
            # Find the metric column in stability dataframe
            stability_metric_col = 'METRIC_NAME' if 'METRIC_NAME' in stability.columns else ('METRIC' if 'METRIC' in stability.columns else 'metric_name')
            top_signal = stability[stability['signal_type'] == 'Signal'].head(20)
            
            fig, ax = plt.subplots(figsize=(12, 8))
            bars = ax.barh(range(len(top_signal)), top_signal['stability_score'].values)
            ax.set_yticks(range(len(top_signal)))
            ax.set_yticklabels(top_signal[stability_metric_col].values, fontsize=9)
            ax.set_xlabel('Stability Score', fontsize=12)
            ax.set_title('Top 20 Stable Metrics (Signal)', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            plt.tight_layout()
            plt.savefig(self.output_dir / 'top_stable_metrics.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  ✓ Saved: top_stable_metrics.png")
        
        # 2. Time series plots for top metrics
        if ts_data is not None and time_col:
            print("2. Time Series Plots...")
            # Find the metric column in ts_data and stability
            ts_metric_col = 'METRIC_NAME' if 'METRIC_NAME' in ts_data.columns else ('METRIC' if 'METRIC' in ts_data.columns else 'metric_name')
            if stability is not None:
                stability_metric_col = 'METRIC_NAME' if 'METRIC_NAME' in stability.columns else ('METRIC' if 'METRIC' in stability.columns else 'metric_name')
                top_metrics = stability.head(10)[stability_metric_col].values
            else:
                top_metrics = df[metric_col].value_counts().head(10).index
            
            fig, axes = plt.subplots(5, 2, figsize=(16, 20))
            axes = axes.flatten()
            
            for i, metric in enumerate(top_metrics[:10]):
                metric_ts = ts_data[ts_data[ts_metric_col] == metric].sort_values(time_col)
                if len(metric_ts) > 0:
                    ax = axes[i]
                    ax.plot(metric_ts[time_col], metric_ts['lift_mean'], marker='o', linewidth=2)
                    ax.fill_between(
                        metric_ts[time_col],
                        metric_ts['lift_mean'] - metric_ts['lift_std'].fillna(0),
                        metric_ts['lift_mean'] + metric_ts['lift_std'].fillna(0),
                        alpha=0.2
                    )
                    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
                    ax.set_title(metric[:60] + '...' if len(metric) > 60 else metric, fontsize=10)
                    ax.set_ylabel('Lift (%)', fontsize=9)
                    ax.grid(True, alpha=0.3)
                    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            plt.tight_layout()
            plt.savefig(self.output_dir / 'time_series_top_metrics.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  ✓ Saved: time_series_top_metrics.png")
        
        # 3. Signal vs Noise distribution
        if stability is not None:
            print("3. Signal vs Noise Distribution...")
            fig, ax = plt.subplots(figsize=(10, 6))
            signal_counts = stability['signal_type'].value_counts()
            colors = {'Signal': 'green', 'Uncertain': 'yellow', 'Noise': 'red'}
            bars = ax.bar(signal_counts.index, signal_counts.values, 
                         color=[colors.get(x, 'gray') for x in signal_counts.index])
            ax.set_ylabel('Number of Metrics', fontsize=12)
            ax.set_title('Signal vs Noise Classification', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom')
            plt.tight_layout()
            plt.savefig(self.output_dir / 'signal_vs_noise_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("  ✓ Saved: signal_vs_noise_distribution.png")
        
        # 4. Heatmap by channel (if available)
        if 'channel' in df.columns or 'CHANNEL' in df.columns:
            print("4. Channel Performance Heatmap...")
            channel_col = 'channel' if 'channel' in df.columns else 'CHANNEL'
            channel_metric = df.groupby([channel_col, metric_col]).agg({
                lift_col: 'mean'
            }).reset_index()
            
            pivot = channel_metric.pivot_table(
                index=metric_col,
                columns=channel_col,
                values=lift_col,
                aggfunc='mean'
            )
            
            if len(pivot) > 0 and len(pivot.columns) > 0:
                # Sort by average lift
                pivot['avg'] = pivot.mean(axis=1)
                pivot = pivot.sort_values('avg', ascending=False).drop('avg', axis=1)
                
                fig, ax = plt.subplots(figsize=(max(8, len(pivot.columns) * 1.5), max(10, len(pivot) * 0.3)))
                sns.heatmap(pivot, annot=True, fmt='.2f', cmap='RdYlGn', center=0, ax=ax,
                           cbar_kws={'label': 'Lift (%)'}, linewidths=0.5)
                ax.set_title('Lift Heatmap: Metrics by Channel', fontsize=16, fontweight='bold')
                plt.tight_layout()
                plt.savefig(self.output_dir / 'channel_heatmap.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  ✓ Saved: channel_heatmap.png")
        
        print()
    
    def export_summary_report(self, stability: pd.DataFrame = None, filter_results: Dict = None):
        """Export comprehensive summary report."""
        print("=" * 80)
        print("TASK 6: EXPORTING SUMMARY REPORT")
        print("=" * 80)
        print()
        
        report = []
        report.append("=" * 80)
        report.append("KANTAR BLS COMPREHENSIVE ANALYSIS REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        # Data Summary
        if self.merged_data is not None:
            df = self.merged_data
            report.append("DATA SUMMARY")
            report.append("-" * 80)
            report.append(f"Total Observations: {len(df):,}")
            report.append(f"Unique Metrics: {df['METRIC_NAME'].nunique() if 'METRIC_NAME' in df.columns else 'N/A'}")
            if 'timestamp' in df.columns:
                report.append(f"Time Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            report.append("")
        
        # Signal vs Noise
        if stability is not None:
            report.append("SIGNAL VS NOISE ANALYSIS")
            report.append("-" * 80)
            signal_metrics = stability[stability['signal_type'] == 'Signal']
            noise_metrics = stability[stability['signal_type'] == 'Noise']
            
            report.append(f"Signal (Stable Metrics): {len(signal_metrics)}")
            report.append(f"Noise (Unstable Metrics): {len(noise_metrics)}")
            report.append("")
            
            if len(signal_metrics) > 0:
                report.append("Top 10 Stable Metrics (Signal):")
                for i, (_, row) in enumerate(signal_metrics.head(10).iterrows(), 1):
                    metric = row['METRIC_NAME' if 'METRIC_NAME' in stability.columns else ('METRIC' if 'METRIC' in stability.columns else 'metric_name')]
                    report.append(f"  {i}. {metric}: stability={row['stability_score']:.3f}, CV={row['cv']:.2f}")
                report.append("")
        
        # Filter Analysis
        if filter_results:
            report.append("FILTER-LEVEL INSIGHTS")
            report.append("-" * 80)
            for filter_name, results in filter_results.items():
                report.append(f"\n{filter_name.upper()}:")
                stability_df = results['stability']
                report.append(f"  Unique values: {len(stability_df)}")
                report.append(f"  Top 5 by stability:")
                for i, (_, row) in enumerate(stability_df.head(5).iterrows(), 1):
                    filter_val = row[filter_name]
                    report.append(f"    {i}. {filter_val}: avg_lift={row['avg_lift']:.2f}%, stability={row['stability_score']:.3f}")
            report.append("")
        
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"comprehensive_analysis_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        print(f"✓ Report saved: {report_file.name}")
        print()
        print(report_text)
        
        return report_text


def main():
    """Main execution function."""
    print("=" * 80)
    print("KANTAR BLS COMPREHENSIVE ANALYSIS - FROM SCRATCH")
    print("Using ALL Available Data Sources")
    print("=" * 80)
    print()
    
    analyzer = ComprehensiveBLSAnalyzer()
    
    # Task 1: Load all data
    analyzer.load_all_data()
    
    # Task 2: Validate structure
    is_valid = analyzer.validate_structure()
    
    if not is_valid:
        print("  ⚠ Warning: Dataset structure validation failed, but continuing...")
        print()
    
    # Task 3: Clean and standardize
    analyzer.clean_and_standardize()
    
    # Task 4: Time series analysis
    stability, ts_data = analyzer.time_series_analysis()
    
    # Task 5: Filter-level analysis
    filter_results = analyzer.filter_level_analysis()
    
    # Generate visualizations
    analyzer.generate_visualizations(stability=stability, ts_data=ts_data)
    
    # Task 6: Export summary report
    analyzer.export_summary_report(stability=stability, filter_results=filter_results)
    
    print("=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nAll outputs saved to: {analyzer.output_dir}")


if __name__ == "__main__":
    main()

