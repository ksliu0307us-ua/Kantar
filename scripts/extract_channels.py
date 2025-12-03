"""
Extract Media Channels from Kantar BLS Data
============================================

This script analyzes the data to extract all unique media channels
used in DoorDash brand marketing campaigns.
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from analyze import KantarBLSAnalyzer

def extract_channels():
    """Extract and analyze media channels from the data."""
    
    print("=" * 80)
    print("MEDIA CHANNEL EXTRACTION - DoorDash Brand Marketing")
    print("=" * 80)
    print()
    
    # Initialize analyzer
    analyzer = KantarBLSAnalyzer()
    
    # Load data
    print("Loading data...")
    analyzer.load_data(use_snowflake=False)
    
    # Clean and merge
    print("Processing data...")
    analyzer.clean_and_merge()
    
    df = analyzer.merged_data
    
    print("\n" + "=" * 80)
    print("MEDIA CHANNELS IDENTIFIED")
    print("=" * 80)
    print()
    
    # Extract channels from GROUP_NAME
    if 'GROUP_NAME' in df.columns:
        print("CHANNELS BY GROUP_NAME:")
        print("-" * 80)
        group_channels = df['GROUP_NAME'].value_counts()
        for group, count in group_channels.items():
            print(f"  {group}: {count:,} observations")
        print()
    
    # Extract channels from FILTER_NAME
    if 'FILTER_NAME' in df.columns:
        print("CHANNELS BY FILTER_NAME (Sample):")
        print("-" * 80)
        filter_channels = df['FILTER_NAME'].value_counts().head(30)
        for filter_name, count in filter_channels.items():
            print(f"  {filter_name}: {count:,} observations")
        print()
    
    # Extract extracted CHANNEL dimension
    if 'CHANNEL' in df.columns:
        print("CHANNELS BY EXTRACTED CHANNEL DIMENSION:")
        print("-" * 80)
        channel_counts = df['CHANNEL'].value_counts()
        for channel, count in channel_counts.items():
            avg_lift = df[df['CHANNEL'] == channel]['LIFT'].mean()
            print(f"  {channel}: {count:,} observations (Avg Lift: {avg_lift:.2f}%)")
        print()
    
    # Extract specific channel mentions from FILTER_NAME
    print("=" * 80)
    print("DETAILED CHANNEL BREAKDOWN")
    print("=" * 80)
    print()
    
    if 'FILTER_NAME' in df.columns:
        # Look for specific channel mentions
        channel_keywords = {
            'TV': [],
            'YouTube': [],
            'Social': [],
            'Facebook': [],
            'Instagram': [],
            'Twitter': [],
            'TikTok': [],
            'Snapchat': [],
            'Digital': [],
            'Programmatic': [],
            'Display': [],
            'OTT': [],
            'Streaming': [],
            'Podcast': [],
            'Audio': [],
            'Radio': [],
            'CTV': [],
            'Connected TV': [],
            'The Trade Desk': [],
            'Realm': [],
            'iHeart': [],
            'Spotify': [],
            'Pandora': [],
            'Amazon': [],
            'Hulu': [],
            'Netflix': [],
            'Roku': [],
        }
        
        filter_names = df['FILTER_NAME'].unique()
        
        for filter_name in filter_names:
            filter_lower = str(filter_name).lower()
            for keyword, matches in channel_keywords.items():
                if keyword.lower() in filter_lower:
                    matches.append(filter_name)
        
        print("CHANNEL-SPECIFIC FILTERS FOUND:")
        print("-" * 80)
        for keyword, matches in channel_keywords.items():
            if matches:
                unique_matches = list(set(matches))
                print(f"\n{keyword.upper()}:")
                for match in unique_matches[:10]:  # Show first 10
                    count = len(df[df['FILTER_NAME'] == match])
                    print(f"  - {match} ({count:,} obs)")
                if len(unique_matches) > 10:
                    print(f"  ... and {len(unique_matches) - 10} more")
        print()
    
    # Create summary report
    print("=" * 80)
    print("CHANNEL SUMMARY")
    print("=" * 80)
    print()
    
    if 'CHANNEL' in df.columns:
        summary = df.groupby('CHANNEL').agg({
            'LIFT': ['mean', 'count'],
            'FILTER_ID': 'nunique'
        }).round(2)
        summary.columns = ['Avg_Lift_%', 'Total_Observations', 'Unique_Filters']
        summary = summary.sort_values('Total_Observations', ascending=False)
        
        print(summary.to_string())
        print()
    
    # Export to CSV
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    if 'CHANNEL' in df.columns:
        channel_summary = df.groupby('CHANNEL').agg({
            'LIFT': ['mean', 'std', 'count'],
            'FILTER_ID': 'nunique',
            'METRIC_NAME': 'nunique'
        }).round(2)
        channel_summary.columns = ['Avg_Lift_%', 'Std_Lift', 'Total_Observations', 'Unique_Filters', 'Unique_Metrics']
        channel_summary = channel_summary.sort_values('Total_Observations', ascending=False)
        
        output_file = output_dir / "media_channels_summary.csv"
        channel_summary.to_csv(output_file)
        print(f"✓ Channel summary exported to: {output_file}")
        print()
    
    # Detailed filter breakdown
    if 'FILTER_NAME' in df.columns and 'GROUP_NAME' in df.columns:
        filter_breakdown = df.groupby(['GROUP_NAME', 'FILTER_NAME']).agg({
            'LIFT': ['mean', 'count'],
            'FILTER_ID': 'first'
        }).round(2)
        filter_breakdown.columns = ['Avg_Lift_%', 'Observations', 'Filter_ID']
        filter_breakdown = filter_breakdown.sort_values('Observations', ascending=False)
        
        output_file = output_dir / "media_channels_detailed.csv"
        filter_breakdown.to_csv(output_file)
        print(f"✓ Detailed channel breakdown exported to: {output_file}")
        print()
    
    print("=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    extract_channels()

