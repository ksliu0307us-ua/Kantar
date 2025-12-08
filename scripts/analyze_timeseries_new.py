"""
Time Series Analysis for New Kantar BLS Data Format

This script analyzes brand lift metrics over time and across channels
using the new timestamp-aggregated data format from Martech team.

Data Format:
- LIMITING_FILTER contains timestamp info: "Timestamp: 3/1/25-3/31/25"
- EXPOSED_FILTER/WEIGHT_SET contains channel info: "XM: 2. Social", "XM: 3. TV", etc.
- METRIC contains the brand metric name
- LIFT, DELTA, CONTROL_, EXPOSED_ contain the lift calculations
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re
from typing import Optional, List, Dict
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class KantarBLSTimeSeriesAnalyzer:
    """Analyzer for new timestamp-aggregated Kantar BLS data."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize analyzer with data directory."""
        if data_dir is None:
            # Default to data/ directory relative to script location
            script_dir = Path(__file__).parent
            data_dir = script_dir.parent / "data"
        self.data_dir = Path(data_dir)
        self.output_dir = script_dir.parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        self.data = None
        self.processed_data = None
        
    def load_data(self, filename: str = "kantar_bls_sample_data.csv"):
        """Load data from CSV file."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        print(f"Loading data from {filepath}...")
        self.data = pd.read_csv(filepath, low_memory=False)
        print(f"  Loaded {len(self.data):,} rows")
        print(f"  Columns: {list(self.data.columns)}")
        return self.data
    
    def extract_timestamp(self, limiting_filter: str) -> Optional[str]:
        """
        Extract timestamp from LIMITING_FILTER column.
        
        Examples:
        - "Timestamp: 3/1/25-3/31/25" -> "2025-03-01"
        - "Timestamp: 2/1/25-2/28/25" -> "2025-02-01"
        - "Timestamp: 4/1/25-6/30/25" -> "2025-04-01" (quarterly, use start date)
        """
        if pd.isna(limiting_filter):
            return None
        
        limiting_filter = str(limiting_filter).strip()
        
        # Pattern: "Timestamp: M/D/YY-M/D/YY" or "Timestamp: M/D/YY - M/D/YY"
        pattern = r'Timestamp:\s*(\d{1,2})/(\d{1,2})/(\d{2,4})'
        match = re.search(pattern, limiting_filter, re.IGNORECASE)
        
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            year_str = match.group(3)
            
            # Handle 2-digit years (assume 2000s)
            if len(year_str) == 2:
                year = 2000 + int(year_str)
            else:
                year = int(year_str)
            
            try:
                # Use first day of the period as the timestamp
                date = datetime(year, month, 1)  # Use 1st of month for consistency
                return date.strftime("%Y-%m-%d")
            except ValueError:
                return None
        
        return None
    
    def extract_channel(self, exposed_filter: str, weight_set: str = None) -> str:
        """
        Extract channel from EXPOSED_FILTER or WEIGHT_SET column.
        
        Priority: WEIGHT_SET (more reliable) > EXPOSED_FILTER
        
        Examples:
        - "XM: 2. Social" -> "Social"
        - "XM: 3. TV" -> "TV"
        - "XM: 4. Digital" -> "Digital"
        - "XM: 0. ANY" -> "Any"
        - "XM Combos (Through 4/30) OLD: 0. ANY Exposed" -> Extract from WEIGHT_SET instead
        """
        # Priority 1: Try WEIGHT_SET first (more reliable for channel info)
        if weight_set and pd.notna(weight_set):
            text = str(weight_set)
            
            # Pattern: "XM: N. Channel" or "XM: Channel"
            patterns = [
                r'XM:\s*\d+\.\s*(\w+)',  # "XM: 2. Social"
                r'XM:\s*(\w+)',  # "XM: Social"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    channel = match.group(1).strip()
                    # Clean up common variations
                    if channel.lower() in ['any', 'all']:
                        return "Any"
                    # Handle "Digital ONLY" -> "Digital"
                    if channel.lower().startswith('digital'):
                        return "Digital"
                    return channel.title()
        
        # Priority 2: Try EXPOSED_FILTER
        text = str(exposed_filter) if pd.notna(exposed_filter) else ""
        
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
        
        # Check for combo filters in EXPOSED_FILTER
        if "combo" in text.lower() or "through" in text.lower():
            # Extract from combo description
            if "0. ANY" in text.upper():
                return "Any"
            elif "4. Digital" in text:
                return "Digital"
        
        return "Unknown"
    
    def process_data(self):
        """Process raw data to extract dimensions and clean."""
        if self.data is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        print("\nProcessing data...")
        df = self.data.copy()
        
        # Extract timestamp
        print("  Extracting timestamps...")
        df['TIMESTAMP'] = df['LIMITING_FILTER'].apply(self.extract_timestamp)
        df['TIMESTAMP_DATE'] = pd.to_datetime(df['TIMESTAMP'], errors='coerce')
        
        # Extract channel
        print("  Extracting channels...")
        df['CHANNEL'] = df.apply(
            lambda row: self.extract_channel(
                row.get('EXPOSED_FILTER', ''),
                row.get('WEIGHT_SET', '')
            ),
            axis=1
        )
        
        # Clean metric names
        df['METRIC_CLEAN'] = df['METRIC'].str.strip()
        
        # Filter out rows without timestamp
        before = len(df)
        df = df[df['TIMESTAMP'].notna()].copy()
        after = len(df)
        print(f"  Filtered out {before - after:,} rows without valid timestamps")
        
        # Summary
        print(f"\n  Processed data summary:")
        print(f"    Total rows: {len(df):,}")
        print(f"    Unique timestamps: {df['TIMESTAMP'].nunique()}")
        print(f"    Unique channels: {df['CHANNEL'].nunique()}")
        print(f"    Unique metrics: {df['METRIC_CLEAN'].nunique()}")
        print(f"    Date range: {df['TIMESTAMP_DATE'].min()} to {df['TIMESTAMP_DATE'].max()}")
        
        self.processed_data = df
        return df
    
    def analyze_time_series(
        self,
        metric_name: Optional[str] = None,
        channel: Optional[str] = None,
        min_observations: int = 1,
        group_by_demographic: bool = False
    ) -> pd.DataFrame:
        """
        Analyze brand lift metrics over time.
        
        Parameters:
        -----------
        metric_name : str, optional
            Filter to specific metric (e.g., "DashPass")
        channel : str, optional
            Filter to specific channel (e.g., "TV", "Social")
        min_observations : int
            Minimum number of observations per time period
        group_by_demographic : bool
            Whether to include demographic breakdowns
        """
        if self.processed_data is None:
            raise ValueError("Data not processed. Call process_data() first.")
        
        print(f"\nAnalyzing time series...")
        df = self.processed_data.copy()
        
        # Apply filters
        if metric_name:
            # Escape special regex characters to avoid warnings
            escaped_metric = re.escape(metric_name)
            df = df[df['METRIC_CLEAN'].str.contains(escaped_metric, case=False, na=False, regex=True)]
            print(f"  Filtered to metric: {metric_name}")
        
        if channel:
            df = df[df['CHANNEL'] == channel]
            print(f"  Filtered to channel: {channel}")
        
        # Group by time period
        group_cols = ['TIMESTAMP', 'TIMESTAMP_DATE', 'METRIC_CLEAN']
        if not group_by_demographic:
            # Aggregate across demographics
            pass
        else:
            # Include demographic dimensions
            if 'FOLDER_NAME' in df.columns:
                group_cols.append('FOLDER_NAME')
            if 'FILTER' in df.columns:
                group_cols.append('FILTER')
        
        # Aggregate
        agg_dict = {
            'LIFT': ['mean', 'std', 'count', 'min', 'max'],
            'DELTA': ['mean', 'std'],
            'CONTROL_': ['mean'],
            'EXPOSED_': ['mean'],
            'CONTROL_N': ['sum'],
            'EXPOSED_N': ['sum'],
        }
        
        # Add statistical significance if available
        if 'STATISTICAL_SIGNIFICANCE' in df.columns:
            agg_dict['STATISTICAL_SIGNIFICANCE'] = ['mean', 'min']
        
        time_series = df.groupby(group_cols).agg(agg_dict).reset_index()
        
        # Flatten column names
        time_series.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                              for col in time_series.columns.values]
        
        # Filter by minimum observations
        if 'LIFT_count' in time_series.columns:
            time_series = time_series[time_series['LIFT_count'] >= min_observations]
        
        # Sort by date
        time_series = time_series.sort_values('TIMESTAMP_DATE')
        
        print(f"  Generated {len(time_series):,} time series data points")
        
        return time_series
    
    def analyze_by_channel(
        self,
        metric_name: Optional[str] = None,
        min_observations: int = 3
    ) -> pd.DataFrame:
        """
        Analyze brand lift metrics by channel.
        
        Parameters:
        -----------
        metric_name : str, optional
            Filter to specific metric
        min_observations : int
            Minimum number of observations per channel
        """
        if self.processed_data is None:
            raise ValueError("Data not processed. Call process_data() first.")
        
        print(f"\nAnalyzing by channel...")
        df = self.processed_data.copy()
        
        # Apply filters
        if metric_name:
            # Escape special regex characters to avoid warnings
            escaped_metric = re.escape(metric_name)
            df = df[df['METRIC_CLEAN'].str.contains(escaped_metric, case=False, na=False, regex=True)]
            print(f"  Filtered to metric: {metric_name}")
        
        # Group by channel and metric
        group_cols = ['CHANNEL', 'METRIC_CLEAN']
        
        agg_dict = {
            'LIFT': ['mean', 'std', 'count', 'min', 'max'],
            'DELTA': ['mean', 'std'],
            'CONTROL_': ['mean'],
            'EXPOSED_': ['mean'],
            'CONTROL_N': ['sum'],
            'EXPOSED_N': ['sum'],
        }
        
        if 'STATISTICAL_SIGNIFICANCE' in df.columns:
            agg_dict['STATISTICAL_SIGNIFICANCE'] = ['mean', 'min']
        
        channel_analysis = df.groupby(group_cols).agg(agg_dict).reset_index()
        
        # Flatten column names
        channel_analysis.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                                    for col in channel_analysis.columns.values]
        
        # Filter by minimum observations
        if 'LIFT_count' in channel_analysis.columns:
            channel_analysis = channel_analysis[
                channel_analysis['LIFT_count'] >= min_observations
            ]
        
        # Sort by average lift
        channel_analysis = channel_analysis.sort_values('LIFT_mean', ascending=False)
        
        print(f"  Generated {len(channel_analysis):,} channel-metric combinations")
        
        return channel_analysis
    
    def plot_time_series(
        self,
        metric_name: str,
        channel: Optional[str] = None,
        save_path: Optional[Path] = None
    ):
        """Plot time series for a specific metric."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call process_data() first.")
        
        # Get time series data
        ts_data = self.analyze_time_series(metric_name=metric_name, channel=channel)
        
        if len(ts_data) == 0:
            print(f"No data found for metric: {metric_name}")
            return
        
        # Create plot
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Plot mean lift over time
        ax.plot(ts_data['TIMESTAMP_DATE'], ts_data['LIFT_mean'], 
                marker='o', linewidth=2, markersize=8, label='Mean Lift')
        
        # Add error bars (std)
        if 'LIFT_std' in ts_data.columns:
            ax.fill_between(
                ts_data['TIMESTAMP_DATE'],
                ts_data['LIFT_mean'] - ts_data['LIFT_std'],
                ts_data['LIFT_mean'] + ts_data['LIFT_std'],
                alpha=0.2,
                label='±1 Std Dev'
            )
        
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Lift (%)', fontsize=12)
        title = f'Brand Lift Over Time: {metric_name}'
        if channel:
            title += f' - {channel}'
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"  Saved plot to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def plot_channel_comparison(
        self,
        metric_name: str,
        save_path: Optional[Path] = None
    ):
        """Plot channel comparison for a specific metric."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call process_data() first.")
        
        # Get channel analysis data
        channel_data = self.analyze_by_channel(metric_name=metric_name, min_observations=1)
        
        if len(channel_data) == 0:
            print(f"No data found for metric: {metric_name}")
            return
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Sort by mean lift
        channel_data = channel_data.sort_values('LIFT_mean', ascending=True)
        
        # Create bar plot
        bars = ax.barh(channel_data['CHANNEL'], channel_data['LIFT_mean'])
        
        # Color bars based on lift value
        colors = ['green' if x > 0 else 'red' for x in channel_data['LIFT_mean']]
        for bar, color in zip(bars, colors):
            bar.set_color(color)
            bar.set_alpha(0.7)
        
        # Add error bars
        if 'LIFT_std' in channel_data.columns:
            ax.errorbar(
                channel_data['LIFT_mean'],
                channel_data['CHANNEL'],
                xerr=channel_data['LIFT_std'],
                fmt='none',
                color='black',
                capsize=3
            )
        
        ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Average Lift (%)', fontsize=12)
        ax.set_ylabel('Channel', fontsize=12)
        ax.set_title(f'Brand Lift by Channel: {metric_name}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"  Saved plot to {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def save_results(
        self,
        time_series_df: pd.DataFrame,
        channel_df: pd.DataFrame,
        prefix: str = "timeseries_analysis"
    ):
        """Save analysis results to CSV files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save time series
        ts_file = self.output_dir / f"{prefix}_time_series_{timestamp}.csv"
        time_series_df.to_csv(ts_file, index=False)
        print(f"  Saved time series to {ts_file}")
        
        # Save channel analysis
        channel_file = self.output_dir / f"{prefix}_channels_{timestamp}.csv"
        channel_df.to_csv(channel_file, index=False)
        print(f"  Saved channel analysis to {channel_file}")
        
        return ts_file, channel_file


