"""
Complete Analysis Pipeline for New Kantar BLS Data Format

This script performs a full analysis from scratch using the new timestamp-aggregated
data format from Martech team (kantar_bls_sample_data.csv).

Data Format:
- LIMITING_FILTER contains timestamp info: "Timestamp: 3/1/25-3/31/25"
- EXPOSED_FILTER/WEIGHT_SET contains channel info: "XM: 2. Social", "XM: 3. TV", etc.
- METRIC contains the brand metric name
- LIFT, DELTA, CONTROL_, EXPOSED_ contain the lift calculations
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re
from datetime import datetime
from typing import Optional, Dict, List

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

class NewDataAnalyzer:
    """Complete analyzer for new Kantar BLS data format."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize analyzer with data directory."""
        if data_dir is None:
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
        
        print(f"Loading data from {filepath.name}...")
        self.data = pd.read_csv(filepath, low_memory=False)
        print(f"  Loaded {len(self.data):,} rows")
        print(f"  Columns: {list(self.data.columns)}")
        return self.data
    
    def extract_timestamp(self, limiting_filter: str) -> Optional[str]:
        """Extract timestamp from LIMITING_FILTER column."""
        if pd.isna(limiting_filter):
            return None
        
        limiting_filter = str(limiting_filter).strip()
        pattern = r'Timestamp:\s*(\d{1,2})/(\d{1,2})/(\d{2,4})'
        match = re.search(pattern, limiting_filter, re.IGNORECASE)
        
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            year_str = match.group(3)
            
            if len(year_str) == 2:
                year = 2000 + int(year_str)
            else:
                year = int(year_str)
            
            try:
                date = datetime(year, month, 1)
                return date.strftime("%Y-%m-%d")
            except ValueError:
                return None
        
        return None
    
    def extract_channel(self, exposed_filter: str, weight_set: str = None) -> str:
        """Extract channel from EXPOSED_FILTER or WEIGHT_SET column."""
        # Priority 1: Try WEIGHT_SET first
        if weight_set and pd.notna(weight_set):
            text = str(weight_set)
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
        
        # Priority 2: Try EXPOSED_FILTER
        text = str(exposed_filter) if pd.notna(exposed_filter) else ""
        patterns = [
            r'XM:\s*\d+\.\s*(\w+)',
            r'XM:\s*(\w+)',
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
        
        # Check for combo filters
        if "combo" in text.lower() or "through" in text.lower():
            if "0. ANY" in text.upper():
                return "Any"
            elif "4. Digital" in text:
                return "Digital"
        
        return "Other"
    
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
        print(f"    Channels: {sorted(df['CHANNEL'].unique())}")
        
        self.processed_data = df
        return df
    
    def analyze_trends(self, group_by: List[str] = None) -> pd.DataFrame:
        """Analyze trends by specified dimensions."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call process_data() first.")
        
        if group_by is None:
            group_by = ['CHANNEL', 'METRIC_CLEAN']
        
        print(f"\nAnalyzing trends grouped by: {group_by}...")
        df = self.processed_data.copy()
        
        # Aggregate
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
        
        trends = df.groupby(group_by).agg(agg_dict).reset_index()
        
        # Flatten column names
        trends.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                         for col in trends.columns.values]
        
        print(f"  Generated {len(trends):,} trend combinations")
        return trends
    
    def find_consistent_signals(self, min_observations: int = 3) -> pd.DataFrame:
        """Find metrics with consistent signals across filters/channels."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call process_data() first.")
        
        print(f"\nFinding consistent signals (min_observations={min_observations})...")
        df = self.processed_data.copy()
        
        # Group by metric and channel to get lift per metric-channel combination
        metric_channel_lift = df.groupby(['METRIC_CLEAN', 'CHANNEL']).agg({
            'LIFT': ['mean', 'std', 'count'],
            'EXPOSED_N': 'sum',
            'CONTROL_N': 'sum',
        }).reset_index()
        
        metric_channel_lift.columns = [
            'METRIC_CLEAN', 'CHANNEL', 'LIFT_mean', 'LIFT_std', 'LIFT_count',
            'EXPOSED_N_sum', 'CONTROL_N_sum'
        ]
        
        # Calculate consistency metrics per brand metric
        metric_consistency = metric_channel_lift.groupby('METRIC_CLEAN').agg({
            'LIFT_mean': ['mean', 'std', 'count', lambda x: (x > 0).sum()],
            'LIFT_std': 'mean',
            'CHANNEL': 'nunique'
        }).reset_index()
        
        metric_consistency.columns = [
            'METRIC_CLEAN', 'AVG_LIFT', 'STD_LIFT', 'TOTAL_OBSERVATIONS',
            'POSITIVE_LIFT_COUNT', 'AVG_STD', 'UNIQUE_CHANNELS'
        ]
        
        # Calculate consistency score
        metric_consistency['CV'] = metric_consistency['STD_LIFT'] / metric_consistency['AVG_LIFT'].abs().replace(0, np.nan)
        metric_consistency['CONSISTENCY_SCORE'] = (
            (metric_consistency['UNIQUE_CHANNELS'] / metric_consistency['UNIQUE_CHANNELS'].max()) * 0.4 +
            (1 / (1 + metric_consistency['CV'].fillna(999))) * 0.4 +
            (metric_consistency['POSITIVE_LIFT_COUNT'] / metric_consistency['TOTAL_OBSERVATIONS']) * 0.2
        )
        
        # Filter by minimum observations
        consistent_signals = metric_consistency[
            metric_consistency['TOTAL_OBSERVATIONS'] >= min_observations
        ].copy()
        
        # Classify consistency
        consistent_signals['CONSISTENCY_LEVEL'] = pd.cut(
            consistent_signals['CONSISTENCY_SCORE'],
            bins=[0, 0.4, 0.7, 1.0],
            labels=['Low', 'Medium', 'High']
        )
        
        # Sort by consistency score
        consistent_signals = consistent_signals.sort_values('CONSISTENCY_SCORE', ascending=False)
        
        print(f"  Found {len(consistent_signals):,} metrics with consistent signals")
        return consistent_signals
    
    def detect_significance(self, alpha: float = 0.05) -> pd.DataFrame:
        """Identify statistically significant lift results."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call process_data() first.")
        
        print(f"\nDetecting significant results (alpha={alpha})...")
        df = self.processed_data.copy()
        
        # Add significance flag
        if 'STATISTICAL_SIGNIFICANCE' in df.columns:
            df['IS_SIGNIFICANT'] = df['STATISTICAL_SIGNIFICANCE'] <= alpha
        else:
            # Heuristic based on sample size and lift
            df['IS_SIGNIFICANT'] = (
                (df['EXPOSED_N'] >= 100) &
                (df['CONTROL_N'] >= 100) &
                (df['LIFT'].abs() > 5)
            )
        
        sig_count = df['IS_SIGNIFICANT'].sum()
        print(f"  Found {sig_count:,} significant results ({sig_count/len(df)*100:.1f}%)")
        
        return df
    
    def generate_visualizations(self):
        """Generate all visualizations."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call process_data() first.")
        
        print("\nGenerating visualizations...")
        df = self.processed_data.copy()
        
        # 1. Lift by Channel (bar chart)
        print("  1. Lift by Channel...")
        channel_avg = df.groupby('CHANNEL')['LIFT'].mean().sort_values(ascending=True)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(channel_avg.index, channel_avg.values)
        colors = ['green' if x > 0 else 'red' for x in channel_avg.values]
        for bar, color in zip(bars, colors):
            bar.set_color(color)
            bar.set_alpha(0.7)
        
        ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Average Lift (%)', fontsize=12)
        ax.set_ylabel('Channel', fontsize=12)
        ax.set_title('Average Brand Lift by Channel', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'lift_by_channel.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"     Saved: lift_by_channel.png")
        
        # 2. Heatmap: Metrics by Channel
        print("  2. Heatmap: Metrics by Channel...")
        channel_metric = df.groupby(['CHANNEL', 'METRIC_CLEAN']).agg({
            'LIFT': 'mean'
        }).reset_index()
        
        pivot = channel_metric.pivot_table(
            index='METRIC_CLEAN',
            columns='CHANNEL',
            values='LIFT',
            aggfunc='mean'
        )
        
        # Sort channels (put TV first if it exists)
        if 'TV' in pivot.columns:
            channel_order = ['TV'] + [c for c in pivot.columns if c != 'TV']
            pivot = pivot[channel_order]
        
        # Sort metrics by average lift
        pivot['avg_lift'] = pivot.mean(axis=1)
        pivot = pivot.sort_values('avg_lift', ascending=False)
        pivot = pivot.drop('avg_lift', axis=1)
        
        fig, ax = plt.subplots(figsize=(max(8, len(pivot.columns) * 1.5), max(10, len(pivot) * 0.3)))
        sns.heatmap(
            pivot,
            annot=True,
            fmt='.2f',
            cmap='RdYlGn',
            center=0,
            ax=ax,
            cbar_kws={'label': 'Lift (%)'},
            linewidths=0.5,
            linecolor='gray'
        )
        ax.set_title('Lift Heatmap: Metrics by Channel', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Channel', fontsize=12)
        ax.set_ylabel('Metric', fontsize=12)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'lift_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"     Saved: lift_heatmap.png")
        
        # 3. Top Metrics (bar chart)
        print("  3. Top Metrics...")
        metric_avg = df.groupby('METRIC_CLEAN')['LIFT'].mean().sort_values(ascending=False).head(20)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        bars = ax.barh(range(len(metric_avg)), metric_avg.values)
        colors = ['green' if x > 0 else 'red' for x in metric_avg.values]
        for bar, color in zip(bars, colors):
            bar.set_color(color)
            bar.set_alpha(0.7)
        
        ax.set_yticks(range(len(metric_avg)))
        ax.set_yticklabels(metric_avg.index, fontsize=9)
        ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Average Lift (%)', fontsize=12)
        ax.set_title('Top 20 Metrics by Average Lift', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'top_metrics.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"     Saved: top_metrics.png")
        
        # 4. Consistent Signals (if available)
        print("  4. Consistent Signals...")
        try:
            consistent = self.find_consistent_signals(min_observations=1)
            if len(consistent) > 0:
                top_consistent = consistent.head(20)
                
                fig, ax = plt.subplots(figsize=(12, 8))
                bars = ax.barh(range(len(top_consistent)), top_consistent['CONSISTENCY_SCORE'].values)
                ax.set_yticks(range(len(top_consistent)))
                ax.set_yticklabels(top_consistent['METRIC_CLEAN'].values, fontsize=9)
                ax.set_xlabel('Consistency Score', fontsize=12)
                ax.set_title('Top 20 Metrics by Consistency Score', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3, axis='x')
                plt.tight_layout()
                plt.savefig(self.output_dir / 'top_consistent_metrics.png', dpi=300, bbox_inches='tight')
                plt.close()
                print(f"     Saved: top_consistent_metrics.png")
        except Exception as e:
            print(f"     Skipped: {str(e)}")
    
    def generate_report(self) -> str:
        """Generate text report."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call process_data() first.")
        
        print("\nGenerating report...")
        df = self.processed_data.copy()
        report = []
        
        report.append("=" * 80)
        report.append("KANTAR BLS ANALYSIS REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        report.append("")
        
        # Data Summary
        report.append("DATA SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Observations: {len(df):,}")
        report.append(f"Unique Metrics: {df['METRIC_CLEAN'].nunique()}")
        report.append(f"Unique Channels: {df['CHANNEL'].nunique()}")
        report.append(f"Unique Time Periods: {df['TIMESTAMP'].nunique()}")
        report.append(f"Date Range: {df['TIMESTAMP_DATE'].min()} to {df['TIMESTAMP_DATE'].max()}")
        report.append("")
        
        # Channel Performance
        report.append("CHANNEL PERFORMANCE")
        report.append("-" * 80)
        channel_stats = df.groupby('CHANNEL').agg({
            'LIFT': ['mean', 'std', 'count'],
            'EXPOSED_N': 'sum',
            'CONTROL_N': 'sum'
        })
        for channel in channel_stats.index:
            avg_lift = channel_stats.loc[channel, ('LIFT', 'mean')]
            count = channel_stats.loc[channel, ('LIFT', 'count')]
            report.append(f"  {channel}: {avg_lift:.2f}% avg lift ({count:,} observations)")
        report.append("")
        
        # Top Metrics
        report.append("TOP 10 METRICS BY AVERAGE LIFT")
        report.append("-" * 80)
        top_metrics = df.groupby('METRIC_CLEAN')['LIFT'].mean().sort_values(ascending=False).head(10)
        for i, (metric, lift) in enumerate(top_metrics.items(), 1):
            report.append(f"  {i}. {metric}: {lift:.2f}%")
        report.append("")
        
        # Consistent Signals
        try:
            consistent = self.find_consistent_signals(min_observations=3)
            if len(consistent) > 0:
                report.append("TOP 10 CONSISTENT SIGNALS")
                report.append("-" * 80)
                top_consistent = consistent.head(10)
                for i, (_, row) in enumerate(top_consistent.iterrows(), 1):
                    report.append(f"  {i}. {row['METRIC_CLEAN']}: "
                                f"{row['AVG_LIFT']:.2f}% lift, "
                                f"consistency={row['CONSISTENCY_SCORE']:.2f}")
                report.append("")
        except Exception as e:
            report.append(f"Note: Could not calculate consistent signals: {str(e)}")
            report.append("")
        
        # Significant Results
        try:
            significant = self.detect_significance()
            sig_count = significant['IS_SIGNIFICANT'].sum()
            report.append("STATISTICAL SIGNIFICANCE")
            report.append("-" * 80)
            report.append(f"Significant Results: {sig_count:,} ({sig_count/len(significant)*100:.1f}%)")
            report.append("")
        except Exception as e:
            report.append(f"Note: Could not calculate significance: {str(e)}")
            report.append("")
        
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"kantar_bls_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        print(f"  Report saved to: {report_file}")
        return report_text
    
    def save_results(self):
        """Save all analysis results to CSV files."""
        if self.processed_data is None:
            raise ValueError("Data not processed. Call process_data() first.")
        
        print("\nSaving results...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save processed data
        processed_file = self.output_dir / f"processed_data_{timestamp}.csv"
        self.processed_data.to_csv(processed_file, index=False)
        print(f"  Saved processed data: {processed_file.name}")
        
        # Save trends
        try:
            trends = self.analyze_trends(group_by=['CHANNEL', 'METRIC_CLEAN'])
            trends_file = self.output_dir / f"trends_by_channel_metric_{timestamp}.csv"
            trends.to_csv(trends_file, index=False)
            print(f"  Saved trends: {trends_file.name}")
        except Exception as e:
            print(f"  Could not save trends: {str(e)}")
        
        # Save consistent signals
        try:
            consistent = self.find_consistent_signals()
            consistent_file = self.output_dir / f"consistent_signals_{timestamp}.csv"
            consistent.to_csv(consistent_file, index=False)
            print(f"  Saved consistent signals: {consistent_file.name}")
        except Exception as e:
            print(f"  Could not save consistent signals: {str(e)}")
        
        # Save significant results
        try:
            significant = self.detect_significance()
            sig_file = self.output_dir / f"significant_results_{timestamp}.csv"
            significant.to_csv(sig_file, index=False)
            print(f"  Saved significant results: {sig_file.name}")
        except Exception as e:
            print(f"  Could not save significant results: {str(e)}")


def main():
    """Main execution function."""
    print("=" * 80)
    print("KANTAR BLS ANALYSIS - NEW DATA FORMAT")
    print("Starting from scratch with new sample data")
    print("=" * 80)
    print()
    
    # Initialize analyzer
    analyzer = NewDataAnalyzer()
    
    # Load data
    analyzer.load_data()
    
    # Process data
    analyzer.process_data()
    
    # Generate visualizations
    analyzer.generate_visualizations()
    
    # Generate report
    report = analyzer.generate_report()
    print("\n" + report)
    
    # Save results
    analyzer.save_results()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nAll outputs saved to: {analyzer.output_dir}")


if __name__ == "__main__":
    main()

