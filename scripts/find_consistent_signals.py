"""
Find Consistent Signals Across Filters and Brand Metrics
=======================================================

This script identifies brand metrics that show consistent performance
across different filters (channels, demographics, time periods, etc.).
"""

import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from analyze import KantarBLSAnalyzer

def main():
    """Find and report consistent signals across filters."""
    
    print("=" * 80)
    print("FINDING CONSISTENT SIGNALS ACROSS FILTERS AND BRAND METRICS")
    print("=" * 80)
    print()
    
    # Initialize analyzer
    analyzer = KantarBLSAnalyzer()
    
    # Try to load saved merged data first (faster)
    merged_file = analyzer.data_dir / "bls_metrics_merged.csv"
    if merged_file.exists():
        print("Loading saved merged data...")
        analyzer.load_merged_data()
    else:
        print("Loading and merging data...")
        analyzer.load_data(use_snowflake=False)
        analyzer.clean_and_merge(save_merged=True)
    
    print("\n" + "=" * 80)
    print("ANALYZING CONSISTENT SIGNALS")
    print("=" * 80)
    print()
    
    # Find consistent signals
    print("Finding metrics with consistent signal across filters...")
    consistent_signals = analyzer.find_consistent_signals(min_filters=3, min_lift=0.0)
    
    print(f"\nFound {len(consistent_signals)} metrics with consistent signal across filters")
    print()
    
    # Display top consistent signals
    print("TOP 20 MOST CONSISTENT METRICS ACROSS FILTERS:")
    print("-" * 80)
    top_20 = consistent_signals.head(20)
    
    for idx, row in top_20.iterrows():
        print(f"\n{row['METRIC_NAME']}")
        print(f"  Average Lift: {row['AVG_LIFT']:.2f}%")
        print(f"  Consistency Score: {row['CONSISTENCY_SCORE']:.3f}")
        print(f"  Unique Filters: {int(row['UNIQUE_FILTERS'])}")
        print(f"  Total Observations: {int(row['TOTAL_OBSERVATIONS'])}")
        print(f"  Positive Lift Count: {int(row['POSITIVE_LIFT_COUNT'])}")
        print(f"  Coefficient of Variation: {row['CV']:.2f}" if pd.notna(row['CV']) else "  Coefficient of Variation: N/A")
        print(f"  Consistency Level: {row['CONSISTENCY_LEVEL']}")
    
    # Analyze specific metrics across filters
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS: TOP 5 METRICS")
    print("=" * 80)
    print()
    
    top_5_metrics = consistent_signals.head(5)['METRIC_NAME'].tolist()
    
    for metric_name in top_5_metrics:
        print(f"\n{metric_name}:")
        print("-" * 80)
        
        # Get filter-level breakdown
        filter_breakdown = analyzer.analyze_metric_filter_consistency(metric_name=metric_name)
        
        # Show top performing filters
        top_filters = filter_breakdown.nlargest(5, 'LIFT_MEAN')
        print("Top 5 Filters by Lift:")
        for _, row in top_filters.iterrows():
            print(f"  {row.get('FILTER_NAME', 'N/A')[:50]}: "
                  f"Lift: {row['LIFT_MEAN']:.2f}%, "
                  f"Channel: {row.get('CHANNEL', 'N/A')}, "
                  f"Observations: {int(row['OBSERVATIONS'])}")
    
    # Save results
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Save consistent signals
    output_file = output_dir / "consistent_signals_across_filters.csv"
    consistent_signals.to_csv(output_file, index=False)
    print(f"\n✓ Saved consistent signals to: {output_file}")
    
    # Save detailed breakdown for top metrics
    if len(top_5_metrics) > 0:
        detailed_breakdown = analyzer.analyze_metric_filter_consistency(metric_name=top_5_metrics[0])
        for metric in top_5_metrics[1:]:
            breakdown = analyzer.analyze_metric_filter_consistency(metric_name=metric)
            detailed_breakdown = pd.concat([detailed_breakdown, breakdown], ignore_index=True)
        
        output_file = output_dir / "metric_filter_consistency_breakdown.csv"
        detailed_breakdown.to_csv(output_file, index=False)
        print(f"✓ Saved detailed breakdown to: {output_file}")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    
    print(f"Total metrics analyzed: {len(consistent_signals)}")
    print(f"Metrics with high consistency: {len(consistent_signals[consistent_signals['CONSISTENCY_LEVEL'] == 'High'])}")
    print(f"Metrics with medium consistency: {len(consistent_signals[consistent_signals['CONSISTENCY_LEVEL'] == 'Medium'])}")
    print(f"Metrics with low consistency: {len(consistent_signals[consistent_signals['CONSISTENCY_LEVEL'] == 'Low'])}")
    print()
    
    print(f"Average lift across consistent signals: {consistent_signals['AVG_LIFT'].mean():.2f}%")
    print(f"Average number of filters per metric: {consistent_signals['UNIQUE_FILTERS'].mean():.1f}")
    print(f"Average consistency score: {consistent_signals['CONSISTENCY_SCORE'].mean():.3f}")
    print()
    
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()

