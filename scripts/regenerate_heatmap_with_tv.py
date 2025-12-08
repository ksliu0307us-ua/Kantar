"""
Regenerate heatmap using new sample data that includes TV channel.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re
from datetime import datetime

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

def extract_channel(exposed_filter: str, weight_set: str = None) -> str:
    """
    Extract channel from EXPOSED_FILTER or WEIGHT_SET column.
    
    Examples:
    - "XM: 2. Social" -> "Social"
    - "XM: 3. TV" -> "TV"
    - "XM: 4. Digital" -> "Digital"
    """
    # Priority 1: Try WEIGHT_SET first (more reliable for channel info)
    if weight_set and pd.notna(weight_set):
        text = str(weight_set)
        
        # Pattern: "XM: N. Channel" or "XM: Channel"
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
    
    # Check for combo filters
    if "combo" in text.lower() or "through" in text.lower():
        if "0. ANY" in text.upper():
            return "Any"
        elif "4. Digital" in text:
            return "Digital"
    
    return "Other"

def main():
    """Main function to regenerate heatmap with TV data."""
    print("=" * 80)
    print("REGENERATING HEATMAP WITH TV DATA")
    print("=" * 80)
    print()
    
    # Get paths
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    output_dir = script_dir.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Load new sample data
    sample_file = data_dir / "kantar_bls_sample_data.csv"
    if not sample_file.exists():
        print(f"Error: {sample_file} not found!")
        return
    
    print(f"Loading data from {sample_file.name}...")
    df = pd.read_csv(sample_file, low_memory=False)
    print(f"  Loaded {len(df):,} rows")
    print()
    
    # Extract channels
    print("Extracting channels...")
    df['CHANNEL'] = df.apply(
        lambda row: extract_channel(
            row.get('EXPOSED_FILTER', ''),
            row.get('WEIGHT_SET', '')
        ),
        axis=1
    )
    
    # Clean metric names
    df['METRIC_CLEAN'] = df['METRIC'].str.strip()
    
    # Check channels found
    print("\nChannels found:")
    channel_counts = df['CHANNEL'].value_counts()
    print(channel_counts)
    print()
    
    # Filter out rows with missing data
    df_clean = df[
        (df['CHANNEL'].notna()) & 
        (df['METRIC_CLEAN'].notna()) &
        (df['LIFT'].notna())
    ].copy()
    
    print(f"After cleaning: {len(df_clean):,} rows")
    print()
    
    # Aggregate by channel and metric
    print("Aggregating by channel and metric...")
    channel_metric = df_clean.groupby(['CHANNEL', 'METRIC_CLEAN']).agg({
        'LIFT': ['mean', 'std', 'count'],
        'EXPOSED_N': 'sum',
        'CONTROL_N': 'sum'
    }).reset_index()
    
    # Flatten column names
    channel_metric.columns = [
        'CHANNEL', 'METRIC_CLEAN', 'MEAN_LIFT', 'STD_LIFT', 'COUNT',
        'EXPOSED_N_SUM', 'CONTROL_N_SUM'
    ]
    
    # Filter by minimum observations
    min_obs = 1  # Lower threshold to include more data
    channel_metric = channel_metric[channel_metric['COUNT'] >= min_obs]
    
    print(f"  Generated {len(channel_metric):,} channel-metric combinations")
    print()
    
    # Create pivot table for heatmap
    print("Creating heatmap...")
    pivot = channel_metric.pivot_table(
        index='METRIC_CLEAN',
        columns='CHANNEL',
        values='MEAN_LIFT',
        aggfunc='mean'
    )
    
    # Sort channels (put TV first if it exists)
    if 'TV' in pivot.columns:
        channel_order = ['TV'] + [c for c in pivot.columns if c != 'TV']
        pivot = pivot[channel_order]
    
    # Sort metrics by average lift across all channels
    pivot['avg_lift'] = pivot.mean(axis=1)
    pivot = pivot.sort_values('avg_lift', ascending=False)
    pivot = pivot.drop('avg_lift', axis=1)
    
    print(f"  Heatmap dimensions: {len(pivot)} metrics × {len(pivot.columns)} channels")
    print()
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(max(8, len(pivot.columns) * 1.5), max(10, len(pivot) * 0.3)))
    
    # Use RdYlGn colormap (red-yellow-green) centered at 0
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
    
    # Save heatmap
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"lift_heatmap_with_tv_{timestamp}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Heatmap saved to: {output_file}")
    
    # Also save as lift_heatmap.png (overwrite old one)
    output_file_main = output_dir / "lift_heatmap.png"
    plt.savefig(output_file_main, dpi=300, bbox_inches='tight')
    print(f"✓ Also saved as: {output_file_main}")
    
    plt.close()
    
    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total metrics: {len(pivot)}")
    print(f"Channels included: {', '.join(pivot.columns)}")
    print(f"TV data included: {'Yes' if 'TV' in pivot.columns else 'No'}")
    print()
    
    # Show channel averages
    print("Average lift by channel:")
    channel_avg = channel_metric.groupby('CHANNEL')['MEAN_LIFT'].mean().sort_values(ascending=False)
    for channel, avg_lift in channel_avg.items():
        print(f"  {channel}: {avg_lift:.2f}%")
    print()
    
    print("=" * 80)
    print("DONE!")
    print("=" * 80)

if __name__ == "__main__":
    main()

