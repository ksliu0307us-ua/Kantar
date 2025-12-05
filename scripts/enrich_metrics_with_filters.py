"""
Enrich BLS Metrics with Human-Readable Filter Names
===================================================

This script joins bls_metrics with kantar_bls_filters and kantar_bls_filter_ids
using FILTER_ID as the join key to create enriched metrics with human-readable
filter names like "TV - Hispanic, exposed", "Gen Z, not exposed", etc.
"""

import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def create_human_readable_filter_name(row):
    """
    Create a human-readable filter name from filter metadata.
    
    Combines information from GROUP_NAME, FILTER_NAME, NAME, and SURVEY_LABEL
    to create descriptive names like "TV - Hispanic, exposed" or "Gen Z, not exposed"
    """
    parts = []
    
    # Get values, handling missing/NaN
    group_name = str(row.get('GROUP_NAME', '')).strip() if pd.notna(row.get('GROUP_NAME')) else ''
    filter_name = str(row.get('FILTER_NAME', '')).strip() if pd.notna(row.get('FILTER_NAME')) else ''
    name = str(row.get('NAME', '')).strip() if pd.notna(row.get('NAME')) else ''
    survey_label = str(row.get('SURVEY_LABEL', '')).strip() if pd.notna(row.get('SURVEY_LABEL')) else ''
    
    # Extract channel from filter name or group name
    channel_keywords = {
        'TV': ['TV', 'television', 'broadcast', 'network'],
        'Social': ['social', 'facebook', 'instagram', 'twitter', 'x', 'tiktok', 'snapchat', 'meta'],
        'Digital': ['digital', 'display', 'banner', 'programmatic', 'trade desk'],
        'Podcast': ['podcast', 'iheart', 'audio'],
        'OTT': ['OTT', 'streaming', 'hulu', 'netflix', 'amazon ctv', 'ctv'],
        'Radio': ['radio'],
        'Outdoor': ['billboard', 'outdoor', 'ooh']
    }
    
    channel = None
    text_to_search = f"{group_name} {filter_name} {name}".lower()
    for ch, keywords in channel_keywords.items():
        if any(kw in text_to_search for kw in keywords):
            channel = ch
            break
    
    # Extract demographic/segment info
    demo_keywords = {
        'Hispanic': ['hispanic', 'hisp'],
        'Gen Z': ['gen z', '18-24', '18 to 24'],
        'Millennial': ['millennial', '25-34', '25 to 34'],
        'Gen X': ['gen x', '35-44', '35 to 44', '45-54', '45 to 54'],
        'Boomer': ['boomer', '55+', '55 plus'],
        'Core': ['core'],
        'HISPANIC': ['HISPANIC']  # Survey label
    }
    
    demographic = None
    for demo, keywords in demo_keywords.items():
        if any(kw in text_to_search for kw in keywords):
            demographic = demo
            break
    
    # Note: Exposure status (exposed vs control) is typically in the metrics data
    # structure itself, not in filter names. Filter names describe the segment/channel.
    
    # Build human-readable name
    name_parts = []
    
    # Add channel
    if channel:
        name_parts.append(channel)
    
    # Add demographic
    if demographic:
        name_parts.append(demographic)
    
    # Add survey label if it's meaningful (not just "CORE" or "HISPANIC")
    if survey_label and survey_label.upper() not in ['CORE', 'HISPANIC']:
        name_parts.append(survey_label)
    
    # Add filter name if it's meaningful and not already captured
    if filter_name and filter_name not in name_parts:
        # Clean up filter name (remove "Creative:", "Site All Hits:", etc.)
        clean_filter = filter_name
        for prefix in ['Creative:', 'Site All Hits:', 'TV Network:', 'Placement']:
            if clean_filter.startswith(prefix):
                clean_filter = clean_filter.replace(prefix, '').strip()
                break
        if clean_filter and len(clean_filter) < 50:  # Only if reasonable length
            name_parts.append(clean_filter)
    
    # If we have group name that's meaningful, add it
    if group_name and group_name not in ['Creative', 'Site All Hits'] and group_name not in name_parts:
        name_parts.append(group_name)
    
    # Join parts
    if name_parts:
        readable_name = " - ".join(name_parts)
    else:
        # Fallback: use filter_name or name
        readable_name = filter_name or name or group_name or f"Filter {row.get('FILTER_ID', 'Unknown')}"
    
    return readable_name

