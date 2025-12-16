"""
Kantar Brand Lift Survey (BLS) Analysis
========================================

This script ingests, cleans, and analyzes Kantar BLS data to identify patterns
in brand lift across time, channel, and demographics.

Author: DoorDash Brand Measurement Team
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional
from contextlib import contextmanager

# Try to import openpyxl for Excel support (optional)
try:
    import openpyxl
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False

warnings.filterwarnings('ignore')

# Set style for visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class TeeOutput:
    """Class to tee output to both console and file."""
    def __init__(self, file_path: Path):
        self.file = open(file_path, 'w', encoding='utf-8')
        self.console = sys.stdout
        
    def write(self, message):
        self.console.write(message)
        self.file.write(message)
        self.file.flush()
        
    def flush(self):
        self.console.flush()
        self.file.flush()
        
    def close(self):
        self.file.close()


@contextmanager
def log_to_file(file_path: Path):
    """
    Context manager to capture console output to a file.
    
    Usage:
        with log_to_file(Path("output/analysis.log")):
            analyzer.load_data()
            analyzer.clean_and_merge()
            # All print statements will be saved to the log file
    """
    tee = TeeOutput(file_path)
    original_stdout = sys.stdout
    sys.stdout = tee
    try:
        yield tee
    finally:
        sys.stdout = original_stdout
        tee.close()


class KantarBLSAnalyzer:
    """Main class for Kantar BLS data analysis."""
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the analyzer.
        
        Parameters:
        -----------
        data_dir : str, optional
            Directory containing the CSV files. If None, defaults to ../data relative to script location.
        """
        if data_dir is None:
            # Default to data directory relative to script location
            script_dir = Path(__file__).parent
            self.data_dir = script_dir.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        self.metrics = None
        self.answers = None
        self.filters = None
        self.filter_ids = None
        self.codebook = None
        self.merged_data = None
        self.log_file = None
        self.log_enabled = False
        
    def load_data(self, use_snowflake: bool = False, snowflake_config: Optional[Dict] = None):
        """
        Load all BLS data tables from CSV files or Snowflake.
        
        Parameters:
        -----------
        use_snowflake : bool
            If True, load from Snowflake. Otherwise, load from CSV files.
        snowflake_config : dict, optional
            Snowflake connection configuration
        """
        print("Loading Kantar BLS data...")
        
        if use_snowflake:
            self._load_from_snowflake(snowflake_config)
        else:
            self._load_from_csv()
        
        print(f"✓ Loaded metrics: {len(self.metrics):,} rows")
        if self.answers is not None and not self.answers.empty:
            print(f"✓ Loaded answers: {len(self.answers):,} rows")
        else:
            print("✓ Answers: Not loaded (optional)")
        if self.filters is not None and not self.filters.empty:
            print(f"✓ Loaded filters: {len(self.filters):,} rows")
        else:
            print("✓ Filters: Not loaded (using merged file)")
        if self.filter_ids is not None and not self.filter_ids.empty:
            print(f"✓ Loaded filter_ids: {len(self.filter_ids):,} rows")
        else:
            print("✓ Filter IDs: Not loaded (using merged file)")
        if self.codebook is not None and not self.codebook.empty:
            print(f"✓ Loaded codebook: {len(self.codebook):,} mappings")
        else:
            print("✓ Codebook: Not loaded (optional)")
        
    def _load_from_csv(self):
        """Load data from CSV files."""
        # Check if pre-merged file exists (faster option)
        # Priority: 1) bls_metrics_merged.csv (our saved version), 2) bls_metrics_with_filters.csv (Kantar version)
        merged_file = self.data_dir / "bls_metrics_merged.csv"
        if merged_file.exists():
            print("  Found saved merged file: bls_metrics_merged.csv")
            print("  Using saved merged file (skipping individual file loading and merge)...")
            # Load as metrics for compatibility, but we'll use load_merged_data() instead
            self.metrics = pd.read_csv(merged_file, low_memory=False)
            # Initialize other data objects as empty DataFrames since we're using merged file
            self.filters = pd.DataFrame()
            self.filter_ids = pd.DataFrame()
            self.answers = pd.DataFrame()
            self.codebook = pd.DataFrame()
        elif (self.data_dir / "bls_metrics_with_filters.csv").exists():
            merged_file = self.data_dir / "bls_metrics_with_filters.csv"
            print("  Found pre-merged file: bls_metrics_with_filters.csv")
            print("  Using pre-merged file (skipping individual file loading)...")
            self.metrics = pd.read_csv(merged_file, low_memory=False)
            # Still need to load filter_ids for additional metadata if needed
            filter_ids_file = self.data_dir / "kantar_bls_filter_ids.csv"
            if filter_ids_file.exists():
                self.filter_ids = pd.read_csv(filter_ids_file, low_memory=False)
            else:
                self.filter_ids = pd.DataFrame()
            # Filters may not be needed if already merged, but load for compatibility
            filters_file = self.data_dir / "kantar_bls_filters.csv"
            if filters_file.exists():
                self.filters = pd.read_csv(filters_file, low_memory=False)
            else:
                self.filters = pd.DataFrame()
        elif (self.data_dir / "kantar_bls_sample_data.csv").exists():
            # Use sample data file (has timestamps and is complete)
            sample_file = self.data_dir / "kantar_bls_sample_data.csv"
            print("  Found sample data file: kantar_bls_sample_data.csv")
            print("  Using sample data file (has timestamps and is complete)...")
            self.metrics = pd.read_csv(sample_file, low_memory=False)
            # Still need to load filter_ids for additional metadata if needed
            filter_ids_file = self.data_dir / "kantar_bls_filter_ids.csv"
            if filter_ids_file.exists():
                self.filter_ids = pd.read_csv(filter_ids_file, low_memory=False)
            else:
                self.filter_ids = pd.DataFrame()
            # Filters may not be needed if already merged, but load for compatibility
            filters_file = self.data_dir / "kantar_bls_filters.csv"
            if filters_file.exists():
                self.filters = pd.read_csv(filters_file, low_memory=False)
            else:
                self.filters = pd.DataFrame()
        else:
            # Load individual files (fallback to old bls_metrics.csv if transformed data not available)
            self.metrics = pd.read_csv(self.data_dir / "bls_metrics.csv", low_memory=False)
            # Load filters
            self.filters = pd.read_csv(self.data_dir / "kantar_bls_filters.csv", low_memory=False)
            # Load filter_ids
            self.filter_ids = pd.read_csv(self.data_dir / "kantar_bls_filter_ids.csv", low_memory=False)
        
        # Load answers (may be large, so use chunking if needed)
        answers_file = self.data_dir / "bls_answers.csv"
        if answers_file.exists():
            try:
                self.answers = pd.read_csv(answers_file, low_memory=False)
            except MemoryError:
                print("Warning: Answers file is very large. Loading in chunks...")
                chunks = []
                for chunk in pd.read_csv(answers_file, chunksize=100000, low_memory=False):
                    chunks.append(chunk)
                self.answers = pd.concat(chunks, ignore_index=True)
        else:
            print("  Warning: bls_answers.csv not found. Skipping answers data.")
            self.answers = pd.DataFrame()
        
        # Load codebook mapping
        codebook_files = list(self.data_dir.glob("*codebook*.csv"))
        if codebook_files:
            self.codebook = pd.read_csv(codebook_files[0])
        else:
            print("  Warning: Codebook mapping file not found.")
            self.codebook = pd.DataFrame()
        
    def _load_from_snowflake(self, config: Dict):
        """Load data from Snowflake (to be implemented)."""
        # TODO: Implement Snowflake connection
        # import snowflake.connector
        # conn = snowflake.connector.connect(**config)
        # self.metrics = pd.read_sql("SELECT * FROM marketing.kantar.bls_metrics", conn)
        # ...
        raise NotImplementedError("Snowflake loading not yet implemented. Use CSV files for now.")
    
    def clean_and_merge(self, save_merged: bool = True):
        """
        Clean data and create merged analysis dataset.
        
        Parameters:
        -----------
        save_merged : bool, default True
            If True, save the merged dataset to CSV file for future use
        """
        print("\nCleaning and merging data...")
        
        # Check if data is already merged (from saved file or pre-merged file)
        # First check if we already loaded the saved merged file in load_data()
        if (self.metrics is not None and 
            not self.metrics.empty and
            ('CHANNEL' in self.metrics.columns or 'TIME_PERIOD' in self.metrics.columns)):
            # This is our saved merged file with extracted dimensions
            print("  Using saved merged file with extracted dimensions...")
            self.merged_data = self.metrics.copy()
            # Ensure TIME_DATE is datetime if it exists
            if 'TIME_DATE' in self.merged_data.columns:
                self.merged_data['TIME_DATE'] = pd.to_datetime(self.merged_data['TIME_DATE'], errors='coerce')
            print(f"✓ Using saved merged dataset: {len(self.merged_data):,} rows")
            return
        
        # Check if we have pre-merged file from Kantar
        merged_file = self.data_dir / "bls_metrics_with_filters.csv"
        if (merged_file.exists() and 
            self.metrics is not None and 
            not self.metrics.empty and
            'FILTER_NAME' in self.metrics.columns and 
            'GROUP_NAME' in self.metrics.columns):
            print("  Data already merged. Skipping merge step...")
            self.merged_data = self._clean_metrics()
        else:
            # Clean metrics
            self.metrics = self._clean_metrics()
            
            # Clean filters and filter_ids
            self.filters = self._clean_filters()
            self.filter_ids = self._clean_filter_ids()
            
            # Merge metrics with filter metadata
            self.merged_data = self._merge_data()
        
        # Extract time and channel information
        self.merged_data = self._extract_dimensions()
        
        print(f"✓ Merged dataset: {len(self.merged_data):,} rows")
        
        # Handle FILTER_ID - create from FILTER column if needed (sample data format)
        is_sample_data = 'FILTER' in self.merged_data.columns and 'FILTER_ID' not in self.merged_data.columns
        if is_sample_data:
            # Create FILTER_ID from FILTER column for compatibility
            if 'FILTER_ID' not in self.merged_data.columns and 'FILTER' in self.merged_data.columns:
                # Use FILTER as FILTER_ID (or could create hash)
                self.merged_data['FILTER_ID'] = self.merged_data['FILTER']
        
        # Print unique counts (handle missing columns gracefully)
        if 'FILTER_ID' in self.merged_data.columns:
            print(f"✓ Unique filters: {self.merged_data['FILTER_ID'].nunique():,}")
        elif 'FILTER' in self.merged_data.columns:
            print(f"✓ Unique filters: {self.merged_data['FILTER'].nunique():,}")
        
        # Use METRIC column directly (sample data has METRIC column)
        if 'METRIC' in self.merged_data.columns:
            print(f"✓ Unique metrics: {self.merged_data['METRIC'].nunique():,}")
        elif 'FOLDER_NAME' in self.merged_data.columns:
            print(f"✓ Unique metrics: {self.merged_data['FOLDER_NAME'].nunique():,}")
        
        # Save merged data if requested
        if save_merged:
            self._save_merged_data()
        
    def _clean_metrics(self) -> pd.DataFrame:
        """Clean metrics data."""
        df = self.metrics.copy()
        
        # Ensure numeric columns are numeric (using sample data column names)
        numeric_cols = ['LIFT', 'DELTA', 'EXPOSED_', 'CONTROL_', 
                        'EXPOSED_N', 'CONTROL_N', 'STATISTICAL_SIGNIFICANCE']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate lift if missing (using sample data column names)
        if 'LIFT' in df.columns and df['LIFT'].isna().any():
            mask = df['LIFT'].isna()
            # Use EXPOSED_ and CONTROL_ from sample data
            if 'EXPOSED_' in df.columns and 'CONTROL_' in df.columns:
                df.loc[mask, 'LIFT'] = (
                    (df.loc[mask, 'EXPOSED_'] - df.loc[mask, 'CONTROL_']) 
                    / df.loc[mask, 'CONTROL_'].replace(0, np.nan) * 100
                )
        
        return df
    
    def _clean_filters(self) -> pd.DataFrame:
        """Clean filters data."""
        df = self.filters.copy()
        
        # Standardize column names
        if 'GROUP_NAME' in df.columns:
            df['GROUP_NAME'] = df['GROUP_NAME'].str.strip()
        if 'NAME' in df.columns:
            df['NAME'] = df['NAME'].str.strip()
        
        return df
    
    def _clean_filter_ids(self) -> pd.DataFrame:
        """Clean filter_ids data."""
        df = self.filter_ids.copy()
        
        # Standardize column names
        if 'GROUP_NAME' in df.columns:
            df['GROUP_NAME'] = df['GROUP_NAME'].str.strip()
        if 'NAME' in df.columns:
            df['NAME'] = df['NAME'].str.strip()
        if 'SURVEY_LABEL' in df.columns:
            df['SURVEY_LABEL'] = df['SURVEY_LABEL'].str.strip()
        
        return df
    
    def _merge_data(self) -> pd.DataFrame:
        """
        Merge metrics with filter metadata.
        
        Steps:
        1. Join bls_metrics with kantar_bls_filter_ids on FILTER_ID (old data) or FILTER/NAME (transformed data)
        2. Join to kantar_bls_filters to get filter_name and group_name
        
        For sample data (kantar_bls_sample_data.csv):
        - Uses FILTER column to merge with NAME column in filter tables
        For old data (bls_metrics.csv):
        - Uses FILTER_ID column to merge with FILTER_ID in filter tables
        """
        # Start with metrics
        merged = self.metrics.copy()
        
        # Detect data format: transformed data has FILTER column, old data has FILTER_ID
        is_transformed_data = 'FILTER' in merged.columns and 'FILTER_ID' not in merged.columns
        
        if is_transformed_data:
            # Transformed data: merge using FILTER column (filter name) with NAME column
            print("  Detected transformed data format: using FILTER column for merging")
            
            # Step 1: Merge with filter_ids using FILTER (name) -> NAME
            if 'FILTER' in merged.columns and not self.filter_ids.empty and 'NAME' in self.filter_ids.columns:
                # Get available columns from filter_ids
                filter_id_cols = ['NAME']  # Use NAME as the join key
                for col in ['FILTER_ID', 'GROUP_NAME', 'SURVEY_ID', 'SURVEY_LABEL']:
                    if col in self.filter_ids.columns:
                        filter_id_cols.append(col)
                
                # Rename NAME to FILTER for joining, then rename back
                filter_ids_for_join = self.filter_ids[filter_id_cols].copy()
                filter_ids_for_join = filter_ids_for_join.rename(columns={'NAME': 'FILTER'})
                
                # Remove duplicates to avoid many-to-many joins
                filter_ids_for_join = filter_ids_for_join.drop_duplicates(subset=['FILTER'])
                
                merged = merged.merge(
                    filter_ids_for_join,
                    on='FILTER',
                    how='left'
                )
                print(f"  Merged with filter_ids using FILTER->NAME: {len(merged):,} rows")
            
            # Step 2: Merge with filters table (if it has NAME column)
            if 'FILTER' in merged.columns and not self.filters.empty and 'NAME' in self.filters.columns:
                # Get available columns from filters
                filter_cols = ['NAME']  # Use NAME as the join key
                for col in ['FILTER_ID', 'GROUP_NAME', 'SURVEY_ID']:
                    if col in self.filters.columns:
                        filter_cols.append(col)
                
                # Rename NAME to FILTER for joining
                filters_for_join = self.filters[filter_cols].copy()
                filters_for_join = filters_for_join.rename(columns={'NAME': 'FILTER'})
                
                # Remove duplicates to avoid many-to-many joins
                filters_for_join = filters_for_join.drop_duplicates(subset=['FILTER'])
                
                # Merge with suffixes to handle overlapping column names
                merged = merged.merge(
                    filters_for_join,
                    on='FILTER',
                    how='left',
                    suffixes=('_filter_ids', '_filters')
                )
                print(f"  Merged with filters using FILTER->NAME: {len(merged):,} rows")
            
            # Consolidate GROUP_NAME columns
            if 'GROUP_NAME_filters' in merged.columns:
                merged['GROUP_NAME'] = merged['GROUP_NAME_filters'].fillna(merged.get('GROUP_NAME_filter_ids', ''))
                merged = merged.drop(columns=['GROUP_NAME_filters', 'GROUP_NAME_filter_ids'], errors='ignore')
            elif 'GROUP_NAME_filter_ids' in merged.columns:
                merged['GROUP_NAME'] = merged['GROUP_NAME_filter_ids']
                merged = merged.drop(columns=['GROUP_NAME_filter_ids'], errors='ignore')
            
            # Set FILTER_NAME from FILTER column (it's already the filter name)
            if 'FILTER' in merged.columns:
                merged['FILTER_NAME'] = merged['FILTER']
        
        else:
            # Old data format: merge using FILTER_ID
            print("  Detected old data format: using FILTER_ID column for merging")
            
            # Step 1: Merge with filter_ids to get GROUP_NAME, NAME, SURVEY_LABEL, etc.
            if 'FILTER_ID' in merged.columns and not self.filter_ids.empty and 'FILTER_ID' in self.filter_ids.columns:
                # Get available columns from filter_ids
                filter_id_cols = ['FILTER_ID']
                for col in ['GROUP_NAME', 'NAME', 'SURVEY_ID', 'SURVEY_LABEL']:
                    if col in self.filter_ids.columns:
                        filter_id_cols.append(col)
                
                merged = merged.merge(
                    self.filter_ids[filter_id_cols],
                    on='FILTER_ID',
                    how='left'
                )
            
            # Step 2: Merge with filters table to get additional filter_name and group_name
            # (filters table may have more detailed information)
            if 'FILTER_ID' in merged.columns and not self.filters.empty and 'FILTER_ID' in self.filters.columns:
                # Get available columns from filters
                filter_cols = ['FILTER_ID']
                for col in ['GROUP_NAME', 'NAME', 'SURVEY_ID']:
                    if col in self.filters.columns:
                        filter_cols.append(col)
                
                # Remove duplicates to avoid many-to-many joins
                filters_subset = self.filters[filter_cols].drop_duplicates(subset=['FILTER_ID'])
                
                # Merge with suffixes to handle overlapping column names
                merged = merged.merge(
                    filters_subset,
                    on='FILTER_ID',
                    how='left',
                    suffixes=('_filter_ids', '_filters')
                )
                
                # Consolidate GROUP_NAME and NAME columns
                # Prefer filters table values, fall back to filter_ids
                if 'GROUP_NAME_filters' in merged.columns:
                    merged['GROUP_NAME'] = merged['GROUP_NAME_filters'].fillna(merged.get('GROUP_NAME_filter_ids', ''))
                    merged = merged.drop(columns=['GROUP_NAME_filters', 'GROUP_NAME_filter_ids'], errors='ignore')
                elif 'GROUP_NAME_filter_ids' in merged.columns:
                    merged['GROUP_NAME'] = merged['GROUP_NAME_filter_ids']
                    merged = merged.drop(columns=['GROUP_NAME_filter_ids'], errors='ignore')
                
                # Handle NAME/FILTER_NAME - use NAME from filters as FILTER_NAME
                if 'NAME_filters' in merged.columns:
                    merged['FILTER_NAME'] = merged['NAME_filters'].fillna(merged.get('NAME_filter_ids', ''))
                    # Keep original NAME from filter_ids as well if it exists
                    if 'NAME_filter_ids' in merged.columns:
                        merged['NAME'] = merged['NAME_filter_ids']
                    merged = merged.drop(columns=['NAME_filters', 'NAME_filter_ids'], errors='ignore')
                elif 'NAME_filter_ids' in merged.columns:
                    merged['FILTER_NAME'] = merged['NAME_filter_ids']
                    merged['NAME'] = merged['NAME_filter_ids']
        
        return merged
    
    def _extract_timestamp_from_limiting_filter(self, limiting_filter: str) -> Optional[str]:
        """
        Extract timestamp from LIMITING_FILTER column (for new data format).
        
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
    
    def _extract_dimensions(self) -> pd.DataFrame:
        """
        Extract time, channel, and demographic dimensions from filter metadata.
        
        Based on Kantar API structure:
        - Channels are in filters call, often with "XM" prefix/folder
        - Time/date information is in filters call with "timestamp" as GROUP_NAME
        - Multiple filter IDs can be combined for aggregated analysis
        
        For transformed data:
        - Channels are in WEIGHT_SET or EXPOSED_FILTER columns
        - Time information is in LIMITING_FILTER column
        """
        df = self.merged_data.copy()
        
        # Check if this is transformed data (has WEIGHT_SET/EXPOSED_FILTER columns)
        is_transformed_data = 'WEIGHT_SET' in df.columns or 'EXPOSED_FILTER' in df.columns
        
        # Extract channel from GROUP_NAME or FILTER_NAME or NAME
        # Look for "XM" prefix/folder (Kantar's channel folder structure)
        # Common channels: TV, OTT, Social, Digital, etc.
        channel_keywords = {
            'TV': ['TV', 'television', 'broadcast', 'network'],
            'OTT': ['OTT', 'streaming', 'hulu', 'netflix', 'amazon ctv'],
            'Social': ['social', 'facebook', 'instagram', 'twitter', 'x', 'tiktok', 'snapchat', 'meta'],
            'Digital': ['digital', 'display', 'banner', 'programmatic', 'trade desk', 'realm'],
            'Podcast': ['podcast', 'audio', 'iheart', 'good karma'],
            'Radio': ['radio'],
            'CTV': ['CTV', 'connected tv'],
            'Outdoor': ['billboard', 'outdoor', 'ooh']
        }
        
        def extract_channel(row):
            # For transformed data, extract from WEIGHT_SET or EXPOSED_FILTER
            if is_transformed_data:
                weight_set = str(row.get('WEIGHT_SET', '')).lower()
                exposed_filter = str(row.get('EXPOSED_FILTER', '')).lower()
                text = f"{weight_set} {exposed_filter}"
                
                # Pattern: "XM: N. Channel" or "XM: Channel"
                patterns = [
                    r'xm:\s*\d+\.\s*(\w+)',  # "XM: 2. Social"
                    r'xm:\s*(\w+)',  # "XM: Social"
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
                
                # Fallback to keyword matching
                for channel, keywords in channel_keywords.items():
                    if any(kw in text for kw in keywords):
                        return channel
                return 'Other'
            else:
                # Old data format: extract from GROUP_NAME, FILTER_NAME, NAME
                group_name = str(row.get('GROUP_NAME', ''))
                filter_name = str(row.get('FILTER_NAME', ''))
                name = str(row.get('NAME', ''))
                
                # Check for XM prefix (Kantar's channel folder structure)
                group_lower = group_name.lower()
                if 'xm' in group_lower or group_lower.startswith('xm'):
                    # Extract channel from the group name after XM prefix
                    text = f"{group_name} {filter_name} {name}".lower()
                else:
                    # Try FILTER_NAME first (from merged file), then NAME, then GROUP_NAME
                    text = f"{group_name} {filter_name} {name}".lower()
                
                for channel, keywords in channel_keywords.items():
                    if any(kw in text for kw in keywords):
                        return channel
                return 'Other'
        
        df['CHANNEL'] = df.apply(extract_channel, axis=1)
        
        # Extract time dimension - handle both old and new formats
        if is_transformed_data and 'LIMITING_FILTER' in df.columns:
            # New format: extract from LIMITING_FILTER column
            print("  Extracting timestamps from LIMITING_FILTER (new format)...")
            df['TIMESTAMP'] = df['LIMITING_FILTER'].apply(self._extract_timestamp_from_limiting_filter)
            df['TIMESTAMP_DATE'] = pd.to_datetime(df['TIMESTAMP'], errors='coerce')
            # Also create TIME_PERIOD and TIME_DATE for compatibility
            df['TIME_PERIOD'] = df['TIMESTAMP_DATE'].dt.strftime('%B %Y').fillna('Unknown')
            df['TIME_DATE'] = df['TIMESTAMP_DATE']
        else:
            # Old format: extract from FILTER_NAME, SURVEY_LABEL, or other fields
            df['TIME_PERIOD'] = self._extract_time_period(df)
            df['TIME_DATE'] = self._parse_time_to_date(df)
        
        # Extract demographics from GROUP_NAME or NAME
        demo_keywords = {
            'Hispanic': ['hispanic', 'hisp'],
            'Core': ['core'],
            'Age': ['age', '18-24', '25-34', '35-44', '45-54', '55+'],
            'Gender': ['male', 'female', 'gender'],
            'Income': ['income']
        }
        
        def extract_demographic(group_name, filter_name, name):
            text = f"{group_name} {filter_name} {name}".lower()
            for demo, keywords in demo_keywords.items():
                if any(kw in text for kw in keywords):
                    return demo
            return 'General'
        
        df['DEMOGRAPHIC'] = df.apply(
            lambda row: extract_demographic(
                str(row.get('GROUP_NAME', '')),
                str(row.get('FILTER_NAME', '')),
                str(row.get('NAME', ''))
            ),
            axis=1
        )
        
        return df
    
    def _extract_time_period(self, df: pd.DataFrame) -> pd.Series:
        """
        Extract time period labels from filter names or other fields.
        Returns a series with time period strings (e.g., "April 2025", "Q2 2025").
        
        Based on Kantar API: Time/date information is in filters call with 
        "timestamp" as GROUP_NAME, containing date ranges in the NAME field.
        """
        time_periods = []
        
        for idx, row in df.iterrows():
            time_period = None
            
            # Priority 1: Check if GROUP_NAME is "timestamp" (Kantar's time filter group)
            # In this case, the NAME field should contain the date range
            group_name = str(row.get('GROUP_NAME', '')).strip().lower()
            if group_name == 'timestamp':
                if 'NAME' in row and pd.notna(row['NAME']):
                    time_period = self._parse_time_from_text(str(row['NAME']))
                elif 'FILTER_NAME' in row and pd.notna(row['FILTER_NAME']):
                    time_period = self._parse_time_from_text(str(row['FILTER_NAME']))
            
            # Priority 2: Try FILTER_NAME (most likely to have time info)
            if not time_period and 'FILTER_NAME' in row and pd.notna(row['FILTER_NAME']):
                time_period = self._parse_time_from_text(str(row['FILTER_NAME']))
            
            # Priority 3: Try NAME if FILTER_NAME didn't work
            if not time_period and 'NAME' in row and pd.notna(row['NAME']):
                time_period = self._parse_time_from_text(str(row['NAME']))
            
            # Priority 4: Try SURVEY_LABEL
            if not time_period and 'SURVEY_LABEL' in row and pd.notna(row['SURVEY_LABEL']):
                time_period = self._parse_time_from_text(str(row['SURVEY_LABEL']))
            
            # Priority 5: Try GROUP_NAME as last resort (if not already checked)
            if not time_period and group_name != 'timestamp' and 'GROUP_NAME' in row and pd.notna(row['GROUP_NAME']):
                time_period = self._parse_time_from_text(str(row['GROUP_NAME']))
            
            time_periods.append(time_period if time_period else 'Unknown')
        
        return pd.Series(time_periods, index=df.index)
    
    def _parse_time_from_text(self, text: str) -> Optional[str]:
        """
        Parse time information from text.
        Looks for patterns like:
        - "April 2025" → "April 2025"
        - "Q2 2025" → "Q2 2025"
        - "2025-04" → "April 2025"
        - "Apr 2025" → "April 2025"
        """
        if not text or pd.isna(text):
            return None
        
        text = str(text).strip()
        
        # Month names (full and abbreviated)
        months = {
            'january': 'January', 'jan': 'January',
            'february': 'February', 'feb': 'February',
            'march': 'March', 'mar': 'March',
            'april': 'April', 'apr': 'April',
            'may': 'May',
            'june': 'June', 'jun': 'June',
            'july': 'July', 'jul': 'July',
            'august': 'August', 'aug': 'August',
            'september': 'September', 'sep': 'September', 'sept': 'September',
            'october': 'October', 'oct': 'October',
            'november': 'November', 'nov': 'November',
            'december': 'December', 'dec': 'December'
        }
        
        # Pattern 1: "Month Year" or "Month, Year" (e.g., "April 2025", "Apr 2025")
        for month_key, month_full in months.items():
            pattern = rf'\b{month_key}\s*,?\s*(\d{{4}})\b'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                year = match.group(1)
                return f"{month_full} {year}"
        
        # Pattern 2: "Year-Month" or "Year/Month" (e.g., "2025-04", "2025/04")
        pattern = r'\b(\d{4})[-/](\d{1,2})\b'
        match = re.search(pattern, text)
        if match:
            year = match.group(1)
            month_num = int(match.group(2))
            if 1 <= month_num <= 12:
                month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                return f"{month_names[month_num - 1]} {year}"
        
        # Pattern 3: Quarter format (e.g., "Q2 2025", "Q2-2025", "2025 Q2")
        pattern = r'\bQ([1-4])\s*,?\s*(\d{4})\b|\b(\d{4})\s*,?\s*Q([1-4])\b'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if match.group(1):  # Q2 2025 format
                quarter = match.group(1)
                year = match.group(2)
            else:  # 2025 Q2 format
                year = match.group(3)
                quarter = match.group(4)
            return f"Q{quarter} {year}"
        
        # Pattern 4: Just year (e.g., "2025")
        pattern = r'\b(20\d{2})\b'
        match = re.search(pattern, text)
        if match:
            year = match.group(1)
            return f"{year}"
        
        return None
    
    def _parse_time_to_date(self, df: pd.DataFrame) -> pd.Series:
        """
        Parse time period strings into standardized date format (YYYY-MM-DD).
        Example: "April 2025" → "2025-04-01"
        """
        dates = []
        
        for idx, row in df.iterrows():
            time_period = row.get('TIME_PERIOD', '')
            
            if pd.isna(time_period) or time_period == 'Unknown':
                dates.append(None)
                continue
            
            time_period = str(time_period).strip()
            date = None
            
            # Pattern 1: "Month Year" (e.g., "April 2025")
            months = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            
            for month_name, month_num in months.items():
                pattern = rf'\b{month_name}\s+(\d{{4}})\b'
                match = re.search(pattern, time_period, re.IGNORECASE)
                if match:
                    year = int(match.group(1))
                    try:
                        date = datetime(year, month_num, 1).strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
                    break
            
            # Pattern 2: "Q# Year" (e.g., "Q2 2025" → first month of quarter)
            if not date:
                pattern = r'\bQ([1-4])\s+(\d{4})\b'
                match = re.search(pattern, time_period, re.IGNORECASE)
                if match:
                    quarter = int(match.group(1))
                    year = int(match.group(2))
                    # Q1=Jan, Q2=Apr, Q3=Jul, Q4=Oct
                    month_num = (quarter - 1) * 3 + 1
                    try:
                        date = datetime(year, month_num, 1).strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
            
            # Pattern 3: "YYYY-MM-DD" or "YYYY/MM/DD" (already formatted)
            if not date:
                pattern = r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b'
                match = re.search(pattern, time_period)
                if match:
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
                    try:
                        date = datetime(year, month, day).strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
            
            # Pattern 4: "YYYY-MM" (e.g., "2025-04")
            if not date:
                pattern = r'\b(\d{4})[-/](\d{1,2})\b'
                match = re.search(pattern, time_period)
                if match:
                    year, month = int(match.group(1)), int(match.group(2))
                    try:
                        date = datetime(year, month, 1).strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
            
            # Pattern 5: Just year (e.g., "2025" → "2025-01-01")
            if not date:
                pattern = r'\b(20\d{2})\b'
                match = re.search(pattern, time_period)
                if match:
                    year = int(match.group(1))
                    try:
                        date = datetime(year, 1, 1).strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
            
            dates.append(date)
        
        return pd.Series(dates, index=df.index)
    
    def _save_merged_data(self):
        """
        Save the merged dataset to CSV file for future use.
        Saves to data directory as bls_metrics_merged.csv
        """
        if self.merged_data is None:
            print("  Warning: No merged data to save.")
            return
        
        output_file = self.data_dir / "bls_metrics_merged.csv"
        
        try:
            print(f"\nSaving merged data to {output_file}...")
            self.merged_data.to_csv(output_file, index=False)
            file_size = output_file.stat().st_size / (1024 * 1024)  # Size in MB
            print(f"✓ Saved merged dataset: {len(self.merged_data):,} rows ({file_size:.2f} MB)")
            print(f"  File: {output_file}")
        except Exception as e:
            print(f"  Warning: Could not save merged data: {str(e)}")
    
    def load_merged_data(self, filename: str = "bls_metrics_merged.csv"):
        """
        Load previously saved merged data to skip merge step.
        
        Parameters:
        -----------
        filename : str, default "bls_metrics_merged.csv"
            Name of the saved merged data file in data directory
        """
        merged_file = self.data_dir / filename
        
        if not merged_file.exists():
            raise FileNotFoundError(f"Merged data file not found: {merged_file}")
        
        print(f"Loading saved merged data from {filename}...")
        self.merged_data = pd.read_csv(merged_file, low_memory=False)
        
        # Convert TIME_DATE to datetime if it exists
        if 'TIME_DATE' in self.merged_data.columns:
            self.merged_data['TIME_DATE'] = pd.to_datetime(self.merged_data['TIME_DATE'], errors='coerce')
        
        print(f"✓ Loaded merged dataset: {len(self.merged_data):,} rows")
        
        # Handle FILTER_ID - create from FILTER column if needed (sample data format)
        is_sample_data = 'FILTER' in self.merged_data.columns and 'FILTER_ID' not in self.merged_data.columns
        if is_sample_data:
            # Create FILTER_ID from FILTER column for compatibility
            if 'FILTER_ID' not in self.merged_data.columns and 'FILTER' in self.merged_data.columns:
                self.merged_data['FILTER_ID'] = self.merged_data['FILTER']
        
        # Print unique counts (handle missing columns gracefully)
        if 'FILTER_ID' in self.merged_data.columns:
            print(f"✓ Unique filters: {self.merged_data['FILTER_ID'].nunique():,}")
        elif 'FILTER' in self.merged_data.columns:
            print(f"✓ Unique filters: {self.merged_data['FILTER'].nunique():,}")
        
        # Use METRIC column directly (sample data has METRIC column)
        if 'METRIC' in self.merged_data.columns:
            print(f"✓ Unique metrics: {self.merged_data['METRIC'].nunique():,}")
        elif 'FOLDER_NAME' in self.merged_data.columns:
            print(f"✓ Unique metrics: {self.merged_data['FOLDER_NAME'].nunique():,}")
    
    def analyze_trends(self, metric_name: Optional[str] = None, 
                      group_by: List[str] = None) -> pd.DataFrame:
        """
        Analyze trends in brand lift across specified dimensions.
        
        Parameters:
        -----------
        metric_name : str, optional
            Specific metric to analyze (e.g., "Unaided Brand Awareness")
        group_by : list of str, optional
            Dimensions to group by (e.g., ['CHANNEL', 'TIME_PERIOD'])
        
        Returns:
        --------
        pd.DataFrame
            Aggregated results
        """
        if self.merged_data is None:
            raise ValueError("Must run clean_and_merge() first")
        
        df = self.merged_data.copy()
        
        # Filter by metric if specified
        if metric_name:
            df = df[df['METRIC'].str.contains(metric_name, case=False, na=False)]
        
        # Default grouping
        if group_by is None:
            group_by = ['CHANNEL', 'METRIC']
        
        # Aggregate
        agg_dict = {
            'LIFT': ['mean', 'std', 'count'],
            'DELTA': ['mean', 'std'],
            'EXPOSED_': 'mean',
            'CONTROL_': 'mean',
            'STATISTICAL_SIGNIFICANCE': 'mean'
        }
        
        # Only include columns that exist
        agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
        
        results = df.groupby(group_by).agg(agg_dict).reset_index()
        results.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                          for col in results.columns.values]
        
        return results
    
    def detect_significance(self, alpha: float = 0.05) -> pd.DataFrame:
        """
        Identify statistically significant lift results.
        
        Parameters:
        -----------
        alpha : float
            Significance level threshold
        
        Returns:
        --------
        pd.DataFrame
            Results with significance flags
        """
        if self.merged_data is None:
            raise ValueError("Must run clean_and_merge() first")
        
        df = self.merged_data.copy()
        
        # Add significance flag based on STATISTICAL_SIGNIFICANCE (sample data column name)
        if 'STATISTICAL_SIGNIFICANCE' in df.columns:
            df['IS_SIGNIFICANT'] = df['STATISTICAL_SIGNIFICANCE'] <= alpha
        else:
            # If no significance level, use a heuristic based on sample size and lift
            # This is a simplified approach - adjust based on your needs
            # Use EXPOSED_N and CONTROL_N from sample data
            if 'EXPOSED_N' in df.columns and 'CONTROL_N' in df.columns:
                df['IS_SIGNIFICANT'] = (
                    (df['EXPOSED_N'] >= 100) & 
                    (df['CONTROL_N'] >= 100) &
                    (abs(df['LIFT']) > 0.05)  # At least 5% lift (LIFT stored as decimal: 0.05 = 5%)
                )
            else:
                df['IS_SIGNIFICANT'] = False
        
        # Calculate confidence intervals (simplified)
        # For proper CI calculation, you'd need the standard errors
        df['LIFT_CI_LOWER'] = df['LIFT'] - 1.96 * df.get('LIFT_STD', 0)
        df['LIFT_CI_UPPER'] = df['LIFT'] + 1.96 * df.get('LIFT_STD', 0)
        
        return df
    
    def find_consistent_signals(self, min_filters: int = 3, min_lift: float = 0.0) -> pd.DataFrame:
        """
        Find brand metrics that show consistent signal across multiple filters.
        
        This identifies metrics that perform well (or consistently) across different
        channels, demographics, time periods, etc.
        
        Parameters:
        -----------
        min_filters : int, default 3
            Minimum number of different filters a metric must appear in
        min_lift : float, default 0.0
            Minimum average lift to consider (can be negative to include all)
        
        Returns:
        --------
        pd.DataFrame
            Metrics with consistency scores across filters
        """
        if self.merged_data is None:
            raise ValueError("Must run clean_and_merge() first")
        
        df = self.merged_data.copy()
        
        # Group by metric and filter to get lift per metric-filter combination
        metric_filter_lift = df.groupby(['METRIC', 'FILTER_ID']).agg({
            'LIFT': 'mean',
            'STATISTICAL_SIGNIFICANCE': 'mean',
            'EXPOSED_N': 'sum',
            'CONTROL_N': 'sum'
        }).reset_index()
        
        # Calculate consistency metrics per brand metric
        metric_consistency = metric_filter_lift.groupby('METRIC').agg({
            'LIFT': ['mean', 'std', 'count', lambda x: (x > min_lift).sum()],
            'STATISTICAL_SIGNIFICANCE': 'mean',
            'FILTER_ID': 'nunique'
        }).reset_index()
        
        # Flatten column names
        metric_consistency.columns = [
            'METRIC', 'AVG_LIFT', 'STD_LIFT', 'TOTAL_OBSERVATIONS',
            'POSITIVE_LIFT_COUNT', 'AVG_SIGNIFICANCE', 'UNIQUE_FILTERS'
        ]
        
        # Calculate consistency score
        # Higher score = more consistent across filters
        metric_consistency['CV'] = metric_consistency['STD_LIFT'] / metric_consistency['AVG_LIFT'].abs().replace(0, np.nan)
        metric_consistency['CONSISTENCY_SCORE'] = (
            (metric_consistency['UNIQUE_FILTERS'] / metric_consistency['UNIQUE_FILTERS'].max()) * 0.4 +  # More filters = better
            (1 / (1 + metric_consistency['CV'].fillna(999))) * 0.4 +  # Lower CV = better
            (metric_consistency['POSITIVE_LIFT_COUNT'] / metric_consistency['TOTAL_OBSERVATIONS']) * 0.2  # More positive = better
        )
        
        # Filter by criteria
        consistent_signals = metric_consistency[
            (metric_consistency['UNIQUE_FILTERS'] >= min_filters) &
            (metric_consistency['AVG_LIFT'] >= min_lift)
        ].copy()
        
        # Classify consistency
        consistent_signals['CONSISTENCY_LEVEL'] = pd.cut(
            consistent_signals['CONSISTENCY_SCORE'],
            bins=[0, 0.4, 0.7, 1.0],
            labels=['Low', 'Medium', 'High']
        )
        
        # Sort by consistency score
        consistent_signals = consistent_signals.sort_values('CONSISTENCY_SCORE', ascending=False)
        
        return consistent_signals
    
    def analyze_metric_filter_consistency(self, metric_name: Optional[str] = None) -> pd.DataFrame:
        """
        Analyze how a specific metric (or all metrics) performs across different filters.
        
        Parameters:
        -----------
        metric_name : str, optional
            Specific metric to analyze. If None, analyzes all metrics.
        
        Returns:
        --------
        pd.DataFrame
            Performance breakdown by metric and filter
        """
        if self.merged_data is None:
            raise ValueError("Must run clean_and_merge() first")
        
        df = self.merged_data.copy()
        
        # Filter by metric if specified
        if metric_name:
            df = df[df['METRIC'].str.contains(metric_name, case=False, na=False)]
        
        # Group by metric and filter dimensions
        consistency_analysis = df.groupby(['METRIC', 'FILTER_ID']).agg({
            'LIFT': ['mean', 'std', 'count'],
            'STATISTICAL_SIGNIFICANCE': 'mean',
            'CHANNEL': 'first',
            'FILTER_NAME': 'first',
            'GROUP_NAME': 'first',
            'TIME_PERIOD': 'first'
        }).reset_index()
        
        # Flatten columns
        consistency_analysis.columns = [
            'METRIC', 'FILTER_ID', 'LIFT_MEAN', 'LIFT_STD', 'OBSERVATIONS',
            'AVG_SIGNIFICANCE', 'CHANNEL', 'FILTER_NAME', 'GROUP_NAME', 'TIME_PERIOD'
        ]
        
        # Calculate CV per metric-filter combination
        consistency_analysis['CV'] = consistency_analysis['LIFT_STD'] / consistency_analysis['LIFT_MEAN'].abs().replace(0, np.nan)
        consistency_analysis['IS_CONSISTENT'] = consistency_analysis['CV'] < 0.5
        
        return consistency_analysis
    
    def identify_patterns(self, min_observations: int = 3) -> Dict:
        """
        Identify consistent patterns vs noise in lift results.
        
        Parameters:
        -----------
        min_observations : int
            Minimum number of observations to consider a pattern
        
        Returns:
        --------
        dict
            Dictionary with pattern analysis results
        """
        if self.merged_data is None:
            raise ValueError("Must run clean_and_merge() first")
        
        df = self.merged_data.copy()
        
        patterns = {}
        
        # 1. Consistency by channel
        channel_consistency = df.groupby(['CHANNEL', 'METRIC']).agg({
            'LIFT': ['mean', 'std', 'count']
        }).reset_index()
        channel_consistency.columns = ['CHANNEL', 'METRIC', 'MEAN_LIFT', 'STD_LIFT', 'COUNT']
        channel_consistency = channel_consistency[channel_consistency['COUNT'] >= min_observations]
        channel_consistency['CV'] = channel_consistency['STD_LIFT'] / channel_consistency['MEAN_LIFT'].abs()
        channel_consistency['IS_CONSISTENT'] = channel_consistency['CV'] < 0.5  # Coefficient of variation < 50%
        
        patterns['channel_consistency'] = channel_consistency
        
        # 2. Time trends (enhanced for time series analysis)
        if 'TIME_PERIOD' in df.columns or 'TIME_DATE' in df.columns:
            time_col = 'TIME_DATE' if 'TIME_DATE' in df.columns else 'TIME_PERIOD'
            time_trends = df.groupby([time_col, 'METRIC']).agg({
                'LIFT': ['mean', 'std', 'count'],
                'STATISTICAL_SIGNIFICANCE': 'mean',
                'EXPOSED_N': 'sum',
                'CONTROL_N': 'sum'
            }).reset_index()
            time_trends.columns = [time_col, 'METRIC', 'MEAN_LIFT', 'STD_LIFT', 'COUNT', 
                                   'AVG_SIGNIFICANCE', 'EXPOSED_POP', 'CONTROL_POP']
            patterns['time_trends'] = time_trends
        
        # 3. Metric performance ranking
        metric_performance = df.groupby('METRIC').agg({
            'LIFT': ['mean', 'std', 'count'],
            'STATISTICAL_SIGNIFICANCE': 'mean'
        }).reset_index()
        metric_performance.columns = ['METRIC', 'MEAN_LIFT', 'STD_LIFT', 'COUNT', 'AVG_SIG_LEVEL']
        metric_performance = metric_performance.sort_values('MEAN_LIFT', ascending=False)
        patterns['metric_performance'] = metric_performance
        
        # 4. Signal vs noise assessment
        # Metrics with high variance relative to mean are likely noise
        signal_metrics = metric_performance[
            (metric_performance['COUNT'] >= min_observations) &
            (metric_performance['STD_LIFT'] / metric_performance['MEAN_LIFT'].abs() < 1.0)
        ]
        noise_metrics = metric_performance[
            (metric_performance['COUNT'] >= min_observations) &
            (metric_performance['STD_LIFT'] / metric_performance['MEAN_LIFT'].abs() >= 1.0)
        ]
        
        patterns['signal_metrics'] = signal_metrics
        patterns['noise_metrics'] = noise_metrics
        
        # 5. Consistent signals across filters
        consistent_signals = self.find_consistent_signals(min_filters=3, min_lift=0.0)
        patterns['consistent_signals'] = consistent_signals
        
        return patterns
    
    def generate_report(self, output_dir: str = "output") -> str:
        """
        Generate a comprehensive analysis report.
        
        Parameters:
        -----------
        output_dir : str
            Directory to save report and visualizations
        
        Returns:
        --------
        str
            Path to generated report
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"\nGenerating analysis report in {output_dir}...")
        
        # Detect patterns
        patterns = self.identify_patterns()
        
        # Create visualizations
        self._create_visualizations(patterns, output_path)
        
        # Generate summary statistics
        summary = self._generate_summary(patterns)
        
        # Save report
        report_path = output_path / f"kantar_bls_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("KANTAR BRAND LIFT SURVEY - ANALYSIS REPORT\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            f.write(summary)
        
        print(f"✓ Report saved to {report_path}")
        
        return str(report_path)
    
    def plot_time_series(
        self,
        metric_name: str,
        channel: Optional[str] = None,
        save_path: Optional[Path] = None
    ):
        """
        Plot time series for a specific metric.
        
        Parameters:
        -----------
        metric_name : str
            Metric name to plot
        channel : str, optional
            Filter to specific channel
        save_path : Path, optional
            Path to save the plot. If None, displays the plot.
        """
        if self.merged_data is None:
            raise ValueError("Must run clean_and_merge() first")
        
        # Get time series data
        ts_data = self.analyze_time_series(metric_name=metric_name, channel=channel)
        
        if len(ts_data) == 0:
            print(f"No data found for metric: {metric_name}")
            return
        
        # Determine time column
        time_col = 'TIMESTAMP_DATE' if 'TIMESTAMP_DATE' in ts_data.columns else 'TIME_DATE'
        if time_col not in ts_data.columns:
            time_col = 'TIME_PERIOD'
        
        # Create plot
        fig, ax = plt.subplots(figsize=(14, 7))
        
        # Get mean lift column
        mean_col = [c for c in ts_data.columns if 'mean' in c.lower() and 'lift' in c.lower()][0] if any('mean' in c.lower() and 'lift' in c.lower() for c in ts_data.columns) else None
        std_col = [c for c in ts_data.columns if 'std' in c.lower() and 'lift' in c.lower()][0] if any('std' in c.lower() and 'lift' in c.lower() for c in ts_data.columns) else None
        
        if mean_col:
            # Convert to datetime if needed
            if time_col in ['TIMESTAMP_DATE', 'TIME_DATE']:
                ts_data[time_col] = pd.to_datetime(ts_data[time_col], errors='coerce')
                ts_data = ts_data.sort_values(time_col)
            
            # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
            ax.plot(ts_data[time_col], ts_data[mean_col] * 100, 
                    marker='o', linewidth=2, markersize=8, label='Mean Lift')
            
            # Add error bars (std)
            if std_col:
                ax.fill_between(
                    ts_data[time_col],
                    (ts_data[mean_col] - ts_data[std_col]) * 100,
                    (ts_data[mean_col] + ts_data[std_col]) * 100,
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
        """
        Plot channel comparison for a specific metric.
        
        Parameters:
        -----------
        metric_name : str
            Metric name to plot
        save_path : Path, optional
            Path to save the plot. If None, displays the plot.
        """
        if self.merged_data is None:
            raise ValueError("Must run clean_and_merge() first")
        
        # Get channel analysis data
        channel_data = self.analyze_by_channel(metric_name=metric_name, min_observations=1)
        
        if len(channel_data) == 0:
            print(f"No data found for metric: {metric_name}")
            return
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Get mean lift column
        mean_col = [c for c in channel_data.columns if 'mean' in c.lower() and 'lift' in c.lower()][0] if any('mean' in c.lower() and 'lift' in c.lower() for c in channel_data.columns) else None
        std_col = [c for c in channel_data.columns if 'std' in c.lower() and 'lift' in c.lower()][0] if any('std' in c.lower() and 'lift' in c.lower() for c in channel_data.columns) else None
        
        if mean_col:
            # Sort by mean lift
            channel_data = channel_data.sort_values(mean_col, ascending=True)
            
            # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
            bars = ax.barh(channel_data['CHANNEL'], channel_data[mean_col] * 100)
            
            # Color bars based on lift value
            colors = ['green' if x > 0 else 'red' for x in channel_data[mean_col]]
            for bar, color in zip(bars, colors):
                bar.set_color(color)
                bar.set_alpha(0.7)
            
            # Add error bars
            if std_col:
                ax.errorbar(
                    channel_data[mean_col] * 100,
                    channel_data['CHANNEL'],
                    xerr=channel_data[std_col] * 100,
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
    
    def _create_visualizations(self, patterns: Dict, output_path: Path):
        """Create visualization charts."""
        
        # 1. Lift by channel
        if 'channel_consistency' in patterns:
            fig, ax = plt.subplots(figsize=(12, 6))
            channel_data = patterns['channel_consistency'].groupby('CHANNEL')['MEAN_LIFT'].mean().sort_values()
            # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
            (channel_data * 100).plot(kind='barh', ax=ax)
            ax.set_xlabel('Average Lift (%)')
            ax.set_title('Average Brand Lift by Channel')
            ax.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
            plt.tight_layout()
            plt.savefig(output_path / 'lift_by_channel.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. Consistent signals across filters
        if 'consistent_signals' in patterns and len(patterns['consistent_signals']) > 0:
            consistent = patterns['consistent_signals'].head(20)
            
            # Scatter plot: Consistency Score vs Average Lift
            fig, ax = plt.subplots(figsize=(14, 8))
            # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
            scatter = ax.scatter(
                consistent['AVG_LIFT'] * 100,
                consistent['CONSISTENCY_SCORE'],
                s=consistent['UNIQUE_FILTERS'] * 10,
                c=consistent['UNIQUE_FILTERS'],
                cmap='viridis',
                alpha=0.6,
                edgecolors='black',
                linewidth=0.5
            )
            ax.set_xlabel('Average Lift (%)', fontsize=12)
            ax.set_ylabel('Consistency Score', fontsize=12)
            ax.set_title('Consistent Signals: Metrics with Reliable Performance Across Filters', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add metric names for top performers
            for idx, row in consistent.head(10).iterrows():
                # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
                ax.annotate(
                    row['METRIC'][:40] + '...' if len(row['METRIC']) > 40 else row['METRIC'],
                    (row['AVG_LIFT'] * 100, row['CONSISTENCY_SCORE']),
                    fontsize=8,
                    alpha=0.7
                )
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Number of Unique Filters', fontsize=10)
            
            plt.tight_layout()
            plt.savefig(output_path / 'consistent_signals.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Bar chart: Top consistent metrics
            fig, ax = plt.subplots(figsize=(14, 10))
            top_consistent = consistent.head(15)
            y_pos = range(len(top_consistent))
            ax.barh(y_pos, top_consistent['CONSISTENCY_SCORE'], color='steelblue')
            ax.set_yticks(y_pos)
            ax.set_yticklabels([name[:60] + '...' if len(name) > 60 else name 
                               for name in top_consistent['METRIC']], fontsize=9)
            ax.set_xlabel('Consistency Score', fontsize=12)
            ax.set_title('Top 15 Most Consistent Metrics Across Filters', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
            
            # Add value labels
            for i, (idx, row) in enumerate(top_consistent.iterrows()):
                ax.text(row['CONSISTENCY_SCORE'] + 0.01, i, 
                       # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
                       f"Lift: {row['AVG_LIFT']*100:.2f}% | Filters: {int(row['UNIQUE_FILTERS'])}",
                       va='center', fontsize=8)
            
            plt.tight_layout()
            plt.savefig(output_path / 'top_consistent_metrics.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. Metric performance
        if 'metric_performance' in patterns:
            top_metrics = patterns['metric_performance'].head(15)
            fig, ax = plt.subplots(figsize=(12, 8))
            # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
            ax.barh(range(len(top_metrics)), top_metrics['MEAN_LIFT'] * 100)
            ax.set_yticks(range(len(top_metrics)))
            ax.set_yticklabels([name[:60] + '...' if len(name) > 60 else name 
                               for name in top_metrics['METRIC']], fontsize=8)
            ax.set_xlabel('Average Lift (%)')
            ax.set_title('Top 15 Metrics by Average Lift')
            ax.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
            plt.tight_layout()
            plt.savefig(output_path / 'top_metrics.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Consistency heatmap
        if 'channel_consistency' in patterns:
            pivot = patterns['channel_consistency'].pivot_table(
                index='METRIC',
                columns='CHANNEL',
                values='MEAN_LIFT'
            )
            if not pivot.empty:
                fig, ax = plt.subplots(figsize=(14, max(8, len(pivot) * 0.3)))
                # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
                sns.heatmap(pivot * 100, annot=True, fmt='.1f', cmap='RdYlGn', center=0, ax=ax, cbar_kws={'label': 'Lift (%)'})
                ax.set_title('Lift Heatmap: Metrics by Channel')
                plt.tight_layout()
                plt.savefig(output_path / 'lift_heatmap.png', dpi=300, bbox_inches='tight')
                plt.close()
    
    def _generate_summary(self, patterns: Dict) -> str:
        """Generate text summary of findings."""
        summary = []
        
        summary.append("EXECUTIVE SUMMARY\n")
        summary.append("-" * 80 + "\n")
        
        if 'metric_performance' in patterns:
            top_5 = patterns['metric_performance'].head(5)
            summary.append("Top 5 Metrics by Average Lift:\n")
            for idx, row in top_5.iterrows():
                # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
                summary.append(f"  {row['METRIC']}: {row['MEAN_LIFT']*100:.2f}% (n={row['COUNT']})\n")
            summary.append("\n")
        
        if 'channel_consistency' in patterns:
            channel_summary = patterns['channel_consistency'].groupby('CHANNEL').agg({
                'MEAN_LIFT': 'mean',
                'IS_CONSISTENT': lambda x: x.sum() / len(x) * 100
            })
            summary.append("Channel Performance:\n")
            for channel, row in channel_summary.iterrows():
                # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
                summary.append(f"  {channel}: {row['MEAN_LIFT']*100:.2f}% avg lift, "
                             f"{row['IS_CONSISTENT']:.1f}% consistent metrics\n")
            summary.append("\n")
        
        if 'signal_metrics' in patterns and 'noise_metrics' in patterns:
            summary.append("Signal vs Noise:\n")
            summary.append(f"  Metrics with consistent signal: {len(patterns['signal_metrics'])}\n")
            summary.append(f"  Metrics with high noise: {len(patterns['noise_metrics'])}\n")
            summary.append("\n")
        
        if 'consistent_signals' in patterns and len(patterns['consistent_signals']) > 0:
            consistent = patterns['consistent_signals']
            top_5_consistent = consistent.head(5)
            summary.append("Consistent Signals Across Filters:\n")
            summary.append("  (Metrics that perform reliably across multiple filters/channels)\n")
            for idx, row in top_5_consistent.iterrows():
                # LIFT is stored as decimal (0.20 = 20%), so multiply by 100 for display
                summary.append(f"  {row['METRIC'][:60]}: "
                             f"Lift: {row['AVG_LIFT']*100:.2f}%, "
                             f"Filters: {int(row['UNIQUE_FILTERS'])}, "
                             f"Consistency: {row['CONSISTENCY_SCORE']:.2f}\n")
            summary.append(f"\n  Total metrics with consistent cross-filter signal: {len(consistent)}\n")
            summary.append("\n")
        
        return "".join(summary)
    
    def analyze_time_series(self, metric_name: Optional[str] = None, 
                           channel: Optional[str] = None,
                           min_observations: int = 1) -> pd.DataFrame:
        """
        Perform time series analysis of brand lift metrics over time.
        
        Based on Kantar API: Time information comes from filters call with 
        "timestamp" as GROUP_NAME containing date ranges.
        
        Parameters:
        -----------
        metric_name : str, optional
            Specific metric to analyze (e.g., "Unaided Brand Awareness")
        channel : str, optional
            Filter by specific channel (e.g., "TV", "Social")
        min_observations : int, default 1
            Minimum observations per time period
            
        Returns:
        --------
        pd.DataFrame
            Time series data with lift trends
        """
        if self.merged_data is None:
            raise ValueError("Must run clean_and_merge() first")
        
        df = self.merged_data.copy()
        
        # Filter by metric if specified
        if metric_name:
            df = df[df['METRIC'].str.contains(metric_name, case=False, na=False)]
        
        # Filter by channel if specified
        if channel:
            df = df[df['CHANNEL'] == channel]
        
        # Use TIME_DATE if available (standardized dates), otherwise TIME_PERIOD
        time_col = 'TIME_DATE' if 'TIME_DATE' in df.columns and df['TIME_DATE'].notna().any() else 'TIME_PERIOD'
        
        if time_col not in df.columns:
            raise ValueError("No time dimension found. Ensure data has TIME_PERIOD or TIME_DATE columns.")
        
        # Remove unknown/None time periods
        df = df[df[time_col].notna()]
        if time_col == 'TIME_PERIOD':
            df = df[df[time_col] != 'Unknown']
        
        # Sort by time
        if time_col == 'TIME_DATE':
            df = df.sort_values(time_col)
        else:
            df = df.sort_values(time_col)
        
        # Aggregate by time and metric
        agg_dict = {
            'LIFT': ['mean', 'std', 'count'],
            'DELTA': 'mean',
            'EXPOSED_': 'mean',
            'CONTROL_': 'mean',
            'STATISTICAL_SIGNIFICANCE': 'mean',
            'EXPOSED_N': 'sum',
            'CONTROL_N': 'sum'
        }
        
        # Only include columns that exist
        agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
        
        group_by = [time_col, 'METRIC']
        if 'CHANNEL' in df.columns:
            group_by.append('CHANNEL')
        
        results = df.groupby(group_by).agg(agg_dict).reset_index()
        results.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                          for col in results.columns.values]
        
        # Filter by minimum observations
        count_col = [c for c in results.columns if 'count' in c.lower()][0] if any('count' in c.lower() for c in results.columns) else None
        if count_col:
            results = results[results[count_col] >= min_observations]
        
        return results
    
    def analyze_by_channel(self, metric_name: Optional[str] = None,
                          time_period: Optional[str] = None,
                          min_observations: int = 3) -> pd.DataFrame:
        """
        Analyze brand lift performance by channel.
        
        Based on Kantar API: Channels are in filters call, often with "XM" prefix/folder.
        
        Parameters:
        -----------
        metric_name : str, optional
            Specific metric to analyze
        time_period : str, optional
            Filter by specific time period (e.g., "April 2025")
        min_observations : int, default 3
            Minimum observations per channel
            
        Returns:
        --------
        pd.DataFrame
            Channel performance analysis
        """
        if self.merged_data is None:
            raise ValueError("Must run clean_and_merge() first")
        
        df = self.merged_data.copy()
        
        # Filter by metric if specified
        if metric_name:
            df = df[df['METRIC'].str.contains(metric_name, case=False, na=False)]
        
        # Filter by time period if specified
        if time_period:
            if 'TIME_PERIOD' in df.columns:
                df = df[df['TIME_PERIOD'] == time_period]
            elif 'TIME_DATE' in df.columns:
                df = df[df['TIME_DATE'].astype(str).str.contains(time_period, case=False, na=False)]
        
        if 'CHANNEL' not in df.columns:
            raise ValueError("No CHANNEL dimension found. Ensure data has been processed with _extract_dimensions().")
        
        # Aggregate by channel and metric
        agg_dict = {
            'LIFT': ['mean', 'std', 'count'],
            'DELTA': 'mean',
            'EXPOSED_': 'mean',
            'CONTROL_': 'mean',
            'STATISTICAL_SIGNIFICANCE': 'mean',
            'EXPOSED_N': 'sum',
            'CONTROL_N': 'sum'
        }
        
        # Only include columns that exist
        agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}
        
        group_by = ['CHANNEL', 'METRIC']
        if 'TIME_PERIOD' in df.columns:
            group_by.append('TIME_PERIOD')
        elif 'TIME_DATE' in df.columns:
            group_by.append('TIME_DATE')
        
        results = df.groupby(group_by).agg(agg_dict).reset_index()
        results.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                          for col in results.columns.values]
        
        # Filter by minimum observations
        count_col = [c for c in results.columns if 'count' in c.lower()][0] if any('count' in c.lower() for c in results.columns) else None
        if count_col:
            results = results[results[count_col] >= min_observations]
        
        # Calculate coefficient of variation for consistency
        mean_col = [c for c in results.columns if 'mean' in c.lower() and 'lift' in c.lower()][0] if any('mean' in c.lower() and 'lift' in c.lower() for c in results.columns) else None
        std_col = [c for c in results.columns if 'std' in c.lower() and 'lift' in c.lower()][0] if any('std' in c.lower() and 'lift' in c.lower() for c in results.columns) else None
        
        if mean_col and std_col:
            results['CV'] = results[std_col] / results[mean_col].abs().replace(0, np.nan)
            results['IS_CONSISTENT'] = results['CV'] < 0.5
        
        return results
    
    def aggregate_filter_ids(self, filter_ids: List[int], 
                            metric_name: Optional[str] = None,
                            method: str = 'weighted_mean') -> pd.DataFrame:
        """
        Aggregate results from multiple filter IDs.
        
        Based on Kantar API: You can pass multiple filter IDs to the metrics call
        to combine results (e.g., "last 7 days" + "last 3 months").
        
        Parameters:
        -----------
        filter_ids : list of int
            List of FILTER_IDs to aggregate
        metric_name : str, optional
            Specific metric to analyze
        method : str, default 'weighted_mean'
            Aggregation method: 'weighted_mean' (by population), 'mean', or 'sum'
            
        Returns:
        --------
        pd.DataFrame
            Aggregated results across the specified filter IDs
        """
        if self.merged_data is None:
            raise ValueError("Must run clean_and_merge() first")
        
        df = self.merged_data.copy()
        
        # Filter by specified filter IDs
        df = df[df['FILTER_ID'].isin(filter_ids)]
        
        if len(df) == 0:
            raise ValueError(f"No data found for filter IDs: {filter_ids}")
        
        # Filter by metric if specified
        if metric_name:
            df = df[df['METRIC'].str.contains(metric_name, case=False, na=False)]
        
        # Aggregate based on method
        if method == 'weighted_mean':
            # Weight by population size
            if 'EXPOSED_N' in df.columns and 'CONTROL_N' in df.columns:
                df['TOTAL_POPULATION'] = df['EXPOSED_N'] + df['CONTROL_N']
                df['WEIGHTED_LIFT'] = df['LIFT'] * df['TOTAL_POPULATION']
                
                results = df.groupby('METRIC').agg({
                    'WEIGHTED_LIFT': 'sum',
                    'TOTAL_POPULATION': 'sum',
                    'LIFT': ['mean', 'std', 'count'],
                    'DELTA': 'mean',
                    'STATISTICAL_SIGNIFICANCE': 'mean',
                    'EXPOSED_N': 'sum',
                    'CONTROL_N': 'sum'
                }).reset_index()
                
                results['AGGREGATED_LIFT'] = results['WEIGHTED_LIFT'] / results['TOTAL_POPULATION']
                results = results.drop(columns=['WEIGHTED_LIFT'])
            else:
                method = 'mean'  # Fallback if population columns not available
        
        if method == 'mean':
            results = df.groupby('METRIC').agg({
                'LIFT': ['mean', 'std', 'count'],
                'DELTA': 'mean',
                'EXPOSED_': 'mean',
                'CONTROL_': 'mean',
                'STATISTICAL_SIGNIFICANCE': 'mean',
                'EXPOSED_N': 'sum',
                'CONTROL_N': 'sum'
            }).reset_index()
        
        elif method == 'sum':
            results = df.groupby('METRIC').agg({
                'LIFT': 'sum',
                'DELTA': 'sum',
                'EXPOSED_N': 'sum',
                'CONTROL_N': 'sum'
            }).reset_index()
        
        # Flatten column names
        results.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                          for col in results.columns.values]
        
        # Add metadata
        results['FILTER_IDS'] = str(filter_ids)
        results['NUM_FILTERS'] = len(filter_ids)
        
        return results
    
    def save_analysis_results(self, results: pd.DataFrame, 
                             filename: str,
                             output_dir: str = "output",
                             format: str = "csv") -> str:
        """
        Save analysis results to a file.
        
        Parameters:
        -----------
        results : pd.DataFrame
            Analysis results to save
        filename : str
            Name of the output file (without extension)
        output_dir : str, default "output"
            Directory to save the file
        format : str, default "csv"
            File format: "csv" or "excel"
            
        Returns:
        --------
        str
            Path to saved file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        if format.lower() == "csv":
            file_path = output_path / f"{filename}.csv"
            results.to_csv(file_path, index=False)
        elif format.lower() in ["excel", "xlsx"]:
            if not EXCEL_SUPPORT:
                raise ImportError("Excel support requires openpyxl. Install with: pip install openpyxl")
            file_path = output_path / f"{filename}.xlsx"
            results.to_excel(file_path, index=False, engine='openpyxl')
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv' or 'excel'.")
        
        file_size = file_path.stat().st_size / (1024 * 1024)  # MB
        print(f"✓ Saved analysis results: {file_path} ({len(results):,} rows, {file_size:.2f} MB)")
        
        return str(file_path)
    
    def save_time_series_analysis(self, 
                                  metric_name: Optional[str] = None,
                                  channel: Optional[str] = None,
                                  output_dir: str = "output",
                                  format: str = "csv") -> str:
        """
        Perform time series analysis and save results to file.
        
        Parameters:
        -----------
        metric_name : str, optional
            Specific metric to analyze
        channel : str, optional
            Filter by specific channel
        output_dir : str, default "output"
            Directory to save the file
        format : str, default "csv"
            File format: "csv" or "excel"
            
        Returns:
        --------
        str
            Path to saved file
        """
        results = self.analyze_time_series(metric_name=metric_name, channel=channel)
        
        # Create descriptive filename
        filename_parts = ["time_series"]
        if metric_name:
            filename_parts.append(metric_name.replace(" ", "_").replace("/", "_")[:30])
        if channel:
            filename_parts.append(channel)
        filename = "_".join(filename_parts) + f"_{datetime.now().strftime('%Y%m%d')}"
        
        return self.save_analysis_results(results, filename, output_dir, format)
    
    def save_channel_analysis(self,
                              metric_name: Optional[str] = None,
                              time_period: Optional[str] = None,
                              output_dir: str = "output",
                              format: str = "csv") -> str:
        """
        Perform channel analysis and save results to file.
        
        Parameters:
        -----------
        metric_name : str, optional
            Specific metric to analyze
        time_period : str, optional
            Filter by specific time period
        output_dir : str, default "output"
            Directory to save the file
        format : str, default "csv"
            File format: "csv" or "excel"
            
        Returns:
        --------
        str
            Path to saved file
        """
        results = self.analyze_by_channel(metric_name=metric_name, time_period=time_period)
        
        # Create descriptive filename
        filename_parts = ["channel_analysis"]
        if metric_name:
            filename_parts.append(metric_name.replace(" ", "_").replace("/", "_")[:30])
        if time_period:
            filename_parts.append(time_period.replace(" ", "_").replace("/", "_")[:20])
        filename = "_".join(filename_parts) + f"_{datetime.now().strftime('%Y%m%d')}"
        
        return self.save_analysis_results(results, filename, output_dir, format)
    
    def save_all_analysis_results(self, output_dir: str = "output", format: str = "csv") -> Dict[str, str]:
        """
        Run all analyses and save results to files.
        
        Parameters:
        -----------
        output_dir : str, default "output"
            Directory to save files
        format : str, default "csv"
            File format: "csv" or "excel"
            
        Returns:
        --------
        dict
            Dictionary mapping analysis type to file path
        """
        saved_files = {}
        
        print("\n" + "=" * 80)
        print("SAVING ALL ANALYSIS RESULTS")
        print("=" * 80)
        print()
        
        # 1. Time series analysis
        print("1. Saving time series analysis...")
        try:
            time_series = self.analyze_time_series()
            filename = f"time_series_all_metrics_{datetime.now().strftime('%Y%m%d')}"
            file_path = self.save_analysis_results(time_series, filename, output_dir, format)
            saved_files['time_series'] = file_path
        except Exception as e:
            print(f"  Warning: Could not save time series: {str(e)}")
        
        # 2. Channel analysis
        print("\n2. Saving channel analysis...")
        try:
            channel_analysis = self.analyze_by_channel()
            filename = f"channel_analysis_all_metrics_{datetime.now().strftime('%Y%m%d')}"
            file_path = self.save_analysis_results(channel_analysis, filename, output_dir, format)
            saved_files['channel_analysis'] = file_path
        except Exception as e:
            print(f"  Warning: Could not save channel analysis: {str(e)}")
        
        # 3. Consistent signals
        print("\n3. Saving consistent signals...")
        try:
            consistent_signals = self.find_consistent_signals()
            filename = f"consistent_signals_{datetime.now().strftime('%Y%m%d')}"
            file_path = self.save_analysis_results(consistent_signals, filename, output_dir, format)
            saved_files['consistent_signals'] = file_path
        except Exception as e:
            print(f"  Warning: Could not save consistent signals: {str(e)}")
        
        # 4. Trend analysis
        print("\n4. Saving trend analysis...")
        try:
            trends = self.analyze_trends(group_by=['CHANNEL', 'METRIC'])
            filename = f"trends_by_channel_metric_{datetime.now().strftime('%Y%m%d')}"
            file_path = self.save_analysis_results(trends, filename, output_dir, format)
            saved_files['trends'] = file_path
        except Exception as e:
            print(f"  Warning: Could not save trends: {str(e)}")
        
        # 5. Significant results
        print("\n5. Saving significant results...")
        try:
            significant = self.detect_significance()
            filename = f"significant_results_{datetime.now().strftime('%Y%m%d')}"
            file_path = self.save_analysis_results(significant, filename, output_dir, format)
            saved_files['significant_results'] = file_path
        except Exception as e:
            print(f"  Warning: Could not save significant results: {str(e)}")
        
        # 6. Pattern analysis
        print("\n6. Saving pattern analysis...")
        try:
            patterns = self.identify_patterns()
            
            # Save each pattern type
            for pattern_name, pattern_data in patterns.items():
                if isinstance(pattern_data, pd.DataFrame):
                    filename = f"pattern_{pattern_name}_{datetime.now().strftime('%Y%m%d')}"
                    file_path = self.save_analysis_results(pattern_data, filename, output_dir, format)
                    saved_files[f'pattern_{pattern_name}'] = file_path
        except Exception as e:
            print(f"  Warning: Could not save patterns: {str(e)}")
        
        print("\n" + "=" * 80)
        print(f"✓ Saved {len(saved_files)} analysis result files")
        print("=" * 80)
        print("\nSaved files:")
        for analysis_type, file_path in saved_files.items():
            print(f"  {analysis_type}: {file_path}")
        
        return saved_files
    
    def enable_logging(self, log_file: str = None, output_dir: str = "output") -> str:
        """
        Enable logging of all console output to a file.
        
        Parameters:
        -----------
        log_file : str, optional
            Name of the log file. If None, auto-generates with timestamp.
        output_dir : str, default "output"
            Directory to save the log file
            
        Returns:
        --------
        str
            Path to the log file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        if log_file is None:
            log_file = f"analysis_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        log_path = output_path / log_file
        
        # Create TeeOutput to capture both console and file
        self.log_file = TeeOutput(log_path)
        self.log_enabled = True
        
        # Redirect stdout
        self.original_stdout = sys.stdout
        sys.stdout = self.log_file
        
        print("=" * 80)
        print("ANALYSIS LOGGING ENABLED")
        print("=" * 80)
        print(f"Log file: {log_path}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        
        return str(log_path)
    
    def disable_logging(self):
        """Disable logging and restore normal console output."""
        if self.log_enabled and self.log_file:
            print()
            print("=" * 80)
            print(f"Logging ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)
            
            sys.stdout = self.original_stdout
            self.log_file.close()
            self.log_enabled = False
            self.log_file = None
            print("✓ Logging disabled. Console output restored.")


def main():
    """
    Main execution function - unified analysis pipeline.
    
    This function provides a comprehensive analysis workflow that handles:
    - Both old and new data formats
    - Time series analysis
    - Channel analysis
    - Pattern detection
    - Visualization generation
    - Report generation
    """
    print("=" * 80)
    print("KANTAR BLS COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    print()
    
    # Initialize analyzer (uses default data_dir: ../data)
    analyzer = KantarBLSAnalyzer()
    
    # Load data
    analyzer.load_data(use_snowflake=False)
    
    # Clean and merge (saves merged data automatically)
    # If merged file was loaded, clean_and_merge will detect it and skip merge
    analyzer.clean_and_merge(save_merged=True)
    
    # Analyze trends
    print("\n" + "=" * 80)
    print("ANALYZING TRENDS")
    print("=" * 80)
    trends = analyzer.analyze_trends(group_by=['CHANNEL', 'METRIC'])
    print(f"✓ Found {len(trends)} trend combinations")
    
    # Detect significance
    print("\n" + "=" * 80)
    print("DETECTING SIGNIFICANT RESULTS")
    print("=" * 80)
    significant = analyzer.detect_significance()
    sig_count = significant['IS_SIGNIFICANT'].sum() if 'IS_SIGNIFICANT' in significant.columns else 0
    print(f"✓ Found {sig_count:,} significant results")
    
    # Identify patterns
    print("\n" + "=" * 80)
    print("IDENTIFYING PATTERNS")
    print("=" * 80)
    patterns = analyzer.identify_patterns()
    print(f"✓ Analyzed {len(patterns)} pattern categories")
    
    # Time series analysis (if timestamps are available)
    print("\n" + "=" * 80)
    print("TIME SERIES ANALYSIS")
    print("=" * 80)
    try:
        time_series = analyzer.analyze_time_series()
        print(f"✓ Generated {len(time_series):,} time series data points")
    except Exception as e:
        print(f"⚠ Time series analysis skipped: {str(e)}")
        time_series = None
    
    # Channel analysis
    print("\n" + "=" * 80)
    print("CHANNEL ANALYSIS")
    print("=" * 80)
    try:
        channel_analysis = analyzer.analyze_by_channel()
        print(f"✓ Generated {len(channel_analysis):,} channel-metric combinations")
    except Exception as e:
        print(f"⚠ Channel analysis skipped: {str(e)}")
        channel_analysis = None
    
    # Generate report in output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    print("\n" + "=" * 80)
    print("GENERATING REPORT AND VISUALIZATIONS")
    print("=" * 80)
    report_path = analyzer.generate_report(output_dir=str(output_dir))
    print(f"✓ Report saved to: {report_path}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nAll outputs saved to: {output_dir}")
    
    return analyzer, patterns


if __name__ == "__main__":
    analyzer, patterns = main()
