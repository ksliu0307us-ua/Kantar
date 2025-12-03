"""
Example usage of the Kantar BLS Analyzer

This script demonstrates how to use the analyzer for different analysis scenarios.
"""

from analyze import KantarBLSAnalyzer
import pandas as pd
from pathlib import Path

def example_basic_analysis():
    """Run a basic end-to-end analysis."""
    print("=" * 80)
    print("Example 1: Basic End-to-End Analysis")
    print("=" * 80)
    
    # Use default data_dir (../data relative to script)
    analyzer = KantarBLSAnalyzer()
    analyzer.load_data(use_snowflake=False)
    analyzer.clean_and_merge()
    
    # Generate full report in output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "output"
    report_path = analyzer.generate_report(output_dir=str(output_dir))
    print(f"\nReport generated: {report_path}\n")


def example_specific_metric():
    """Analyze a specific metric across channels."""
    print("=" * 80)
    print("Example 2: Analyze Specific Metric")
    print("=" * 80)
    
    # Use default data_dir (../data relative to script)
    analyzer = KantarBLSAnalyzer()
    analyzer.load_data(use_snowflake=False)
    analyzer.clean_and_merge()
    
    # Analyze "Unaided Brand Awareness" across channels
    trends = analyzer.analyze_trends(
        metric_name="Unaided Brand Awareness",
        group_by=['CHANNEL']
    )
    
    print("\nUnaided Brand Awareness by Channel:")
    print(trends[['CHANNEL', 'LIFT_mean', 'LIFT_count']].to_string())
    print()


def example_channel_comparison():
    """Compare lift across different channels."""
    print("=" * 80)
    print("Example 3: Channel Comparison")
    print("=" * 80)
    
    # Use default data_dir (../data relative to script)
    analyzer = KantarBLSAnalyzer()
    analyzer.load_data(use_snowflake=False)
    analyzer.clean_and_merge()
    
    # Get patterns
    patterns = analyzer.identify_patterns()
    
    if 'channel_consistency' in patterns:
        channel_summary = patterns['channel_consistency'].groupby('CHANNEL').agg({
            'MEAN_LIFT': 'mean',
            'COUNT': 'sum',
            'IS_CONSISTENT': lambda x: (x.sum() / len(x)) * 100
        }).sort_values('MEAN_LIFT', ascending=False)
        
        print("\nChannel Performance Summary:")
        print(channel_summary.to_string())
        print()


def example_significant_results():
    """Find statistically significant lift results."""
    print("=" * 80)
    print("Example 4: Significant Results Only")
    print("=" * 80)
    
    # Use default data_dir (../data relative to script)
    analyzer = KantarBLSAnalyzer()
    analyzer.load_data(use_snowflake=False)
    analyzer.clean_and_merge()
    
    # Detect significance
    significant = analyzer.detect_significance(alpha=0.05)
    sig_results = significant[significant.get('IS_SIGNIFICANT', pd.Series([False] * len(significant)))]
    
    print(f"\nFound {len(sig_results):,} significant results (out of {len(significant):,} total)")
    
    if len(sig_results) > 0:
        # Top significant results
        top_sig = sig_results.nlargest(10, 'LIFT')[
            ['METRIC_NAME', 'CHANNEL', 'LIFT', 'EXPOSED_PERCENT', 'CONTROL_PERCENT']
        ]
        print("\nTop 10 Significant Results:")
        print(top_sig.to_string())
        print()


def example_signal_vs_noise():
    """Identify metrics with consistent signal vs high noise."""
    print("=" * 80)
    print("Example 5: Signal vs Noise Analysis")
    print("=" * 80)
    
    # Use default data_dir (../data relative to script)
    analyzer = KantarBLSAnalyzer()
    analyzer.load_data(use_snowflake=False)
    analyzer.clean_and_merge()
    
    patterns = analyzer.identify_patterns()
    
    if 'signal_metrics' in patterns and 'noise_metrics' in patterns:
        print(f"\nMetrics with consistent signal: {len(patterns['signal_metrics'])}")
        print("\nTop Signal Metrics:")
        print(patterns['signal_metrics'].head(10)[['METRIC_NAME', 'MEAN_LIFT', 'STD_LIFT', 'COUNT']].to_string())
        
        print(f"\n\nMetrics with high noise: {len(patterns['noise_metrics'])}")
        print("\nTop Noise Metrics (to investigate):")
        print(patterns['noise_metrics'].head(10)[['METRIC_NAME', 'MEAN_LIFT', 'STD_LIFT', 'COUNT']].to_string())
        print()


if __name__ == "__main__":
    # Run examples
    try:
        example_basic_analysis()
    except Exception as e:
        print(f"Error in basic analysis: {e}")
    
    try:
        example_specific_metric()
    except Exception as e:
        print(f"Error in specific metric analysis: {e}")
    
    try:
        example_channel_comparison()
    except Exception as e:
        print(f"Error in channel comparison: {e}")
    
    try:
        example_significant_results()
    except Exception as e:
        print(f"Error in significant results: {e}")
    
    try:
        example_signal_vs_noise()
    except Exception as e:
        print(f"Error in signal vs noise analysis: {e}")

