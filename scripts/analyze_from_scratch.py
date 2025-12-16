"""
Kantar BLS Analysis Pipeline - Built from Scratch
===================================================

This script analyzes Kantar Brand Lift Survey data based on the ACTUAL data structure
found in the data files. No assumptions - only uses what's actually in the data.

Data Files Used:
1. kantar_bls_sample_data.csv - Main metrics data
2. kantar_bls_filter_ids.csv - Filter metadata (GROUP_NAME, NAME, SURVEY_LABEL, etc.)
3. kantar_bls_filters.csv - Additional filter details

Data Structure (from kantar_bls_sample_data.csv):
- FILTER: Demographic/segment values (e.g., "Male", "Gender", "45-54", "Several times a week")
- METRIC: Metric names (e.g., "BA: Is an essential part of my life", "DashPass Aided Awareness")
- LIFT: Lift value (decimal, e.g., 0.17 = 17%)
- DELTA: Delta value
- EXPOSED_: Exposed percentage (decimal)
- CONTROL_: Control percentage (decimal)
- EXPOSED_N: Exposed population count
- CONTROL_N: Control population count
- LIMITING_FILTER: Timestamp info (e.g., "Timestamp: 3/1/25-3/31/25")
- EXPOSED_FILTER: Channel exposure info (e.g., "XM: 2. Social Exposed")
- WEIGHT_SET: Channel weight set (e.g., "XM: 2. Social (3/1/25 - 3/31/25)")
- FOLDER_NAME: Category/group name (e.g., "Past Brand Recency - DoorDash", "Gender", "Age")
- STATISTICAL_SIGNIFICANCE: P-value
- SID: Survey ID
- CID: Campaign ID

Join Strategy:
- Attempts multiple join strategies to link sample data with filter tables:
  1. FILTER column -> NAME column in filter_ids/filters
  2. FOLDER_NAME column -> GROUP_NAME column in filter_ids/filters
  3. SID (Survey ID) -> SURVEY_ID in filter_ids/filters
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import re
from typing import Optional
import warnings

warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class KantarBLSAnalyzer:
    """
    Analyzer for Kantar BLS data - built from actual data structure.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize analyzer.
        
        Parameters:
        -----------
        data_dir : str
            Directory containing data files
        """
        self.data_dir = Path(data_dir)
        self.data = None
        self.filter_ids = None
        self.filters = None
        self.processed_data = None
        
    def load_data(self, filename: str = "kantar_bls_sample_data.csv") -> pd.DataFrame:
        """
        Load data from CSV file and filter tables.
        
        Parameters:
        -----------
        filename : str
            Name of CSV file in data directory
            
        Returns:
        --------
        pd.DataFrame
            Loaded data
        """
        # Load main data file
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        print(f"Loading data from {filename}...")
        self.data = pd.read_csv(filepath, low_memory=False)
        print(f"✓ Loaded {len(self.data):,} rows")
        print(f"✓ Columns: {list(self.data.columns)}")
        
        # Load filter_ids table
        filter_ids_path = self.data_dir / "kantar_bls_filter_ids.csv"
        if filter_ids_path.exists():
            print(f"\nLoading kantar_bls_filter_ids.csv...")
            self.filter_ids = pd.read_csv(filter_ids_path, low_memory=False)
            print(f"✓ Loaded {len(self.filter_ids):,} rows")
            print(f"✓ Columns: {list(self.filter_ids.columns)}")
        else:
            print(f"\n⚠ kantar_bls_filter_ids.csv not found, skipping filter metadata")
            self.filter_ids = pd.DataFrame()
        
        # Load filters table
        filters_path = self.data_dir / "kantar_bls_filters.csv"
        if filters_path.exists():
            print(f"\nLoading kantar_bls_filters.csv...")
            self.filters = pd.read_csv(filters_path, low_memory=False)
            print(f"✓ Loaded {len(self.filters):,} rows")
            print(f"✓ Columns: {list(self.filters.columns)}")
        else:
            print(f"\n⚠ kantar_bls_filters.csv not found, skipping filter details")
            self.filters = pd.DataFrame()
        
        return self.data
    
    def extract_channel(self, row: pd.Series) -> str:
        """
        Extract channel from WEIGHT_SET or EXPOSED_FILTER columns.
        
        Based on actual data structure:
        - WEIGHT_SET: "XM: 0. ANY (3/1/25 - 3/31/25)" -> "ANY"
        - WEIGHT_SET: "XM: 2. Social (3/1/25 - 3/31/25)" -> "Social"
        - WEIGHT_SET: "XM: 3. TV (3/1/25 - 3/31/25)" -> "TV"
        - WEIGHT_SET: "XM: 4. Digital ONLY (2/1/25-2/28/25)" -> "Digital"
        """
        # Try WEIGHT_SET first (more reliable)
        if pd.notna(row.get('WEIGHT_SET')):
            weight_set = str(row['WEIGHT_SET'])
            # Pattern: "XM: N. Channel Name" or "XM: N. Channel Name ONLY"
            match = re.search(r'XM:\s*\d+\.\s*([^\(]+)', weight_set)
            if match:
                channel = match.group(1).strip()
                # Remove "ONLY" suffix if present
                channel = channel.replace(' ONLY', '').strip()
                return channel
        
        # Fallback to EXPOSED_FILTER
        if pd.notna(row.get('EXPOSED_FILTER')):
            exposed_filter = str(row['EXPOSED_FILTER'])
            # Pattern: "XM: N. Channel Exposed" or "XM Combos...: N. Channel Exposed"
            match = re.search(r'XM[^:]*:\s*\d+\.\s*([^:]+?)(?:\s+Exposed|$)', exposed_filter)
            if match:
                channel = match.group(1).strip()
                return channel
        
        return "Unknown"
    
    def extract_timestamp(self, limiting_filter: str) -> Optional[str]:
        """
        Extract timestamp from LIMITING_FILTER column.
        
        Based on actual data:
        - "Timestamp: 3/1/25-3/31/25" -> "2025-03-01"
        - "Timestamp: 2/1/25-2/28/25" -> "2025-02-01"
        - "Timestamp: 4/1/25-6/30/25" -> "2025-04-01" (quarterly, use start date)
        """
        if pd.isna(limiting_filter):
            return None
        
        limiting_filter = str(limiting_filter).strip()
        
        # Pattern: "Timestamp: M/D/YY-M/D/YY"
        pattern = r'Timestamp:\s*(\d{1,2})/(\d{1,2})/(\d{2,4})'
        match = re.search(pattern, limiting_filter, re.IGNORECASE)
        
        if match:
            month = int(match.group(1))
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
    
    def merge_with_filter_tables(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Merge data with filter_ids and filters tables to get additional metadata.
        
        Tries multiple join strategies:
        1. FILTER column -> NAME column in filter_ids/filters
        2. FOLDER_NAME column -> GROUP_NAME column in filter_ids/filters
        3. SID (Survey ID) -> SURVEY_ID in filter_ids/filters
        
        Parameters:
        -----------
        df : pd.DataFrame
            Data to merge
            
        Returns:
        --------
        pd.DataFrame
            Merged data with filter metadata
        """
        merged = df.copy()
        
        if self.filter_ids.empty and self.filters.empty:
            print("  ⚠ No filter tables available, skipping merge")
            return merged
        
        print("\n  Merging with filter tables...")
        
        # Strategy 1: Join on FILTER -> NAME
        if not self.filter_ids.empty and 'NAME' in self.filter_ids.columns and 'FILTER' in merged.columns:
            print("    Attempting join: FILTER -> NAME (filter_ids)...")
            filter_id_cols = ['NAME']
            for col in ['FILTER_ID', 'GROUP_NAME', 'SURVEY_ID', 'SURVEY_LABEL']:
                if col in self.filter_ids.columns:
                    filter_id_cols.append(col)
            
            filter_ids_for_join = self.filter_ids[filter_id_cols].copy()
            filter_ids_for_join = filter_ids_for_join.rename(columns={'NAME': 'FILTER'})
            filter_ids_for_join = filter_ids_for_join.drop_duplicates(subset=['FILTER'])
            
            # Check for matches
            sample_filters = set(merged['FILTER'].dropna().unique()[:50])
            filter_names = set(filter_ids_for_join['FILTER'].dropna().unique()[:100])
            matches = sample_filters.intersection(filter_names)
            
            if len(matches) > 0:
                print(f"    ✓ Found {len(matches)} matching FILTER values")
                merged = merged.merge(
                    filter_ids_for_join,
                    on='FILTER',
                    how='left',
                    suffixes=('', '_filter_ids')
                )
            else:
                print(f"    ⚠ No matches found for FILTER->NAME join")
        
        # Strategy 2: Join on FOLDER_NAME -> GROUP_NAME
        if not self.filter_ids.empty and 'GROUP_NAME' in self.filter_ids.columns and 'FOLDER_NAME' in merged.columns:
            print("    Attempting join: FOLDER_NAME -> GROUP_NAME (filter_ids)...")
            filter_id_cols = ['GROUP_NAME']
            for col in ['FILTER_ID', 'NAME', 'SURVEY_ID', 'SURVEY_LABEL']:
                if col in self.filter_ids.columns and col not in merged.columns:
                    filter_id_cols.append(col)
            
            filter_ids_for_join = self.filter_ids[filter_id_cols].copy()
            filter_ids_for_join = filter_ids_for_join.rename(columns={'GROUP_NAME': 'FOLDER_NAME'})
            filter_ids_for_join = filter_ids_for_join.drop_duplicates(subset=['FOLDER_NAME'])
            
            # Check for matches
            sample_folders = set(merged['FOLDER_NAME'].dropna().unique()[:50])
            group_names = set(filter_ids_for_join['FOLDER_NAME'].dropna().unique()[:100])
            matches = sample_folders.intersection(group_names)
            
            if len(matches) > 0:
                print(f"    ✓ Found {len(matches)} matching FOLDER_NAME values")
                merged = merged.merge(
                    filter_ids_for_join,
                    on='FOLDER_NAME',
                    how='left',
                    suffixes=('', '_filter_ids_group')
                )
            else:
                print(f"    ⚠ No matches found for FOLDER_NAME->GROUP_NAME join")
        
        # Strategy 3: Join on SID -> SURVEY_ID
        if not self.filter_ids.empty and 'SURVEY_ID' in self.filter_ids.columns and 'SID' in merged.columns:
            print("    Attempting join: SID -> SURVEY_ID (filter_ids)...")
            filter_id_cols = ['SURVEY_ID']
            for col in ['FILTER_ID', 'GROUP_NAME', 'NAME', 'SURVEY_LABEL']:
                if col in self.filter_ids.columns:
                    filter_id_cols.append(col)
            
            # Get unique survey metadata
            survey_metadata = self.filter_ids[filter_id_cols].drop_duplicates(subset=['SURVEY_ID'])
            survey_metadata = survey_metadata.rename(columns={'SURVEY_ID': 'SID'})
            
            merged = merged.merge(
                survey_metadata,
                on='SID',
                how='left',
                suffixes=('', '_filter_ids_survey')
            )
            print(f"    ✓ Merged survey metadata")
        
        # Also merge with filters table (similar strategies)
        if not self.filters.empty:
            print("    Merging with kantar_bls_filters...")
            if 'NAME' in self.filters.columns and 'FILTER' in merged.columns:
                filter_cols = ['NAME']
                for col in ['ID', 'GROUP_NAME', 'SURVEY_ID']:
                    if col in self.filters.columns:
                        filter_cols.append(col)
                
                filters_for_join = self.filters[filter_cols].copy()
                filters_for_join = filters_for_join.rename(columns={'NAME': 'FILTER', 'ID': 'FILTER_ID'})
                filters_for_join = filters_for_join.drop_duplicates(subset=['FILTER'])
                
                merged = merged.merge(
                    filters_for_join,
                    on='FILTER',
                    how='left',
                    suffixes=('', '_filters')
                )
                print(f"    ✓ Merged with filters table")
        
        # Consolidate duplicate columns
        # Prefer values from filters table, then filter_ids
        if 'GROUP_NAME_filters' in merged.columns:
            merged['GROUP_NAME'] = merged['GROUP_NAME_filters'].fillna(merged.get('GROUP_NAME', ''))
            merged = merged.drop(columns=['GROUP_NAME_filters'], errors='ignore')
        elif 'GROUP_NAME' not in merged.columns and 'GROUP_NAME_filter_ids' in merged.columns:
            merged['GROUP_NAME'] = merged['GROUP_NAME_filter_ids']
        
        if 'SURVEY_LABEL' not in merged.columns and 'SURVEY_LABEL_filter_ids' in merged.columns:
            merged['SURVEY_LABEL'] = merged['SURVEY_LABEL_filter_ids']
        
        print(f"  ✓ Merged data: {len(merged):,} rows")
        print(f"  ✓ New columns added: {set(merged.columns) - set(df.columns)}")
        
        return merged
    
    def process_data(self) -> pd.DataFrame:
        """
        Process raw data to extract dimensions and prepare for analysis.
        
        Extracts:
        - Channel from WEIGHT_SET/EXPOSED_FILTER
        - Timestamp from LIMITING_FILTER
        - Merges with filter tables to get metadata (GROUP_NAME, SURVEY_LABEL, etc.)
        - Keeps all original columns
        """
        if self.data is None:
            raise ValueError("Must load data first using load_data()")
        
        print("\nProcessing data...")
        processed = self.data.copy()
        
        # Extract channel
        print("  Extracting channels from WEIGHT_SET/EXPOSED_FILTER...")
        processed['CHANNEL'] = processed.apply(self.extract_channel, axis=1)
        channel_counts = processed['CHANNEL'].value_counts()
        print(f"  ✓ Found {len(channel_counts)} unique channels: {dict(channel_counts.head(10))}")
        
        # Extract timestamp
        print("  Extracting timestamps from LIMITING_FILTER...")
        processed['TIMESTAMP'] = processed['LIMITING_FILTER'].apply(self.extract_timestamp)
        processed['TIMESTAMP_DATE'] = pd.to_datetime(processed['TIMESTAMP'], errors='coerce')
        
        timestamp_counts = processed['TIMESTAMP'].value_counts()
        print(f"  ✓ Found {len(timestamp_counts)} unique timestamps: {dict(timestamp_counts)}")
        
        # Merge with filter tables
        processed = self.merge_with_filter_tables(processed)
        
        # Ensure numeric columns are numeric
        numeric_cols = ['LIFT', 'DELTA', 'EXPOSED_', 'CONTROL_', 'EXPOSED_N', 'CONTROL_N', 'STATISTICAL_SIGNIFICANCE']
        for col in numeric_cols:
            if col in processed.columns:
                processed[col] = pd.to_numeric(processed[col], errors='coerce')
        
        self.processed_data = processed
        print(f"✓ Processed {len(processed):,} rows")
        
        return processed
    
    def analyze_by_channel(self, metric_name: Optional[str] = None) -> pd.DataFrame:
        """
        Analyze lift by channel.
        
        Parameters:
        -----------
        metric_name : str, optional
            Filter to specific metric (partial match)
            
        Returns:
        --------
        pd.DataFrame
            Aggregated results by channel
        """
        if self.processed_data is None:
            raise ValueError("Must process data first using process_data()")
        
        df = self.processed_data.copy()
        
        # Filter by metric if specified
        if metric_name:
            df = df[df['METRIC'].str.contains(metric_name, case=False, na=False)]
        
        # Group by channel and metric
        grouped = df.groupby(['CHANNEL', 'METRIC']).agg({
            'LIFT': ['mean', 'std', 'count'],
            'DELTA': 'mean',
            'EXPOSED_N': 'sum',
            'CONTROL_N': 'sum',
            'STATISTICAL_SIGNIFICANCE': 'mean'
        }).reset_index()
        
        # Flatten column names
        grouped.columns = ['CHANNEL', 'METRIC', 'LIFT_MEAN', 'LIFT_STD', 'LIFT_COUNT', 
                          'DELTA_MEAN', 'EXPOSED_N_SUM', 'CONTROL_N_SUM', 'SIGNIFICANCE_MEAN']
        
        # Calculate total sample size
        grouped['TOTAL_N'] = grouped['EXPOSED_N_SUM'] + grouped['CONTROL_N_SUM']
        
        # Sort by average lift
        grouped = grouped.sort_values('LIFT_MEAN', ascending=False)
        
        return grouped
    
    def analyze_time_series(self, metric_name: Optional[str] = None, 
                           channel: Optional[str] = None) -> pd.DataFrame:
        """
        Analyze lift over time.
        
        Parameters:
        -----------
        metric_name : str, optional
            Filter to specific metric (partial match)
        channel : str, optional
            Filter to specific channel
            
        Returns:
        --------
        pd.DataFrame
            Aggregated results by time period
        """
        if self.processed_data is None:
            raise ValueError("Must process data first using process_data()")
        
        df = self.processed_data.copy()
        
        # Filter by metric if specified
        if metric_name:
            df = df[df['METRIC'].str.contains(metric_name, case=False, na=False)]
        
        # Filter by channel if specified
        if channel:
            df = df[df['CHANNEL'] == channel]
        
        # Remove rows without timestamps
        df = df[df['TIMESTAMP'].notna()]
        
        # Group by timestamp and metric
        grouped = df.groupby(['TIMESTAMP', 'TIMESTAMP_DATE', 'METRIC']).agg({
            'LIFT': ['mean', 'std', 'count'],
            'DELTA': 'mean',
            'EXPOSED_N': 'sum',
            'CONTROL_N': 'sum',
            'STATISTICAL_SIGNIFICANCE': 'mean'
        }).reset_index()
        
        # Flatten column names
        grouped.columns = ['TIMESTAMP', 'TIMESTAMP_DATE', 'METRIC', 'LIFT_MEAN', 'LIFT_STD', 
                          'LIFT_COUNT', 'DELTA_MEAN', 'EXPOSED_N_SUM', 'CONTROL_N_SUM', 
                          'SIGNIFICANCE_MEAN']
        
        # Calculate total sample size
        grouped['TOTAL_N'] = grouped['EXPOSED_N_SUM'] + grouped['CONTROL_N_SUM']
        
        # Sort by timestamp
        grouped = grouped.sort_values('TIMESTAMP_DATE')
        
        return grouped
    
    def detect_significance(self, alpha: float = 0.05) -> pd.DataFrame:
        """
        Detect statistically significant results.
        
        Parameters:
        -----------
        alpha : float
            Significance threshold (default 0.05)
            
        Returns:
        --------
        pd.DataFrame
            Data with significance flag
        """
        if self.processed_data is None:
            raise ValueError("Must process data first using process_data()")
        
        df = self.processed_data.copy()
        
        # Mark as significant if p-value < alpha
        df['IS_SIGNIFICANT'] = (df['STATISTICAL_SIGNIFICANCE'] < alpha) & (df['STATISTICAL_SIGNIFICANCE'].notna())
        
        # Also mark as significant if lift is substantial (heuristic)
        # LIFT is stored as decimal (0.20 = 20%), so threshold is 0.05 (5%)
        df['IS_SUBSTANTIAL'] = (df['LIFT'].abs() > 0.05) & (df['LIFT'].notna())
        
        return df
    
    def find_top_metrics(self, min_observations: int = 3, 
                        min_lift: float = 0.0) -> pd.DataFrame:
        """
        Find top performing metrics.
        
        Parameters:
        -----------
        min_observations : int
            Minimum number of observations required
        min_lift : float
            Minimum average lift (as decimal, e.g., 0.05 = 5%)
            
        Returns:
        --------
        pd.DataFrame
            Top metrics with aggregated statistics
        """
        if self.processed_data is None:
            raise ValueError("Must process data first using process_data()")
        
        df = self.processed_data.copy()
        
        # Group by metric
        grouped = df.groupby('METRIC').agg({
            'LIFT': ['mean', 'std', 'count'],
            'DELTA': 'mean',
            'EXPOSED_N': 'sum',
            'CONTROL_N': 'sum',
            'STATISTICAL_SIGNIFICANCE': lambda x: (x < 0.05).sum()  # Count significant
        }).reset_index()
        
        # Flatten column names
        grouped.columns = ['METRIC', 'LIFT_MEAN', 'LIFT_STD', 'OBSERVATIONS', 
                          'DELTA_MEAN', 'EXPOSED_N_SUM', 'CONTROL_N_SUM', 'SIGNIFICANT_COUNT']
        
        # Filter by minimum observations and lift
        grouped = grouped[
            (grouped['OBSERVATIONS'] >= min_observations) &
            (grouped['LIFT_MEAN'].abs() >= min_lift)
        ]
        
        # Calculate total sample size
        grouped['TOTAL_N'] = grouped['EXPOSED_N_SUM'] + grouped['CONTROL_N_SUM']
        
        # Sort by average lift
        grouped = grouped.sort_values('LIFT_MEAN', ascending=False)
        
        return grouped
    
    def plot_channel_comparison(self, metric_name: str, 
                               save_path: Optional[Path] = None):
        """
        Plot channel comparison for a specific metric.
        
        Parameters:
        -----------
        metric_name : str
            Metric name to plot
        save_path : Path, optional
            Path to save the plot
        """
        channel_data = self.analyze_by_channel(metric_name=metric_name)
        
        if len(channel_data) == 0:
            print(f"No data found for metric: {metric_name}")
            return
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Sort by mean lift
        channel_data = channel_data.sort_values('LIFT_MEAN', ascending=True)
        
        # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
        bars = ax.barh(channel_data['CHANNEL'], channel_data['LIFT_MEAN'] * 100)
        
        # Color bars based on lift value
        colors = ['green' if x > 0 else 'red' for x in channel_data['LIFT_MEAN']]
        for bar, color in zip(bars, colors):
            bar.set_color(color)
            bar.set_alpha(0.7)
        
        # Add error bars (std)
        if 'LIFT_STD' in channel_data.columns:
            ax.errorbar(
                channel_data['LIFT_MEAN'] * 100,
                channel_data['CHANNEL'],
                xerr=channel_data['LIFT_STD'] * 100,
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
    
    def plot_time_series(self, metric_name: str, channel: Optional[str] = None,
                        save_path: Optional[Path] = None):
        """
        Plot time series for a specific metric.
        
        Parameters:
        -----------
        metric_name : str
            Metric name to plot
        channel : str, optional
            Filter to specific channel
        save_path : Path, optional
            Path to save the plot
        """
        ts_data = self.analyze_time_series(metric_name=metric_name, channel=channel)
        
        if len(ts_data) == 0:
            print(f"No data found for metric: {metric_name}")
            return
        
        # Create plot
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Sort by timestamp
        ts_data = ts_data.sort_values('TIMESTAMP_DATE')
        
        # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
        ax.plot(ts_data['TIMESTAMP_DATE'], ts_data['LIFT_MEAN'] * 100, 
                marker='o', linewidth=2, markersize=8, label='Mean Lift')
        
        # Add error bars (std)
        if 'LIFT_STD' in ts_data.columns:
            ax.fill_between(
                ts_data['TIMESTAMP_DATE'],
                (ts_data['LIFT_MEAN'] - ts_data['LIFT_STD']) * 100,
                (ts_data['LIFT_MEAN'] + ts_data['LIFT_STD']) * 100,
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
    
    def generate_report(self, output_dir: str = "output", 
                      top_metrics: Optional[pd.DataFrame] = None,
                      channel_analysis: Optional[pd.DataFrame] = None,
                      time_series: Optional[pd.DataFrame] = None) -> str:
        """
        Generate comprehensive analysis report.
        
        Parameters:
        -----------
        output_dir : str
            Output directory for report
        top_metrics : pd.DataFrame, optional
            Top metrics analysis results
        channel_analysis : pd.DataFrame, optional
            Channel analysis results
        time_series : pd.DataFrame, optional
            Time series analysis results
            
        Returns:
        --------
        str
            Path to generated report
        """
        if self.processed_data is None:
            raise ValueError("Must process data first using process_data()")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_path / f"kantar_bls_report_{timestamp}.txt"
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("KANTAR BLS ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data: {len(self.processed_data):,} rows\n")
            f.write("\n")
            
            # Summary statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total observations: {len(self.processed_data):,}\n")
            f.write(f"Unique metrics: {self.processed_data['METRIC'].nunique():,}\n")
            f.write(f"Unique channels: {self.processed_data['CHANNEL'].nunique():,}\n")
            f.write(f"Unique timestamps: {self.processed_data['TIMESTAMP'].nunique():,}\n")
            if 'TIMESTAMP_DATE' in self.processed_data.columns:
                f.write(f"Date range: {self.processed_data['TIMESTAMP_DATE'].min()} to {self.processed_data['TIMESTAMP_DATE'].max()}\n")
            f.write("\n")
            
            # Top metrics
            f.write("TOP PERFORMING METRICS\n")
            f.write("-" * 80 + "\n")
            if top_metrics is not None and len(top_metrics) > 0:
                f.write(f"Showing top {min(50, len(top_metrics))} metrics:\n\n")
                for idx, row in top_metrics.head(50).iterrows():
                    f.write(f"{row['METRIC']}: {row['LIFT_MEAN']*100:.2f}% (n={row['TOTAL_N']:.0f}, obs={row['OBSERVATIONS']:.0f}, sig={row.get('SIGNIFICANT_COUNT', 0):.0f})\n")
            else:
                top_metrics = self.find_top_metrics(min_observations=3, min_lift=0.0)
                for idx, row in top_metrics.head(50).iterrows():
                    f.write(f"{row['METRIC']}: {row['LIFT_MEAN']*100:.2f}% (n={row['TOTAL_N']:.0f}, obs={row['OBSERVATIONS']:.0f})\n")
            f.write("\n")
            
            # Channel analysis
            f.write("CHANNEL PERFORMANCE (SUMMARY)\n")
            f.write("-" * 80 + "\n")
            channel_summary = self.processed_data.groupby('CHANNEL').agg({
                'LIFT': 'mean',
                'EXPOSED_N': 'sum',
                'CONTROL_N': 'sum'
            }).reset_index()
            channel_summary['TOTAL_N'] = channel_summary['EXPOSED_N'] + channel_summary['CONTROL_N']
            channel_summary = channel_summary.sort_values('LIFT', ascending=False)
            
            for idx, row in channel_summary.iterrows():
                f.write(f"{row['CHANNEL']}: {row['LIFT']*100:.2f}% (n={row['TOTAL_N']:.0f})\n")
            f.write("\n")
            
            # Detailed channel analysis
            if channel_analysis is not None and len(channel_analysis) > 0:
                f.write("CHANNEL ANALYSIS (DETAILED)\n")
                f.write("-" * 80 + "\n")
                f.write(f"Showing top {min(50, len(channel_analysis))} channel-metric combinations:\n\n")
                for idx, row in channel_analysis.head(50).iterrows():
                    f.write(f"{row['CHANNEL']} - {row['METRIC']}: {row['LIFT_MEAN']*100:.2f}% (n={row['TOTAL_N']:.0f}, obs={row['LIFT_COUNT']:.0f})\n")
                f.write("\n")
            
            # Time series analysis
            if time_series is not None and len(time_series) > 0:
                f.write("TIME SERIES ANALYSIS\n")
                f.write("-" * 80 + "\n")
                f.write(f"Showing {min(50, len(time_series))} time series data points:\n\n")
                for idx, row in time_series.head(50).iterrows():
                    timestamp_str = str(row.get('TIMESTAMP_DATE', row.get('TIMESTAMP', 'N/A')))
                    f.write(f"{timestamp_str} - {row['METRIC']}: {row['LIFT_MEAN']*100:.2f}% (n={row['TOTAL_N']:.0f}, obs={row['LIFT_COUNT']:.0f})\n")
                f.write("\n")
            
            # Significant results
            f.write("STATISTICALLY SIGNIFICANT RESULTS\n")
            f.write("-" * 80 + "\n")
            significant = self.detect_significance(alpha=0.05)
            sig_count = significant['IS_SIGNIFICANT'].sum()
            f.write(f"Total significant results: {sig_count:,} ({sig_count/len(significant)*100:.1f}%)\n")
            
            # Top significant results
            sig_results = significant[significant['IS_SIGNIFICANT']].sort_values('LIFT', ascending=False)
            if len(sig_results) > 0:
                f.write(f"\nTop {min(20, len(sig_results))} significant results:\n\n")
                for idx, row in sig_results.head(20).iterrows():
                    channel = row.get('CHANNEL', 'Unknown')
                    metric = row.get('METRIC', 'Unknown')
                    lift = row['LIFT'] * 100 if pd.notna(row['LIFT']) else 0
                    f.write(f"{channel} - {metric}: {lift:.2f}% (p={row.get('STATISTICAL_SIGNIFICANCE', 'N/A')})\n")
            f.write("\n")
        
        print(f"✓ Report saved to {report_path}")
        return str(report_path)
    
    def create_aggregate_visualizations(self, output_dir: str = "output"):
        """
        Create aggregate visualizations similar to analyze.py.
        
        Creates:
        - lift_by_channel.png: Average lift by channel
        - top_metrics.png: Top 15 metrics by average lift
        - lift_heatmap.png: Heatmap of metrics by channel
        - consistent_signals.png: Scatter plot of consistency vs lift (if enough data)
        
        Parameters:
        -----------
        output_dir : str
            Output directory for plots
        """
        if self.processed_data is None:
            raise ValueError("Must process data first using process_data()")
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print("\n  Creating aggregate visualizations...")
        
        # 1. Lift by channel (aggregate)
        print("    Creating lift_by_channel.png...")
        channel_summary = self.processed_data.groupby('CHANNEL').agg({
            'LIFT': 'mean'
        }).sort_values('LIFT')
        
        fig, ax = plt.subplots(figsize=(12, 6))
        (channel_summary['LIFT'] * 100).plot(kind='barh', ax=ax, color='steelblue')
        ax.set_xlabel('Average Lift (%)', fontsize=12)
        ax.set_ylabel('Channel', fontsize=12)
        ax.set_title('Average Brand Lift by Channel', fontsize=14, fontweight='bold')
        ax.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        plt.savefig(output_path / 'lift_by_channel.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("      ✓ Saved lift_by_channel.png")
        
        # 2. Top metrics bar chart
        print("    Creating top_metrics.png...")
        top_metrics = self.find_top_metrics(min_observations=3, min_lift=0.0).head(15)
        
        if len(top_metrics) > 0:
            fig, ax = plt.subplots(figsize=(12, 8))
            y_pos = range(len(top_metrics))
            ax.barh(y_pos, top_metrics['LIFT_MEAN'] * 100, color='steelblue')
            ax.set_yticks(y_pos)
            ax.set_yticklabels([name[:60] + '...' if len(name) > 60 else name 
                               for name in top_metrics['METRIC']], fontsize=8)
            ax.set_xlabel('Average Lift (%)', fontsize=12)
            ax.set_title('Top 15 Metrics by Average Lift', fontsize=14, fontweight='bold')
            ax.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
            ax.grid(True, alpha=0.3, axis='x')
            
            # Add value labels
            for i, (idx, row) in enumerate(top_metrics.iterrows()):
                ax.text(row['LIFT_MEAN'] * 100 + (0.5 if row['LIFT_MEAN'] >= 0 else -0.5), i, 
                       f"n={row['TOTAL_N']:.0f}",
                       va='center', fontsize=8, ha='left' if row['LIFT_MEAN'] >= 0 else 'right')
            
            plt.tight_layout()
            plt.savefig(output_path / 'top_metrics.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("      ✓ Saved top_metrics.png")
        
        # 3. Lift heatmap (metrics by channel)
        print("    Creating lift_heatmap.png...")
        channel_analysis = self.analyze_by_channel()
        
        if len(channel_analysis) > 0:
            # Create pivot table: metrics as rows, channels as columns
            pivot = channel_analysis.pivot_table(
                index='METRIC',
                columns='CHANNEL',
                values='LIFT_MEAN',
                aggfunc='mean'
            )
            
            if not pivot.empty and len(pivot) > 0:
                # Limit to top 30 metrics for readability
                if len(pivot) > 30:
                    # Get top metrics by average lift across all channels
                    pivot_avg = pivot.mean(axis=1).sort_values(ascending=False)
                    pivot = pivot.loc[pivot_avg.head(30).index]
                
                fig, ax = plt.subplots(figsize=(14, max(8, len(pivot) * 0.3)))
                # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
                sns.heatmap(
                    pivot * 100, 
                    annot=True, 
                    fmt='.1f', 
                    cmap='RdYlGn', 
                    center=0, 
                    ax=ax, 
                    cbar_kws={'label': 'Lift (%)'},
                    linewidths=0.5
                )
                ax.set_title('Lift Heatmap: Metrics by Channel', fontsize=14, fontweight='bold')
                ax.set_xlabel('Channel', fontsize=12)
                ax.set_ylabel('Metric', fontsize=12)
                plt.tight_layout()
                plt.savefig(output_path / 'lift_heatmap.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("      ✓ Saved lift_heatmap.png")
        
        # 4. Consistent signals scatter plot (if we have enough data)
        print("    Creating consistent_signals.png...")
        # Calculate consistency: metrics that appear across multiple channels/filters
        metric_consistency = self.processed_data.groupby('METRIC').agg({
            'CHANNEL': 'nunique',
            'LIFT': ['mean', 'std', 'count'],
            'FILTER': 'nunique'
        }).reset_index()
        
        # Flatten column names
        metric_consistency.columns = ['METRIC', 'UNIQUE_CHANNELS', 'AVG_LIFT', 'LIFT_STD', 'OBSERVATIONS', 'UNIQUE_FILTERS']
        
        # Filter to metrics with multiple channels/filters
        consistent = metric_consistency[
            (metric_consistency['UNIQUE_CHANNELS'] >= 2) &
            (metric_consistency['OBSERVATIONS'] >= 3)
        ].copy()
        
        if len(consistent) > 0:
            # Calculate consistency score (inverse of coefficient of variation)
            consistent['CONSISTENCY_SCORE'] = 1 / (1 + consistent['LIFT_STD'].abs() / (consistent['AVG_LIFT'].abs() + 0.01))
            consistent = consistent.sort_values('CONSISTENCY_SCORE', ascending=False).head(20)
            
            fig, ax = plt.subplots(figsize=(14, 8))
            # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
            scatter = ax.scatter(
                consistent['AVG_LIFT'] * 100,
                consistent['CONSISTENCY_SCORE'],
                s=consistent['UNIQUE_FILTERS'] * 10,
                c=consistent['UNIQUE_CHANNELS'],
                cmap='viridis',
                alpha=0.6,
                edgecolors='black',
                linewidth=0.5
            )
            ax.set_xlabel('Average Lift (%)', fontsize=12)
            ax.set_ylabel('Consistency Score', fontsize=12)
            ax.set_title('Consistent Signals: Metrics with Reliable Performance Across Channels', 
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add metric names for top performers
            for idx, row in consistent.head(10).iterrows():
                ax.annotate(
                    row['METRIC'][:40] + '...' if len(row['METRIC']) > 40 else row['METRIC'],
                    (row['AVG_LIFT'] * 100, row['CONSISTENCY_SCORE']),
                    fontsize=8,
                    alpha=0.7
                )
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Number of Unique Channels', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(output_path / 'consistent_signals.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("      ✓ Saved consistent_signals.png")
            
            # Also create top consistent metrics bar chart
            print("    Creating top_consistent_metrics.png...")
            fig, ax = plt.subplots(figsize=(14, 10))
            top_consistent = consistent.head(15)
            y_pos = range(len(top_consistent))
            ax.barh(y_pos, top_consistent['CONSISTENCY_SCORE'], color='steelblue')
            ax.set_yticks(y_pos)
            ax.set_yticklabels([name[:60] + '...' if len(name) > 60 else name 
                               for name in top_consistent['METRIC']], fontsize=9)
            ax.set_xlabel('Consistency Score', fontsize=12)
            ax.set_title('Top 15 Most Consistent Metrics Across Channels', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            
            # Add value labels
            for i, (idx, row) in enumerate(top_consistent.iterrows()):
                ax.text(row['CONSISTENCY_SCORE'] + 0.01, i, 
                       f"Lift: {row['AVG_LIFT']*100:.2f}% | Channels: {int(row['UNIQUE_CHANNELS'])}",
                       va='center', fontsize=8)
            
            plt.tight_layout()
            plt.savefig(output_path / 'top_consistent_metrics.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("      ✓ Saved top_consistent_metrics.png")
        
        print("  ✓ Aggregate visualizations complete")


def main():
    """
    Main execution function.
    """
    print("=" * 80)
    print("KANTAR BLS ANALYSIS - FROM SCRATCH")
    print("=" * 80)
    print()
    
    # Initialize analyzer
    analyzer = KantarBLSAnalyzer(data_dir="data")
    
    # Load data
    analyzer.load_data(filename="kantar_bls_sample_data.csv")
    
    # Process data
    analyzer.process_data()
    
    # Get output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Analyze top metrics
    print("\n" + "=" * 80)
    print("TOP METRICS")
    print("=" * 80)
    top_metrics = analyzer.find_top_metrics(min_observations=3, min_lift=0.0)
    print(f"\nTop {min(20, len(top_metrics))} metrics:")
    print(top_metrics.head(20).to_string())
    
    # Channel analysis
    print("\n" + "=" * 80)
    print("CHANNEL ANALYSIS")
    print("=" * 80)
    channel_analysis = analyzer.analyze_by_channel()
    print(f"\nTop {min(20, len(channel_analysis))} channel-metric combinations:")
    print(channel_analysis.head(20).to_string())
    
    # Time series analysis
    print("\n" + "=" * 80)
    print("TIME SERIES ANALYSIS")
    print("=" * 80)
    time_series = analyzer.analyze_time_series()
    print(f"\nTop {min(20, len(time_series))} time series data points:")
    print(time_series.head(20).to_string())
    
    # Generate and save plots
    print("\n" + "=" * 80)
    print("GENERATING PLOTS")
    print("=" * 80)
    
    # Get unique metrics for plotting
    unique_metrics = analyzer.processed_data['METRIC'].unique()[:10]  # Top 10 metrics
    
    plot_files = []
    for metric in unique_metrics:
        try:
            # Sanitize metric name for filename
            safe_metric = re.sub(r'[<>:"/\\|?*]', '_', str(metric))
            timestamp = datetime.now().strftime("%Y%m%d")
            
            # Plot time series
            ts_path = output_dir / f"timeseries_{safe_metric}_{timestamp}.png"
            analyzer.plot_time_series(
                metric_name=str(metric),
                save_path=ts_path
            )
            plot_files.append(ts_path)
            
            # Plot channel comparison
            channel_path = output_dir / f"channels_{safe_metric}_{timestamp}.png"
            analyzer.plot_channel_comparison(
                metric_name=str(metric),
                save_path=channel_path
            )
            plot_files.append(channel_path)
        except Exception as e:
            print(f"  ⚠ Could not generate plots for {metric}: {str(e)}")
    
    print(f"✓ Generated {len(plot_files)} individual metric plots")
    
    # Generate aggregate visualizations
    analyzer.create_aggregate_visualizations(output_dir=str(output_dir))
    
    # Generate comprehensive report with all analysis results
    print("\n" + "=" * 80)
    print("GENERATING REPORT")
    print("=" * 80)
    report_path = analyzer.generate_report(
        output_dir=str(output_dir),
        top_metrics=top_metrics,
        channel_analysis=channel_analysis,
        time_series=time_series
    )
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nAll outputs saved to: {output_dir}")
    print(f"  - Report: {Path(report_path).name}")
    print(f"  - Plots: {len(plot_files)} files")


if __name__ == "__main__":
    main()