def enrich_metrics():
    """
    Main function to enrich metrics with filter information.
    """
    print("=" * 80)
    print("ENRICHING BLS METRICS WITH HUMAN-READABLE FILTER NAMES")
    print("=" * 80)
    print()
    
    # Get data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    output_dir = script_dir.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    print("Step 1: Loading data files...")
    print("-" * 80)
    
    # Load bls_metrics
    metrics_file = data_dir / "bls_metrics.csv"
    if not metrics_file.exists():
        print(f"Error: {metrics_file} not found!")
        return
    
    print(f"  Loading {metrics_file.name}...")
    metrics = pd.read_csv(metrics_file, low_memory=False)
    print(f"  ✓ Loaded {len(metrics):,} rows")
    
    # Load kantar_bls_filter_ids
    filter_ids_file = data_dir / "kantar_bls_filter_ids.csv"
    if not filter_ids_file.exists():
        print(f"Error: {filter_ids_file} not found!")
        return
    
    print(f"  Loading {filter_ids_file.name}...")
    filter_ids = pd.read_csv(filter_ids_file, low_memory=False)
    print(f"  ✓ Loaded {len(filter_ids):,} rows")
    
    # Load kantar_bls_filters
    filters_file = data_dir / "kantar_bls_filters.csv"
    if not filters_file.exists():
        print(f"Error: {filters_file} not found!")
        return
    
    print(f"  Loading {filters_file.name}...")
    filters = pd.read_csv(filters_file, low_memory=False)
    print(f"  ✓ Loaded {len(filters):,} rows")
    print()
    
    print("Step 2: Joining tables on FILTER_ID...")
    print("-" * 80)
    
    # Join 1: metrics + filter_ids
    print("  Joining bls_metrics with kantar_bls_filter_ids...")
    enriched = metrics.merge(
        filter_ids[['FILTER_ID', 'GROUP_NAME', 'NAME', 'SURVEY_ID', 'SURVEY_LABEL']],
        on='FILTER_ID',
        how='left'
    )
    print(f"  ✓ After first join: {len(enriched):,} rows")
    
    # Join 2: result + filters
    print("  Joining with kantar_bls_filters...")
    # Note: filters table uses 'ID' column, not 'FILTER_ID'
    # Rename ID to FILTER_ID for joining
    if 'ID' in filters.columns:
        filters_renamed = filters.rename(columns={'ID': 'FILTER_ID'})
    else:
        filters_renamed = filters.copy()
    
    # Get unique filter_id rows from filters to avoid many-to-many
    filter_cols = ['FILTER_ID']
    for col in ['GROUP_NAME', 'NAME', 'SURVEY_ID']:
        if col in filters_renamed.columns:
            filter_cols.append(col)
    
    filters_unique = filters_renamed[filter_cols].drop_duplicates(subset=['FILTER_ID'])
    
    enriched = enriched.merge(
        filters_unique,
        on='FILTER_ID',
        how='left',
        suffixes=('_filter_ids', '_filters')
    )
    print(f"  ✓ After second join: {len(enriched):,} rows")
    print()
    
    print("Step 3: Consolidating columns...")
    print("-" * 80)
    
    # Consolidate GROUP_NAME (prefer filters, fallback to filter_ids)
    if 'GROUP_NAME_filters' in enriched.columns:
        enriched['GROUP_NAME'] = enriched['GROUP_NAME_filters'].fillna(enriched.get('GROUP_NAME_filter_ids', ''))
        enriched = enriched.drop(columns=['GROUP_NAME_filters', 'GROUP_NAME_filter_ids'], errors='ignore')
    elif 'GROUP_NAME_filter_ids' in enriched.columns:
        enriched['GROUP_NAME'] = enriched['GROUP_NAME_filter_ids']
        enriched = enriched.drop(columns=['GROUP_NAME_filter_ids'], errors='ignore')
    
    # Consolidate NAME/FILTER_NAME
    if 'NAME_filters' in enriched.columns:
        enriched['FILTER_NAME'] = enriched['NAME_filters'].fillna(enriched.get('NAME_filter_ids', ''))
        if 'NAME_filter_ids' in enriched.columns:
            enriched['NAME'] = enriched['NAME_filter_ids']
        enriched = enriched.drop(columns=['NAME_filters', 'NAME_filter_ids'], errors='ignore')
    elif 'NAME_filter_ids' in enriched.columns:
        enriched['FILTER_NAME'] = enriched['NAME_filter_ids']
        enriched['NAME'] = enriched['NAME_filter_ids']
    
    print("  ✓ Consolidated GROUP_NAME and FILTER_NAME columns")
    print()
    
    print("Step 4: Creating human-readable filter names...")
    print("-" * 80)
    
    # Create human-readable filter names
    enriched['FILTER_NAME_READABLE'] = enriched.apply(create_human_readable_filter_name, axis=1)
    
    # Show some examples
    print("  Sample human-readable filter names:")
    sample_names = enriched['FILTER_NAME_READABLE'].value_counts().head(10)
    for name, count in sample_names.items():
        print(f"    - {name}: {count:,} observations")
    print()
    
    print("Step 5: Saving enriched data...")
    print("-" * 80)
    
    # Save to output directory
    output_file = output_dir / "bls_metrics_enriched.csv"
    enriched.to_csv(output_file, index=False)
    file_size = output_file.stat().st_size / (1024 * 1024)  # MB
    print(f"  ✓ Saved enriched metrics to: {output_file}")
    print(f"    Rows: {len(enriched):,}")
    print(f"    Columns: {len(enriched.columns)}")
    print(f"    File size: {file_size:.2f} MB")
    print()
    
    # Also save to data directory for easy access
    data_output_file = data_dir / "bls_metrics_enriched.csv"
    enriched.to_csv(data_output_file, index=False)
    print(f"  ✓ Also saved to: {data_output_file}")
    print()
    
    print("Step 6: Summary statistics...")
    print("-" * 80)
    
    # Summary
    print(f"  Total metrics: {enriched['METRIC_NAME'].nunique():,}")
    print(f"  Total filters: {enriched['FILTER_ID'].nunique():,}")
    print(f"  Total unique filter names: {enriched['FILTER_NAME_READABLE'].nunique():,}")
    print(f"  Metrics with filter info: {enriched['FILTER_NAME_READABLE'].notna().sum():,}")
    print()
    
    # Show top filter names by observation count
    print("  Top 10 filter names by observation count:")
    top_filters = enriched['FILTER_NAME_READABLE'].value_counts().head(10)
    for i, (name, count) in enumerate(top_filters.items(), 1):
        print(f"    {i}. {name}: {count:,} observations")
    print()
    
    print("=" * 80)
    print("ENRICHMENT COMPLETE")
    print("=" * 80)
    print()
    print(f"Output file: {output_file}")
    print(f"Data file: {data_output_file}")
    print()
    print("You can now use this enriched file for analysis with human-readable filter names!")

if __name__ == "__main__":
    enrich_metrics()