def main():
    """Main execution function."""
    print("=" * 60)
    print("Kantar BLS Time Series Analysis (New Data Format)")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = KantarBLSTimeSeriesAnalyzer()
    
    # Load data
    analyzer.load_data()
    
    # Process data
    analyzer.process_data()
    
    # Get list of unique metrics
    metrics = analyzer.processed_data['METRIC_CLEAN'].unique()
    print(f"\nFound {len(metrics)} unique metrics")
    print("Sample metrics:", metrics[:10].tolist())
    
    # Get list of unique channels
    channels = analyzer.processed_data['CHANNEL'].unique()
    print(f"\nFound {len(channels)} unique channels: {channels.tolist()}")
    
    # Analyze time series for all metrics
    print("\n" + "=" * 60)
    print("Time Series Analysis - All Metrics")
    print("=" * 60)
    time_series_all = analyzer.analyze_time_series()
    print(f"\nTime series summary:")
    print(time_series_all.head(10))
    
    # Analyze by channel
    print("\n" + "=" * 60)
    print("Channel Analysis - All Metrics")
    print("=" * 60)
    channel_analysis_all = analyzer.analyze_by_channel()
    print(f"\nChannel analysis summary:")
    print(channel_analysis_all.head(10))
    
    # Example: Analyze specific metric (DashPass)
    dashpass_metrics = [m for m in metrics if 'dashpass' in m.lower()]
    if dashpass_metrics:
        print("\n" + "=" * 60)
        print(f"Example: DashPass Metrics Analysis")
        print("=" * 60)
        
        for metric in dashpass_metrics[:3]:  # Analyze first 3 DashPass metrics
            print(f"\nAnalyzing: {metric}")
            
            # Time series
            ts = analyzer.analyze_time_series(metric_name=metric)
            if len(ts) > 0:
                print(f"  Time series data points: {len(ts)}")
                print(ts[['TIMESTAMP_DATE', 'METRIC_CLEAN', 'LIFT_mean', 'LIFT_count']].head())
                
                # Plot
                plot_file = analyzer.output_dir / f"timeseries_{metric.replace('/', '_')[:50]}_{datetime.now().strftime('%Y%m%d')}.png"
                analyzer.plot_time_series(metric_name=metric, save_path=plot_file)
            
            # Channel analysis
            ch = analyzer.analyze_by_channel(metric_name=metric)
            if len(ch) > 0:
                print(f"  Channel combinations: {len(ch)}")
                print(ch[['CHANNEL', 'METRIC_CLEAN', 'LIFT_mean', 'LIFT_count']].head())
                
                # Plot
                plot_file = analyzer.output_dir / f"channels_{metric.replace('/', '_')[:50]}_{datetime.now().strftime('%Y%m%d')}.png"
                analyzer.plot_channel_comparison(metric_name=metric, save_path=plot_file)
    
    # Save all results
    print("\n" + "=" * 60)
    print("Saving Results")
    print("=" * 60)
    analyzer.save_results(time_series_all, channel_analysis_all)
    
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

