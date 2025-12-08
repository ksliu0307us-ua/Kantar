"""
Example: Saving Analysis Results
=================================

This script demonstrates how to save analysis results to files.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analyze import KantarBLSAnalyzer

def main():
    print("=" * 80)
    print("SAVING ANALYSIS RESULTS")
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
    
    # Set output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "output"
    
    print("\n" + "=" * 80)
    print("1. SAVE TIME SERIES ANALYSIS")
    print("=" * 80)
    print()
    
    # Save time series analysis
    print("Saving time series analysis (all metrics)...")
    time_series_file = analyzer.save_time_series_analysis(output_dir=str(output_dir))
    print(f"✓ Saved to: {time_series_file}")
    
    # Save time series for specific metric
    print("\nSaving time series for DashPass metrics...")
    dashpass_ts_file = analyzer.save_time_series_analysis(
        metric_name="DashPass",
        output_dir=str(output_dir)
    )
    print(f"✓ Saved to: {dashpass_ts_file}")
    
    print("\n" + "=" * 80)
    print("2. SAVE CHANNEL ANALYSIS")
    print("=" * 80)
    print()
    
    # Save channel analysis
    print("Saving channel analysis (all metrics)...")
    channel_file = analyzer.save_channel_analysis(output_dir=str(output_dir))
    print(f"✓ Saved to: {channel_file}")
    
    # Save channel analysis for specific metric
    print("\nSaving channel analysis for Brand Affinity...")
    affinity_channel_file = analyzer.save_channel_analysis(
        metric_name="Affinity",
        output_dir=str(output_dir)
    )
    print(f"✓ Saved to: {affinity_channel_file}")
    
    print("\n" + "=" * 80)
    print("3. SAVE INDIVIDUAL ANALYSIS RESULTS")
    print("=" * 80)
    print()
    
    # Run analysis and save manually
    print("Running consistent signals analysis...")
    consistent_signals = analyzer.find_consistent_signals()
    consistent_file = analyzer.save_analysis_results(
        results=consistent_signals,
        filename="consistent_signals_custom",
        output_dir=str(output_dir),
        format="csv"
    )
    print(f"✓ Saved to: {consistent_file}")
    
    # Save as Excel (if openpyxl is installed)
    try:
        print("\nSaving as Excel format...")
        excel_file = analyzer.save_analysis_results(
            results=consistent_signals.head(20),  # Just top 20 for example
            filename="consistent_signals_top20",
            output_dir=str(output_dir),
            format="excel"
        )
        print(f"✓ Saved to: {excel_file}")
    except ImportError:
        print("  Note: Excel format requires openpyxl. Install with: pip install openpyxl")
    
    print("\n" + "=" * 80)
    print("4. SAVE ALL ANALYSIS RESULTS")
    print("=" * 80)
    print()
    
    # Save all analysis results at once
    print("Saving all analysis results...")
    saved_files = analyzer.save_all_analysis_results(
        output_dir=str(output_dir),
        format="csv"
    )
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\n✓ Saved {len(saved_files)} analysis result files")
    print("\nAll saved files:")
    for analysis_type, file_path in saved_files.items():
        print(f"  - {analysis_type}: {file_path}")
    print()

if __name__ == "__main__":
    main()

