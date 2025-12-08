"""
Example: Running Analysis with Logging
=======================================

This script demonstrates how to capture and save all console output
during analysis to a log file.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analyze import KantarBLSAnalyzer, log_to_file

def example_with_logging_method():
    """Example using the analyzer's built-in logging method."""
    print("=" * 80)
    print("EXAMPLE 1: Using Analyzer's Built-in Logging")
    print("=" * 80)
    print()
    
    analyzer = KantarBLSAnalyzer()
    
    # Set output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "output"
    
    # Enable logging - all subsequent print statements will be saved
    log_path = analyzer.enable_logging(output_dir=str(output_dir))
    print(f"Logging enabled. All output will be saved to: {log_path}")
    print()
    
    try:
        # Run your analysis - all output is automatically logged
        print("Starting analysis...")
        analyzer.load_data(use_snowflake=False)
        analyzer.clean_and_merge()
        
        # Run some analyses
        print("\nRunning time series analysis...")
        time_series = analyzer.analyze_time_series()
        print(f"✓ Time series analysis complete: {len(time_series)} results")
        
        print("\nRunning channel analysis...")
        channels = analyzer.analyze_by_channel()
        print(f"✓ Channel analysis complete: {len(channels)} results")
        
        print("\nFinding consistent signals...")
        signals = analyzer.find_consistent_signals()
        print(f"✓ Found {len(signals)} consistent signals")
        
        print("\n✓ Analysis complete!")
        
    finally:
        # Always disable logging when done
        analyzer.disable_logging()
        print(f"\n✓ Log file saved to: {log_path}")


def example_with_context_manager():
    """Example using the context manager approach."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Using Context Manager")
    print("=" * 80)
    print()
    
    analyzer = KantarBLSAnalyzer()
    
    # Set output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "output"
    log_path = output_dir / f"analysis_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Use context manager - automatically handles setup/teardown
    with log_to_file(log_path):
        print("Starting analysis with context manager...")
        analyzer.load_data(use_snowflake=False)
        analyzer.clean_and_merge()
        
        print("\nRunning analysis...")
        trends = analyzer.analyze_trends()
        print(f"✓ Analysis complete: {len(trends)} results")
    
    print(f"\n✓ Log file saved to: {log_path}")


def example_custom_log_filename():
    """Example with custom log filename."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Custom Log Filename")
    print("=" * 80)
    print()
    
    analyzer = KantarBLSAnalyzer()
    
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "output"
    
    # Use custom log filename
    log_path = analyzer.enable_logging(
        log_file="my_custom_analysis_log.txt",
        output_dir=str(output_dir)
    )
    
    try:
        print("Running analysis with custom log file...")
        analyzer.load_data(use_snowflake=False)
        analyzer.clean_and_merge()
        
        # Your analysis code here
        print("✓ Analysis steps completed")
        
    finally:
        analyzer.disable_logging()
        print(f"✓ Log saved to: {log_path}")


if __name__ == "__main__":
    from datetime import datetime
    
    # Run examples
    example_with_logging_method()
    # example_with_context_manager()  # Uncomment to try this approach
    # example_custom_log_filename()   # Uncomment to try this approach

