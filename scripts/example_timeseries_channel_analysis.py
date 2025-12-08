"""
Example: Time Series and Channel Analysis
==========================================

This script demonstrates how to use the new time series and channel analysis
methods based on the Kantar API structure:
- Time information from filters call with "timestamp" as GROUP_NAME
- Channel information from filters call with "XM" prefix/folder
- Multiple filter ID aggregation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analyze import KantarBLSAnalyzer

def main():
    print("=" * 80)
    print("KANTAR BLS - TIME SERIES & CHANNEL ANALYSIS")
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
    
    print("\n" + "=" * 80)
    print("1. TIME SERIES ANALYSIS")
    print("=" * 80)
    print()
    
    # Time series analysis - all metrics over time
    print("Analyzing time trends for all metrics...")
    time_series = analyzer.analyze_time_series()
    print(f"Found {len(time_series)} time period / metric combinations")
    print("\nSample time series data:")
    print(time_series.head(10))
    print()
    
    # Time series for specific metric
    print("\nAnalyzing time trends for 'DashPass' metrics...")
    dashpass_ts = analyzer.analyze_time_series(metric_name="DashPass")
    print(f"Found {len(dashpass_ts)} time period / metric combinations")
    print("\nSample DashPass time series:")
    print(dashpass_ts.head(10))
    print()
    
    # Time series for specific channel
    if 'CHANNEL' in analyzer.merged_data.columns:
        print("\nAnalyzing time trends for Social channel...")
        social_ts = analyzer.analyze_time_series(channel="Social")
        print(f"Found {len(social_ts)} time period / metric combinations")
        print("\nSample Social channel time series:")
        print(social_ts.head(10))
        print()
    
    print("\n" + "=" * 80)
    print("2. CHANNEL ANALYSIS")
    print("=" * 80)
    print()
    
    # Channel analysis - all metrics
    print("Analyzing performance by channel...")
    channel_analysis = analyzer.analyze_by_channel()
    print(f"Found {len(channel_analysis)} channel / metric combinations")
    print("\nSample channel analysis:")
    print(channel_analysis.head(10))
    print()
    
    # Channel analysis for specific metric
    print("\nAnalyzing channel performance for 'Brand Affinity'...")
    affinity_channels = analyzer.analyze_by_channel(metric_name="Affinity")
    print(f"Found {len(affinity_channels)} channel / metric combinations")
    print("\nBrand Affinity by channel:")
    print(affinity_channels)
    print()
    
    # Channel analysis for specific time period
    if 'TIME_PERIOD' in analyzer.merged_data.columns:
        print("\nAnalyzing channel performance for specific time period...")
        # Get first available time period as example
        time_periods = analyzer.merged_data['TIME_PERIOD'].dropna().unique()
        if len(time_periods) > 0 and time_periods[0] != 'Unknown':
            example_period = time_periods[0]
            print(f"Analyzing channels for: {example_period}")
            period_channels = analyzer.analyze_by_channel(time_period=example_period)
            print(f"Found {len(period_channels)} channel / metric combinations")
            print("\nChannel performance for this period:")
            print(period_channels.head(10))
            print()
    
    print("\n" + "=" * 80)
    print("3. MULTIPLE FILTER ID AGGREGATION")
    print("=" * 80)
    print()
    
    # Example: Aggregate multiple filter IDs
    # This simulates combining "last 7 days" + "last 3 months" filters
    print("Example: Aggregating multiple filter IDs...")
    
    # Get some example filter IDs (first 5 unique filters)
    unique_filters = analyzer.merged_data['FILTER_ID'].unique()[:5]
    print(f"Using filter IDs: {unique_filters.tolist()}")
    
    try:
        aggregated = analyzer.aggregate_filter_ids(
            filter_ids=unique_filters.tolist(),
            method='weighted_mean'
        )
        print(f"\nAggregated results across {len(unique_filters)} filters:")
        print(aggregated.head(10))
        print()
        
        # Aggregate for specific metric
        print("\nAggregating for 'DashPass Worth' metric...")
        dashpass_agg = analyzer.aggregate_filter_ids(
            filter_ids=unique_filters.tolist(),
            metric_name="DashPass Worth",
            method='weighted_mean'
        )
        print("Aggregated DashPass Worth results:")
        print(dashpass_agg)
        print()
    except Exception as e:
        print(f"Note: Could not aggregate filter IDs - {str(e)}")
        print("This is expected if the filter IDs don't have sufficient data.")
        print()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("Key Takeaways:")
    print("- Time series analysis shows trends over time")
    print("- Channel analysis shows performance by media channel")
    print("- Multiple filter IDs can be aggregated for combined analysis")
    print("- All methods support filtering by metric, channel, or time period")
    print()

if __name__ == "__main__":
    main()

