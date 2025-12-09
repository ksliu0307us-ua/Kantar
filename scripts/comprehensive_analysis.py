"""
🟣 KANTAR BRAND LIFT ANALYSIS PIPELINE (DOORDASH)

Goal: 
Build a full analysis pipeline using the following Kantar BLS survey data to:
• Analyze brand lift trends by channel, month, and demographic
• Separate signal from noise in the aggregate outputs
• Validate consistency across time and filters

Input files:
- 'kantar_bls_transformed_data.csv': main aggregate output (with timestamp parsed from LIMITING_FILTER)
- 'kantar_bls_filter_ids.csv': filter metadata (GROUP_NAME, FILTER_NAME, etc.)
- 'kantar_bls_filters.csv': filter group taxonomy (e.g. demo, channel, region, recency)

Tasks:
1. Read all CSVs into DataFrames
2. Merge transformed_data with filter_ids and filters using FILTER_ID and ID
3. Extract `survey_month` (format YYYY-MM) from the LIMITING_FILTER column
4. Save merged result as `merged_kantar_data.csv`
5. Perform analysis:
   - Average LIFT_PERCENTAGE by survey_month and GROUP_NAME (channel, age, etc.)
   - Highlight top 5 and bottom 5 filters by average lift
   - Identify filters with high standard deviation (unstable patterns)
   - Create pivot tables or charts for:
       a. LIFT_PERCENTAGE over time by top channels
       b. LIFT_PERCENTAGE boxplots by demographic
6. Save plots to disk
7. Output findings to a text file: `kantar_analysis_summary.txt`
   - Include narrative summary of key trends, stable filters, and notable anomalies
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
import sys
import re
from typing import Optional, Dict
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
        self.filter_ids = None
        self.filters = None
        self.merged_data = None
        
    def load_all_data(self):
        """Task 1: Read all CSVs into DataFrames."""
        print("=" * 80)
        print("TASK 1: LOADING ALL DATA")
        print("=" * 80)
        print()
        
        # 1. Load transformed data (primary source)
        transformed_file = self.data_dir / "kantar_bls_transformed_data.csv"
        if transformed_file.exists():
            print(f"Loading transformed data: {transformed_file.name}")
            self.transformed_data = pd.read_csv(transformed_file, low_memory=False)
            print(f"  ✓ Loaded {len(self.transformed_data):,} rows")
            print(f"  Columns: {list(self.transformed_data.columns)}")
            print()
        else:
            raise FileNotFoundError(f"Required file not found: {transformed_file}")
        
        # 2. Load filter_ids
        filter_ids_file = self.data_dir / "kantar_bls_filter_ids.csv"
        if filter_ids_file.exists():
            print(f"Loading filter IDs: {filter_ids_file.name}")
            self.filter_ids = pd.read_csv(filter_ids_file, low_memory=False)
            print(f"  ✓ Loaded {len(self.filter_ids):,} rows")
            print(f"  Columns: {list(self.filter_ids.columns)}")
            print()
        else:
            raise FileNotFoundError(f"Required file not found: {filter_ids_file}")
        
        # 3. Load filters
        filters_file = self.data_dir / "kantar_bls_filters.csv"
        if filters_file.exists():
            print(f"Loading filters: {filters_file.name}")
            self.filters = pd.read_csv(filters_file, low_memory=False)
            print(f"  ✓ Loaded {len(self.filters):,} rows")
            print(f"  Columns: {list(self.filters.columns)}")
            print()
        else:
            raise FileNotFoundError(f"Required file not found: {filters_file}")
        
        print("✓ All data loaded successfully!")
        print()
    
    def extract_survey_month(self, limiting_filter: str) -> Optional[str]:
        """
        Extract survey_month (YYYY-MM format) from LIMITING_FILTER column.
        
        Handles formats like:
        - "Timestamp: 3/1/25-3/31/25" -> "2025-03"
        - "Timestamp: 4/1/25-6/30/25" -> "2025-04" (uses start date)
        - Other date formats
        """
        if pd.isna(limiting_filter) or not isinstance(limiting_filter, str):
            return None
        
        # Pattern 1: "Timestamp: M/D/YY-M/D/YY"
        pattern1 = r'Timestamp:\s*(\d{1,2})/(\d{1,2})/(\d{2,4})'
        match = re.search(pattern1, limiting_filter, re.IGNORECASE)
        if match:
            month, day, year = match.groups()
            year = int(year)
            if year < 100:
                year += 2000  # Convert 2-digit to 4-digit year
            month = int(month)
            return f"{year:04d}-{month:02d}"
        
        # Pattern 2: Look for YYYY-MM format directly
        pattern2 = r'(\d{4})-(\d{2})'
        match = re.search(pattern2, limiting_filter)
        if match:
            year, month = match.groups()
            return f"{year}-{month}"
        
        # Pattern 3: Look for month names
        month_map = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        for month_name, month_num in month_map.items():
            pattern = rf'\b{month_name}\s+(\d{4})\b'
            match = re.search(pattern, limiting_filter, re.IGNORECASE)
            if match:
                year = match.group(1)
                return f"{year}-{month_num}"
        
        return None
    
    def merge_data(self):
        """
        Task 2 & 3: Merge transformed_data with filter_ids and filters.
        Extract survey_month from LIMITING_FILTER.
        Save merged result as merged_kantar_data.csv
        """
        print("=" * 80)
        print("TASK 2 & 3: MERGING DATA AND EXTRACTING SURVEY_MONTH")
        print("=" * 80)
        print()
        
        if self.transformed_data is None or self.filter_ids is None or self.filters is None:
            raise ValueError("Please load all data first using load_all_data()")
        
        df = self.transformed_data.copy()
        
        # Step 1: Merge with filter_ids using FILTER_ID
        print("Merging with kantar_bls_filter_ids...")
        
        # Try to find or extract FILTER_ID
        if 'FILTER_ID' not in df.columns:
            # Try to extract FILTER_ID from EXPOSED_FILTER or CONTROL_FILTER
            print("  FILTER_ID not found in transformed_data, attempting to extract from EXPOSED_FILTER/CONTROL_FILTER...")
            
            def extract_filter_id(row):
                """Try to extract numeric FILTER_ID from filter columns."""
                import re
                # Check EXPOSED_FILTER first
                if 'EXPOSED_FILTER' in row.index and pd.notna(row.get('EXPOSED_FILTER')):
                    exp_filter = str(row['EXPOSED_FILTER'])
                    # Look for numeric ID pattern
                    match = re.search(r'(\d{6,})', exp_filter)  # Look for 6+ digit numbers
                    if match:
                        return int(match.group(1))
                
                # Check CONTROL_FILTER
                if 'CONTROL_FILTER' in row.index and pd.notna(row.get('CONTROL_FILTER')):
                    ctrl_filter = str(row['CONTROL_FILTER'])
                    match = re.search(r'(\d{6,})', ctrl_filter)
                    if match:
                        return int(match.group(1))
                
                return None
            
            df['FILTER_ID'] = df.apply(extract_filter_id, axis=1)
            extracted_count = df['FILTER_ID'].notna().sum()
            print(f"  ✓ Extracted FILTER_ID for {extracted_count:,} rows ({extracted_count/len(df)*100:.1f}%)")
        
        # Now merge with filter_ids
        if 'FILTER_ID' in df.columns:
            # Convert FILTER_ID to numeric if it exists and has values
            if df['FILTER_ID'].notna().any():
                # Convert to int64 to match filter_ids
                df['FILTER_ID'] = pd.to_numeric(df['FILTER_ID'], errors='coerce')
                
                # Check if filter_ids has FILTER_ID or ID column
                if 'FILTER_ID' in self.filter_ids.columns:
                    # Ensure types match
                    self.filter_ids['FILTER_ID'] = pd.to_numeric(self.filter_ids['FILTER_ID'], errors='coerce')
                    df = df.merge(self.filter_ids, on='FILTER_ID', how='left', suffixes=('', '_filter_ids'))
                    print(f"  ✓ Merged on FILTER_ID: {len(df):,} rows")
                elif 'ID' in self.filter_ids.columns:
                    # Ensure types match
                    self.filter_ids['ID'] = pd.to_numeric(self.filter_ids['ID'], errors='coerce')
                    df = df.merge(self.filter_ids, left_on='FILTER_ID', right_on='ID', how='left', suffixes=('', '_filter_ids'))
                    print(f"  ✓ Merged on FILTER_ID=ID: {len(df):,} rows")
                else:
                    print("  ⚠ Warning: Cannot find FILTER_ID or ID column in filter_ids, skipping merge")
            else:
                print("  ⚠ Warning: No valid FILTER_ID values extracted, proceeding without filter_ids merge")
                # Remove the empty FILTER_ID column
                df = df.drop(columns=['FILTER_ID'])
        else:
            print("  ⚠ Warning: Could not create FILTER_ID column, proceeding without filter_ids merge")
        
        # Step 2: Merge with filters using FILTER_ID and ID
        print("Merging with kantar_bls_filters...")
        if 'FILTER_ID' in df.columns and df['FILTER_ID'].notna().any():
            # Ensure FILTER_ID is numeric
            df['FILTER_ID'] = pd.to_numeric(df['FILTER_ID'], errors='coerce')
            
            if 'ID' in self.filters.columns:
                # Ensure types match
                self.filters['ID'] = pd.to_numeric(self.filters['ID'], errors='coerce')
                df = df.merge(self.filters, left_on='FILTER_ID', right_on='ID', how='left', suffixes=('', '_filters'))
                print(f"  ✓ Merged on FILTER_ID=ID: {len(df):,} rows")
            elif 'FILTER_ID' in self.filters.columns:
                # Ensure types match
                self.filters['FILTER_ID'] = pd.to_numeric(self.filters['FILTER_ID'], errors='coerce')
                df = df.merge(self.filters, on='FILTER_ID', how='left', suffixes=('', '_filters'))
                print(f"  ✓ Merged on FILTER_ID: {len(df):,} rows")
            else:
                print("  ⚠ Warning: Cannot find ID or FILTER_ID column in filters, skipping merge")
        else:
            print("  ⚠ Warning: FILTER_ID column missing or empty, proceeding without filters merge")
        
        # Step 3: Extract survey_month from LIMITING_FILTER
        print("Extracting survey_month from LIMITING_FILTER...")
        if 'LIMITING_FILTER' in df.columns:
            df['survey_month'] = df['LIMITING_FILTER'].apply(self.extract_survey_month)
            extracted_count = df['survey_month'].notna().sum()
            print(f"  ✓ Extracted survey_month for {extracted_count:,} rows ({extracted_count/len(df)*100:.1f}%)")
        else:
            print("  ⚠ Warning: LIMITING_FILTER column not found")
            df['survey_month'] = None
        
        # Step 4: Identify and standardize LIFT_PERCENTAGE column
        print("Identifying lift column...")
        lift_col = None
        for col in ['LIFT_PERCENTAGE', 'LIFT', 'lift', 'LIFT_PCT', 'DELTA']:
            if col in df.columns:
                lift_col = col
                break
        
        if lift_col is None:
            print("  ⚠ Warning: Could not find lift column. Available columns:", list(df.columns)[:10])
        else:
            print(f"  ✓ Using lift column: {lift_col}")
            # Standardize to LIFT_PERCENTAGE for consistency
            if lift_col != 'LIFT_PERCENTAGE':
                df['LIFT_PERCENTAGE'] = pd.to_numeric(df[lift_col], errors='coerce')
        
        # Step 5: Extract GROUP_NAME from other columns if merge failed
        if 'GROUP_NAME' not in df.columns:
            print("Extracting GROUP_NAME from available columns...")
            def extract_group_name(row):
                """Extract GROUP_NAME from WEIGHT_SET or EXPOSED_FILTER."""
                import re
                # Check WEIGHT_SET first
                if 'WEIGHT_SET' in row.index and pd.notna(row.get('WEIGHT_SET')):
                    weight_set = str(row['WEIGHT_SET'])
                    # Pattern: "XM: N. Channel" or "XM: Channel"
                    patterns = [
                        r'XM:\s*\d+\.\s*(\w+)',  # "XM: 2. Social"
                        r'XM:\s*(\w+)',  # "XM: Social"
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, weight_set, re.IGNORECASE)
                        if match:
                            channel = match.group(1).strip()
                            if channel.lower() in ['any', 'all']:
                                return "Any"
                            if channel.lower().startswith('digital'):
                                return "Digital"
                            return channel.title()
                
                # Check EXPOSED_FILTER
                if 'EXPOSED_FILTER' in row.index and pd.notna(row.get('EXPOSED_FILTER')):
                    exp_filter = str(row['EXPOSED_FILTER'])
                    patterns = [
                        r'XM:\s*\d+\.\s*(\w+)',
                        r'XM:\s*(\w+)',
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, exp_filter, re.IGNORECASE)
                        if match:
                            channel = match.group(1).strip()
                            if channel.lower() in ['any', 'all']:
                                return "Any"
                            if channel.lower().startswith('digital'):
                                return "Digital"
                            return channel.title()
                
                return "Other"
            
            df['GROUP_NAME'] = df.apply(extract_group_name, axis=1)
            print(f"  ✓ Extracted GROUP_NAME for {df['GROUP_NAME'].notna().sum():,} rows")
        
        # Step 6: Save merged data
        merged_file = self.output_dir / "merged_kantar_data.csv"
        df.to_csv(merged_file, index=False)
        print(f"  ✓ Saved merged data: {merged_file.name}")
        print()
        
        self.merged_data = df
        return df
    
    def analyze_lift_by_month_and_group(self) -> pd.DataFrame:
        """Task 5a: Calculate average LIFT_PERCENTAGE by survey_month and GROUP_NAME."""
        print("=" * 80)
        print("TASK 5A: AVERAGE LIFT BY MONTH AND GROUP")
        print("=" * 80)
        print()
        
        if self.merged_data is None:
            raise ValueError("Please run merge_data() first")
        
        df = self.merged_data.copy()
        
        # Find GROUP_NAME column (may have suffixes from merge)
        group_col = None
        for col in ['GROUP_NAME', 'GROUP_NAME_filter_ids', 'GROUP_NAME_filters']:
            if col in df.columns:
                group_col = col
                break
        
        if group_col is None:
            print("  ⚠ Warning: GROUP_NAME column not found. Available columns:", list(df.columns)[:20])
            return pd.DataFrame()
        
        # Filter out rows with missing data
        analysis_df = df[df['survey_month'].notna() & df['LIFT_PERCENTAGE'].notna()].copy()
        
        if len(analysis_df) == 0:
            print("  ⚠ Warning: No data with both survey_month and LIFT_PERCENTAGE")
            return pd.DataFrame()
        
        # Group by survey_month and GROUP_NAME
        result = analysis_df.groupby(['survey_month', group_col]).agg({
            'LIFT_PERCENTAGE': ['mean', 'std', 'count', 'min', 'max']
        }).reset_index()
        
        result.columns = ['survey_month', 'GROUP_NAME', 'avg_lift', 'std_lift', 'count', 'min_lift', 'max_lift']
        result = result.sort_values(['survey_month', 'avg_lift'], ascending=[True, False])
        
        print(f"  ✓ Analyzed {len(result)} combinations")
        print(f"  Date range: {result['survey_month'].min()} to {result['survey_month'].max()}")
        print(f"  Unique groups: {result['GROUP_NAME'].nunique()}")
        print()
        
        # Save to CSV
        output_file = self.output_dir / "lift_by_month_and_group.csv"
        result.to_csv(output_file, index=False)
        print(f"  ✓ Saved: {output_file.name}")
        print()
        
        return result
    
    def identify_top_bottom_filters(self) -> Dict[str, pd.DataFrame]:
        """Task 5b: Identify top 5 and bottom 5 filters by average lift."""
        print("=" * 80)
        print("TASK 5B: TOP AND BOTTOM FILTERS BY LIFT")
        print("=" * 80)
        print()
        
        if self.merged_data is None:
            raise ValueError("Please run merge_data() first")
        
        df = self.merged_data.copy()
        
        # Find filter name column
        filter_name_col = None
        for col in ['FILTER_NAME', 'NAME', 'NAME_filter_ids', 'NAME_filters']:
            if col in df.columns:
                filter_name_col = col
                break
        
        if filter_name_col is None:
            print("  ⚠ Warning: Could not find filter name column")
            return {}
        
        # Calculate average lift by filter
        filter_stats = df.groupby(filter_name_col).agg({
            'LIFT_PERCENTAGE': ['mean', 'std', 'count']
        }).reset_index()
        filter_stats.columns = ['FILTER_NAME', 'avg_lift', 'std_lift', 'count']
        filter_stats = filter_stats.sort_values('avg_lift', ascending=False)
        
        # Get top 5 and bottom 5
        top_5 = filter_stats.head(5).copy()
        bottom_5 = filter_stats.tail(5).copy()
        
        print("Top 5 Filters by Average Lift:")
        print("-" * 80)
        for i, (_, row) in enumerate(top_5.iterrows(), 1):
            print(f"  {i}. {row['FILTER_NAME']}: {row['avg_lift']:.2f}% (std={row['std_lift']:.2f}, n={row['count']})")
        print()
        
        print("Bottom 5 Filters by Average Lift:")
        print("-" * 80)
        for i, (_, row) in enumerate(bottom_5.iterrows(), 1):
            print(f"  {i}. {row['FILTER_NAME']}: {row['avg_lift']:.2f}% (std={row['std_lift']:.2f}, n={row['count']})")
        print()
        
        # Save to CSV
        top_file = self.output_dir / "top_5_filters.csv"
        bottom_file = self.output_dir / "bottom_5_filters.csv"
        top_5.to_csv(top_file, index=False)
        bottom_5.to_csv(bottom_file, index=False)
        print(f"  ✓ Saved: {top_file.name}, {bottom_file.name}")
        print()
        
        return {'top_5': top_5, 'bottom_5': bottom_5, 'all_filters': filter_stats}
    
    def identify_unstable_patterns(self, std_threshold: float = None) -> pd.DataFrame:
        """Task 5c: Identify filters with high standard deviation (unstable patterns)."""
        print("=" * 80)
        print("TASK 5C: IDENTIFYING UNSTABLE PATTERNS")
        print("=" * 80)
        print()
        
        if self.merged_data is None:
            raise ValueError("Please run merge_data() first")
        
        df = self.merged_data.copy()
        
        # Find filter name column
        filter_name_col = None
        for col in ['FILTER_NAME', 'NAME', 'NAME_filter_ids', 'NAME_filters']:
            if col in df.columns:
                filter_name_col = col
                break
        
        if filter_name_col is None:
            print("  ⚠ Warning: Could not find filter name column")
            return pd.DataFrame()
        
        # Calculate statistics by filter
        filter_stats = df.groupby(filter_name_col).agg({
            'LIFT_PERCENTAGE': ['mean', 'std', 'count', 'min', 'max']
        }).reset_index()
        filter_stats.columns = ['FILTER_NAME', 'avg_lift', 'std_lift', 'count', 'min_lift', 'max_lift']
        
        # Calculate coefficient of variation (CV) as stability metric
        filter_stats['cv'] = filter_stats['std_lift'] / filter_stats['avg_lift'].abs().replace(0, np.nan)
        filter_stats['range'] = filter_stats['max_lift'] - filter_stats['min_lift']
        
        # If no threshold provided, use 75th percentile of CV
        if std_threshold is None:
            std_threshold = filter_stats['cv'].quantile(0.75)
        
        # Identify unstable patterns (high CV or high range)
        unstable = filter_stats[
            (filter_stats['cv'] > std_threshold) | 
            (filter_stats['range'] > filter_stats['range'].quantile(0.75))
        ].sort_values('cv', ascending=False)
        
        print(f"Unstable Patterns (CV > {std_threshold:.2f} or high range):")
        print("-" * 80)
        print(f"  Found {len(unstable)} unstable filters out of {len(filter_stats)} total")
        print()
        
        if len(unstable) > 0:
            print("Top 10 Most Unstable Filters:")
            for i, (_, row) in enumerate(unstable.head(10).iterrows(), 1):
                print(f"  {i}. {row['FILTER_NAME']}: CV={row['cv']:.2f}, Range={row['range']:.2f}%, Avg={row['avg_lift']:.2f}%")
            print()
        
        # Save to CSV
        output_file = self.output_dir / "unstable_patterns.csv"
        unstable.to_csv(output_file, index=False)
        print(f"  ✓ Saved: {output_file.name}")
        print()
        
        return unstable
    
    def create_visualizations(self):
        """Task 5d & 6: Create pivot tables and charts for lift analysis. Save plots to disk."""
        print("=" * 80)
        print("TASK 5D & 6: CREATING VISUALIZATIONS")
        print("=" * 80)
        print()
        
        if self.merged_data is None:
            raise ValueError("Please run merge_data() first")
        
        df = self.merged_data.copy()
        
        # Find GROUP_NAME column
        group_col = None
        for col in ['GROUP_NAME', 'GROUP_NAME_filter_ids', 'GROUP_NAME_filters']:
            if col in df.columns:
                group_col = col
                break
        
        if group_col is None:
            print("  ⚠ Warning: GROUP_NAME column not found")
            return
        
        # Filter valid data
        analysis_df = df[df['survey_month'].notna() & df['LIFT_PERCENTAGE'].notna()].copy()
        
        if len(analysis_df) == 0:
            print("  ⚠ Warning: No data with both survey_month and LIFT_PERCENTAGE")
            return
        
        # 5d-a: LIFT_PERCENTAGE over time by top channels
        print("5d-a. Creating time series plot by top channels...")
        if group_col:
            # Identify channels (assuming GROUP_NAME contains channel info)
            # Get top channels by average lift
            channel_avg = analysis_df.groupby(group_col)['LIFT_PERCENTAGE'].mean().sort_values(ascending=False)
            top_channels = channel_avg.head(10).index.tolist()
            
            pivot_time = analysis_df[analysis_df[group_col].isin(top_channels)].pivot_table(
                index='survey_month',
                columns=group_col,
                values='LIFT_PERCENTAGE',
                aggfunc='mean'
            )
            
            if not pivot_time.empty:
                fig, ax = plt.subplots(figsize=(14, 8))
                for col in pivot_time.columns:
                    ax.plot(pivot_time.index, pivot_time[col], marker='o', label=col, linewidth=2, markersize=6)
                ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)
                ax.set_xlabel('Survey Month', fontsize=12)
                ax.set_ylabel('Average Lift (%)', fontsize=12)
                ax.set_title('Lift Over Time by Top Channels', fontsize=14, fontweight='bold')
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(self.output_dir / 'lift_over_time_by_channel.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  ✓ Saved: lift_over_time_by_channel.png")
        
        # 5d-b: LIFT_PERCENTAGE boxplots by demographic
        print("5d-b. Creating boxplots by demographic...")
        # Use GROUP_NAME as proxy for demographic, or find actual demographic column
        demo_col = group_col  # Use GROUP_NAME as proxy
        
        if demo_col and analysis_df[demo_col].nunique() <= 20:  # Only if reasonable number of categories
            # Get top demographics by count
            demo_counts = analysis_df[demo_col].value_counts().head(10)
            demo_groups = demo_counts.index.tolist()
            demo_data = [analysis_df[analysis_df[demo_col] == group]['LIFT_PERCENTAGE'].dropna().values 
                        for group in demo_groups if len(analysis_df[analysis_df[demo_col] == group]) > 0]
            demo_labels = [group for group in demo_groups if len(analysis_df[analysis_df[demo_col] == group]) > 0]
            
            if len(demo_data) > 0:
                fig, ax = plt.subplots(figsize=(12, 8))
                bp = ax.boxplot(demo_data, labels=demo_labels, patch_artist=True)
                # Color the boxes
                for patch in bp['boxes']:
                    patch.set_facecolor('lightblue')
                    patch.set_alpha(0.7)
                ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5, alpha=0.5)
                ax.set_xlabel('Demographic/Group', fontsize=12)
                ax.set_ylabel('Lift (%)', fontsize=12)
                ax.set_title('Lift Distribution by Demographic/Group', fontsize=14, fontweight='bold')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                plt.savefig(self.output_dir / 'lift_boxplot_by_demographic.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  ✓ Saved: lift_boxplot_by_demographic.png")
        
        # Additional: Heatmap of lift by month and group
        print("Creating heatmap: Lift by month and group...")
        if group_col:
            heatmap_data = analysis_df.pivot_table(
                index='survey_month',
                columns=group_col,
                values='LIFT_PERCENTAGE',
                aggfunc='mean'
            )
            
            if not heatmap_data.empty and len(heatmap_data.columns) > 0:
                # Limit to top 15 groups for readability
                if len(heatmap_data.columns) > 15:
                    top_groups = analysis_df.groupby(group_col)['LIFT_PERCENTAGE'].mean().nlargest(15).index
                    heatmap_data = heatmap_data[top_groups]
                
                fig, ax = plt.subplots(figsize=(max(10, len(heatmap_data.columns) * 0.8), 
                                                   max(6, len(heatmap_data) * 0.5)))
                sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn', center=0, 
                           ax=ax, cbar_kws={'label': 'Lift (%)'}, linewidths=0.5)
                ax.set_title('Lift Heatmap: Month × Group', fontsize=14, fontweight='bold')
                ax.set_xlabel('Group', fontsize=12)
                ax.set_ylabel('Survey Month', fontsize=12)
                plt.tight_layout()
                plt.savefig(self.output_dir / 'lift_heatmap_month_group.png', dpi=300, bbox_inches='tight')
                plt.close()
                print("  ✓ Saved: lift_heatmap_month_group.png")
        
        print()
    
    def generate_summary_report(self, lift_by_month_group: pd.DataFrame = None,
                                top_bottom: Dict = None,
                                unstable: pd.DataFrame = None) -> str:
        """Task 7: Generate comprehensive summary report to kantar_analysis_summary.txt."""
        print("=" * 80)
        print("TASK 7: GENERATING SUMMARY REPORT")
        print("=" * 80)
        print()
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("KANTAR BRAND LIFT ANALYSIS SUMMARY REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        # Data Summary
        if self.merged_data is not None:
            df = self.merged_data
            report_lines.append("DATA SUMMARY")
            report_lines.append("-" * 80)
            report_lines.append(f"Total Observations: {len(df):,}")
            report_lines.append(f"Unique Survey Months: {df['survey_month'].nunique() if 'survey_month' in df.columns else 'N/A'}")
            if 'survey_month' in df.columns and df['survey_month'].notna().any():
                report_lines.append(f"Date Range: {df['survey_month'].min()} to {df['survey_month'].max()}")
            report_lines.append("")
        
        # Key Trends
        report_lines.append("KEY TRENDS")
        report_lines.append("-" * 80)
        if lift_by_month_group is not None and len(lift_by_month_group) > 0:
            report_lines.append("Average Lift by Month and Group:")
            report_lines.append("")
            # Group by month to show trends
            monthly_summary = lift_by_month_group.groupby('survey_month')['avg_lift'].agg(['mean', 'count']).reset_index()
            for _, row in monthly_summary.iterrows():
                report_lines.append(f"  {row['survey_month']}: Average Lift = {row['mean']:.2f}% (n={row['count']} groups)")
            report_lines.append("")
            report_lines.append("Top 10 Month-Group Combinations by Lift:")
            for i, (_, row) in enumerate(lift_by_month_group.head(10).iterrows(), 1):
                report_lines.append(f"  {i}. {row['survey_month']} - {row['GROUP_NAME']}: {row['avg_lift']:.2f}% (n={row['count']})")
            report_lines.append("")
        
        # Top and Bottom Filters
        if top_bottom is not None:
            report_lines.append("TOP PERFORMING FILTERS")
            report_lines.append("-" * 80)
            if 'top_5' in top_bottom:
                for i, (_, row) in enumerate(top_bottom['top_5'].iterrows(), 1):
                    report_lines.append(f"  {i}. {row['FILTER_NAME']}: {row['avg_lift']:.2f}% (std={row['std_lift']:.2f}, n={row['count']})")
            report_lines.append("")
            
            report_lines.append("BOTTOM PERFORMING FILTERS")
            report_lines.append("-" * 80)
            if 'bottom_5' in top_bottom:
                for i, (_, row) in enumerate(top_bottom['bottom_5'].iterrows(), 1):
                    report_lines.append(f"  {i}. {row['FILTER_NAME']}: {row['avg_lift']:.2f}% (std={row['std_lift']:.2f}, n={row['count']})")
            report_lines.append("")
        
        # Stable vs Unstable Patterns
        report_lines.append("STABLE VS UNSTABLE PATTERNS")
        report_lines.append("-" * 80)
        if unstable is not None and len(unstable) > 0:
            report_lines.append(f"Unstable Filters Identified: {len(unstable)}")
            report_lines.append("Most Unstable Filters (high standard deviation):")
            for i, (_, row) in enumerate(unstable.head(5).iterrows(), 1):
                report_lines.append(f"  {i}. {row['FILTER_NAME']}: CV={row['cv']:.2f}, Range={row['range']:.2f}%, Avg={row['avg_lift']:.2f}%")
            report_lines.append("")
            report_lines.append("Note: Unstable patterns may indicate:")
            report_lines.append("  - High variability in lift across time or segments")
            report_lines.append("  - Need for more data points to establish reliable patterns")
            report_lines.append("  - Potential measurement issues or small sample sizes")
        else:
            report_lines.append("No highly unstable patterns identified.")
        report_lines.append("")
        
        # Notable Anomalies
        report_lines.append("NOTABLE ANOMALIES")
        report_lines.append("-" * 80)
        if self.merged_data is not None:
            df = self.merged_data
            if 'LIFT_PERCENTAGE' in df.columns:
                valid_lift = df['LIFT_PERCENTAGE'].dropna()
                if len(valid_lift) > 0:
                    high_lift = df[df['LIFT_PERCENTAGE'] > valid_lift.quantile(0.95)]
                    low_lift = df[df['LIFT_PERCENTAGE'] < valid_lift.quantile(0.05)]
                    report_lines.append(f"Extreme High Lift (>95th percentile): {len(high_lift)} observations")
                    report_lines.append(f"Extreme Low Lift (<5th percentile): {len(low_lift)} observations")
                    if len(high_lift) > 0:
                        report_lines.append(f"  Max lift: {valid_lift.max():.2f}%")
                    if len(low_lift) > 0:
                        report_lines.append(f"  Min lift: {valid_lift.min():.2f}%")
        report_lines.append("")
        
        # Narrative Summary
        report_lines.append("NARRATIVE SUMMARY")
        report_lines.append("-" * 80)
        if lift_by_month_group is not None and len(lift_by_month_group) > 0:
            overall_avg = lift_by_month_group['avg_lift'].mean()
            report_lines.append(f"Overall average lift across all month-group combinations: {overall_avg:.2f}%")
            report_lines.append("")
            if top_bottom is not None and 'top_5' in top_bottom:
                top_avg = top_bottom['top_5']['avg_lift'].mean()
                report_lines.append(f"Top performing filters show an average lift of {top_avg:.2f}%, indicating strong")
                report_lines.append("brand impact in these segments.")
        report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)
        
        report_text = "\n".join(report_lines)
        
        # Save report
        report_file = self.output_dir / "kantar_analysis_summary.txt"
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        print(f"✓ Report saved: {report_file.name}")
        print()
        print(report_text)
        
        return report_text


def main():
    """Main execution function."""
    print("=" * 80)
    print("🟣 KANTAR BRAND LIFT ANALYSIS PIPELINE (DOORDASH)")
    print("=" * 80)
    print()
    
    analyzer = ComprehensiveBLSAnalyzer()
    
    # Task 1: Load all data
    analyzer.load_all_data()
    
    # Task 2 & 3: Merge and extract survey_month
    analyzer.merge_data()
    
    # Task 5: Perform analysis
    lift_by_month_group = analyzer.analyze_lift_by_month_and_group()
    top_bottom = analyzer.identify_top_bottom_filters()
    unstable = analyzer.identify_unstable_patterns()
    
    # Task 5d & 6: Create visualizations
    analyzer.create_visualizations()
    
    # Task 7: Generate summary report
    analyzer.generate_summary_report(
        lift_by_month_group=lift_by_month_group,
        top_bottom=top_bottom,
        unstable=unstable
    )
    
    print("=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nAll outputs saved to: {analyzer.output_dir}")
    print("\nGenerated files:")
    print("  - merged_kantar_data.csv")
    print("  - lift_by_month_and_group.csv")
    print("  - top_5_filters.csv")
    print("  - bottom_5_filters.csv")
    print("  - unstable_patterns.csv")
    print("  - lift_over_time_by_channel.png")
    print("  - lift_boxplot_by_demographic.png")
    print("  - lift_heatmap_month_group.png")
    print("  - kantar_analysis_summary.txt")


if __name__ == "__main__":
    main()
