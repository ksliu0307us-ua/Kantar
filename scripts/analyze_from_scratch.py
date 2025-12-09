"""
Complete Analysis Pipeline - Using ALL Available Data Sources

This script performs a full analysis from scratch using ALL available data sources:
- bls_metrics.csv - Main metrics table
- kantar_bls_filter_ids.csv - Filter metadata  
- kantar_bls_filters.csv - Additional filter details
- bls_answers.csv - User-level survey responses (optional)
- kantar_bls_sample_data.csv - New timestamp-aggregated format (if available, for validation)

The script uses the existing KantarBLSAnalyzer class which properly handles all these tables.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from analyze import KantarBLSAnalyzer


def main():
    """Main execution function - complete analysis from scratch."""
    print("=" * 80)
    print("KANTAR BLS COMPREHENSIVE ANALYSIS")
    print("Using ALL Available Data Sources")
    print("=" * 80)
    print()
    
    # Initialize analyzer (will use all available tables)
    analyzer = KantarBLSAnalyzer()
    
    # Step 1: Load all data
    print("STEP 1: Loading All Data Sources")
    print("-" * 80)
    analyzer.load_data(use_snowflake=False)
    print()
    
    # Step 2: Clean and merge
    print("STEP 2: Cleaning and Merging Data")
    print("-" * 80)
    analyzer.clean_and_merge(save_merged=True)
    print()
    
    # Step 3: Analyze trends
    print("STEP 3: Analyzing Trends")
    print("-" * 80)
    trends = analyzer.analyze_trends(group_by=['CHANNEL', 'METRIC_NAME'])
    print(f"✓ Generated {len(trends):,} trend combinations")
    print()
    
    # Step 4: Detect significance
    print("STEP 4: Detecting Significant Results")
    print("-" * 80)
    significant = analyzer.detect_significance(alpha=0.05)
    sig_count = significant['IS_SIGNIFICANT'].sum() if 'IS_SIGNIFICANT' in significant.columns else 0
    print(f"✓ Found {sig_count:,} significant results ({sig_count/len(significant)*100:.1f}%)")
    print()
    
    # Step 5: Identify patterns
    print("STEP 5: Identifying Patterns (Signal vs Noise)")
    print("-" * 80)
    patterns = analyzer.identify_patterns(min_observations=3)
    print(f"✓ Analyzed {len(patterns)} pattern categories")
    
    if 'signal_metrics' in patterns:
        print(f"  Signal metrics: {len(patterns['signal_metrics'])}")
    if 'noise_metrics' in patterns:
        print(f"  Noise metrics: {len(patterns['noise_metrics'])}")
    if 'consistent_signals' in patterns:
        print(f"  Consistent signals: {len(patterns['consistent_signals'])}")
    print()
    
    # Step 6: Find consistent signals
    print("STEP 6: Finding Consistent Signals Across Filters")
    print("-" * 80)
    consistent_signals = analyzer.find_consistent_signals(min_filters=3, min_lift=0.0)
    print(f"✓ Found {len(consistent_signals):,} metrics with consistent signals")
    if len(consistent_signals) > 0:
        print("\n  Top 5 Most Consistent Metrics:")
        for i, (_, row) in enumerate(consistent_signals.head(5).iterrows(), 1):
            print(f"    {i}. {row['METRIC_NAME']}: "
                  f"{row['AVG_LIFT']:.2f}% lift, "
                  f"consistency={row['CONSISTENCY_SCORE']:.2f}")
    print()
    
    # Step 7: Generate comprehensive report
    print("STEP 7: Generating Comprehensive Report")
    print("-" * 80)
    output_dir = script_dir.parent / "output"
    report_path = analyzer.generate_report(output_dir=str(output_dir))
    print(f"✓ Report generated: {report_path}")
    print()
    
    # Step 8: Save all analysis results
    print("STEP 8: Saving Analysis Results")
    print("-" * 80)
    try:
        saved_files = analyzer.save_all_analysis_results(output_dir=str(output_dir))
        print(f"✓ Saved {len(saved_files)} result files:")
        for key, path in saved_files.items():
            print(f"    - {key}: {Path(path).name}")
    except Exception as e:
        print(f"  Note: Could not save all results: {str(e)}")
    print()
    
    # Summary
    print("=" * 80)
    print("ANALYSIS COMPLETE!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Total observations analyzed: {len(analyzer.merged_data):,}")
    print(f"  - Unique metrics: {analyzer.merged_data['METRIC_NAME'].nunique()}")
    print(f"  - Unique channels: {analyzer.merged_data['CHANNEL'].nunique() if 'CHANNEL' in analyzer.merged_data.columns else 'N/A'}")
    print(f"  - Unique filters: {analyzer.merged_data['FILTER_ID'].nunique()}")
    print(f"  - Significant results: {sig_count:,}")
    print(f"  - Consistent signals: {len(consistent_signals):,}")
    print()
    print(f"All outputs saved to: {output_dir}")
    print()
    
    return analyzer, patterns, consistent_signals


if __name__ == "__main__":
    analyzer, patterns, consistent_signals = main()

