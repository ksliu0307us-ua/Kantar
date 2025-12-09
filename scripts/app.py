"""
Kantar BLS Analysis - Streamlit Web UI
======================================

Interactive web interface for Kantar Brand Lift Survey analysis.
Allows non-technical users to run analysis, explore results, and generate reports.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from comprehensive_analysis import ComprehensiveBLSAnalyzer

# Page configuration
st.set_page_config(
    page_title="Kantar BLS Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'merged_data' not in st.session_state:
    st.session_state.merged_data = None
if 'patterns' not in st.session_state:
    st.session_state.patterns = None

def main():
    """Main application."""
    
    # Header
    st.markdown('<p class="main-header">📊 Kantar Brand Lift Survey Analysis</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["🏠 Home", "📁 Data Loading", "🔍 Analysis", "📈 Results", "📊 Visualizations", "📄 Reports"]
    )
    
    if page == "🏠 Home":
        show_home()
    elif page == "📁 Data Loading":
        show_data_loading()
    elif page == "🔍 Analysis":
        show_analysis()
    elif page == "📈 Results":
        show_results()
    elif page == "📊 Visualizations":
        show_visualizations()
    elif page == "📄 Reports":
        show_reports()

def show_home():
    """Home page with overview."""
    st.header("Welcome to Kantar BLS Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### What This Tool Does
        
        This interactive dashboard helps you:
        
        - 📥 **Load** Kantar BLS data from CSV files
        - 🧹 **Clean and merge** multiple data sources
        - 🔍 **Analyze** brand lift across channels and demographics
        - 📊 **Visualize** trends and patterns
        - 📈 **Identify** signal vs noise in metrics
        - 📄 **Generate** comprehensive reports
        
        ### Quick Start
        
        1. Go to **Data Loading** to load your data
        2. Run **Analysis** to process the data
        3. Explore **Results** and **Visualizations**
        4. Generate **Reports** for your team
        """)
    
    with col2:
        st.markdown("""
        ### Key Features
        
        ✅ **Automatic Data Detection**
        - Uses pre-merged files when available
        - Falls back to individual file loading
        
        ✅ **Dimension Extraction**
        - Automatically identifies channels (TV, Social, Digital, etc.)
        - Extracts demographics and time periods
        
        ✅ **Signal Detection**
        - Statistical significance testing
        - Consistency analysis (CV)
        - Separates reliable metrics from noise
        
        ✅ **Interactive Exploration**
        - Filter by channel, metric, or demographic
        - Drill down into specific results
        - Export findings
        """)
    
    # Status check
    st.markdown("---")
    st.subheader("Current Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.merged_data is not None:
            st.success("✅ Data Loaded")
            st.metric("Rows", f"{len(st.session_state.merged_data):,}")
        else:
            st.info("⏳ No Data Loaded")
    
    with col2:
        if st.session_state.patterns is not None:
            st.success("✅ Analysis Complete")
        else:
            st.info("⏳ Analysis Pending")
    
    with col3:
        data_dir = Path(__file__).parent.parent / "data"
        if (data_dir / "bls_metrics_with_filters.csv").exists():
            st.success("✅ Pre-merged File Available")
        else:
            st.warning("⚠️ Using Individual Files")

def show_data_loading():
    """Data loading interface."""
    st.header("📁 Data Loading")
    
    # Data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    
    st.info(f"Data directory: `{data_dir}`")
    
    # Check available files
    st.subheader("Available Files")
    
    required_files = [
        "bls_metrics.csv",
        "bls_metrics_with_filters.csv",
        "kantar_bls_filters.csv",
        "kantar_bls_filter_ids.csv"
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Required Files:**")
        for file in required_files:
            file_path = data_dir / file
            if file_path.exists():
                st.success(f"✅ {file}")
            else:
                st.error(f"❌ {file}")
    
    with col2:
        st.markdown("**Optional Files:**")
        optional_files = ["bls_answers.csv"]
        codebook_files = list(data_dir.glob("*codebook*.csv"))
        
        for file in optional_files:
            file_path = data_dir / file
            if file_path.exists():
                st.success(f"✅ {file}")
            else:
                st.info(f"⏭️ {file} (optional)")
        
        if codebook_files:
            st.success(f"✅ Codebook mapping found")
        else:
            st.warning("⚠️ Codebook mapping not found")
    
    # Load data button
    st.markdown("---")
    
    if st.button("🔄 Load Data", type="primary", use_container_width=True):
        with st.spinner("Loading data..."):
            try:
                analyzer = KantarBLSAnalyzer()
                analyzer.load_data(use_snowflake=False)
                st.session_state.analyzer = analyzer
                st.success("✅ Data loaded successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
                st.exception(e)
    
    # Show loaded data info
    if st.session_state.analyzer is not None:
        st.markdown("---")
        st.subheader("Loaded Data Summary")
        
        analyzer = st.session_state.analyzer
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Metrics", f"{len(analyzer.metrics):,}" if analyzer.metrics is not None else "0")
        with col2:
            st.metric("Answers", f"{len(analyzer.answers):,}" if analyzer.answers is not None else "0")
        with col3:
            st.metric("Filters", f"{len(analyzer.filters):,}" if analyzer.filters is not None else "0")
        with col4:
            st.metric("Filter IDs", f"{len(analyzer.filter_ids):,}" if analyzer.filter_ids is not None else "0")

def show_analysis():
    """Analysis interface."""
    st.header("🔍 Analysis")
    
    if st.session_state.analyzer is None:
        st.warning("⚠️ Please load data first in the Data Loading section.")
        return
    
    st.subheader("Step 1: Clean and Merge Data")
    
    if st.button("🧹 Clean and Merge", type="primary", use_container_width=True):
        with st.spinner("Cleaning and merging data..."):
            try:
                analyzer = st.session_state.analyzer
                analyzer.clean_and_merge()
                st.session_state.merged_data = analyzer.merged_data
                st.success("✅ Data cleaned and merged!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
    
    if st.session_state.merged_data is not None:
        st.markdown("---")
        st.subheader("Step 2: Run Analysis")
        
        # Analysis options
        col1, col2 = st.columns(2)
        
        with col1:
            analyze_trends = st.checkbox("Analyze Trends", value=True)
            detect_significance = st.checkbox("Detect Significance", value=True)
        
        with col2:
            identify_patterns = st.checkbox("Identify Patterns", value=True)
            min_observations = st.number_input("Min Observations for Patterns", min_value=1, value=3)
        
        if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
            with st.spinner("Running analysis..."):
                try:
                    analyzer = st.session_state.analyzer
                    patterns = {}
                    
                    if analyze_trends:
                        trends = analyzer.analyze_trends(group_by=['CHANNEL', 'METRIC_NAME'])
                        patterns['trends'] = trends
                    
                    if detect_significance:
                        significant = analyzer.detect_significance(alpha=0.05)
                        patterns['significant'] = significant
                    
                    if identify_patterns:
                        pattern_results = analyzer.identify_patterns(min_observations=min_observations)
                        patterns.update(pattern_results)
                    
                    st.session_state.patterns = patterns
                    st.success("✅ Analysis complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)
        
        # Show merged data preview
        st.markdown("---")
        st.subheader("Data Preview")
        
        df = st.session_state.merged_data
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", f"{len(df):,}")
        with col2:
            st.metric("Unique Filters", f"{df['FILTER_ID'].nunique():,}")
        with col3:
            st.metric("Unique Metrics", f"{df['METRIC_ID'].nunique():,}")
        
        # Show sample data
        if st.checkbox("Show Sample Data"):
            st.dataframe(df.head(100), use_container_width=True)

def show_results():
    """Results display."""
    st.header("📈 Analysis Results")
    
    if st.session_state.patterns is None:
        st.warning("⚠️ Please run analysis first in the Analysis section.")
        return
    
    patterns = st.session_state.patterns
    
    # Tabs for different result types
    tab1, tab2, tab3, tab4 = st.tabs(["Trends", "Significant Results", "Patterns", "Signal vs Noise"])
    
    with tab1:
        if 'trends' in patterns:
            st.subheader("Trend Analysis")
            trends_df = patterns['trends']
            st.dataframe(trends_df, use_container_width=True)
            
            # Download button
            csv = trends_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Trends CSV",
                data=csv,
                file_name=f"trends_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Run trend analysis to see results here.")
    
    with tab2:
        if 'significant' in patterns:
            st.subheader("Statistically Significant Results")
            sig_df = patterns['significant']
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                min_lift = st.number_input("Min Lift (%)", value=-100.0, step=1.0)
            with col2:
                only_sig = st.checkbox("Only Significant", value=True)
            
            # Filter data
            filtered = sig_df.copy()
            if only_sig and 'IS_SIGNIFICANT' in filtered.columns:
                filtered = filtered[filtered['IS_SIGNIFICANT'] == True]
            filtered = filtered[filtered['LIFT'] >= min_lift]
            
            st.metric("Significant Results", len(filtered))
            st.dataframe(filtered.head(500), use_container_width=True)
            
            # Download
            csv = filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download Significant Results CSV",
                data=csv,
                file_name=f"significant_results_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Run significance detection to see results here.")
    
    with tab3:
        if 'channel_consistency' in patterns:
            st.subheader("Channel Consistency")
            channel_df = patterns['channel_consistency']
            st.dataframe(channel_df, use_container_width=True)
        else:
            st.info("Run pattern identification to see results here.")
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Signal Metrics")
            if 'signal_metrics' in patterns:
                signal_df = patterns['signal_metrics']
                st.metric("Count", len(signal_df))
                st.dataframe(signal_df.head(20), use_container_width=True)
            else:
                st.info("No signal metrics identified.")
        
        with col2:
            st.subheader("Noise Metrics")
            if 'noise_metrics' in patterns:
                noise_df = patterns['noise_metrics']
                st.metric("Count", len(noise_df))
                st.dataframe(noise_df.head(20), use_container_width=True)
            else:
                st.info("No noise metrics identified.")

def show_visualizations():
    """Visualizations."""
    st.header("📊 Visualizations")
    
    if st.session_state.merged_data is None:
        st.warning("⚠️ Please load and process data first.")
        return
    
    df = st.session_state.merged_data
    
    # Visualization options
    viz_type = st.selectbox(
        "Select Visualization",
        ["Lift by Channel", "Top Metrics", "Lift Heatmap", "Custom Analysis"]
    )
    
    if viz_type == "Lift by Channel":
        st.subheader("Average Lift by Channel")
        
        channel_lift = df.groupby('CHANNEL')['LIFT'].mean().sort_values()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        channel_lift.plot(kind='barh', ax=ax, color='steelblue')
        ax.set_xlabel('Average Lift (%)')
        ax.set_title('Average Brand Lift by Channel')
        ax.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        st.pyplot(fig)
    
    elif viz_type == "Top Metrics":
        st.subheader("Top Metrics by Average Lift")
        
        n_metrics = st.slider("Number of Metrics", 5, 30, 15)
        
        metric_lift = df.groupby('METRIC_NAME')['LIFT'].mean().sort_values(ascending=False).head(n_metrics)
        
        fig, ax = plt.subplots(figsize=(12, max(6, n_metrics * 0.4)))
        ax.barh(range(len(metric_lift)), metric_lift.values)
        ax.set_yticks(range(len(metric_lift)))
        ax.set_yticklabels(metric_lift.index, fontsize=9)
        ax.set_xlabel('Average Lift (%)')
        ax.set_title(f'Top {n_metrics} Metrics by Average Lift')
        ax.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
        plt.tight_layout()
        st.pyplot(fig)
    
    elif viz_type == "Lift Heatmap":
        st.subheader("Lift Heatmap: Metrics by Channel")
        
        # Create pivot table
        pivot = df.pivot_table(
            index='METRIC_NAME',
            columns='CHANNEL',
            values='LIFT',
            aggfunc='mean'
        )
        
        if not pivot.empty:
            fig, ax = plt.subplots(figsize=(14, max(8, len(pivot) * 0.3)))
            sns.heatmap(pivot, annot=True, fmt='.1f', cmap='RdYlGn', center=0, ax=ax, cbar_kws={'label': 'Lift (%)'})
            ax.set_title('Lift Heatmap: Metrics by Channel')
            ax.set_xlabel('Channel')
            ax.set_ylabel('Metric')
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("Not enough data for heatmap.")
    
    elif viz_type == "Custom Analysis":
        st.subheader("Custom Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            group_by = st.multiselect(
                "Group By",
                ['CHANNEL', 'METRIC_NAME', 'DEMOGRAPHIC', 'TIME_PERIOD'],
                default=['CHANNEL']
            )
        
        with col2:
            metric_filter = st.text_input("Filter Metric Name (optional)", "")
        
        if st.button("Generate Custom Visualization"):
            filtered_df = df.copy()
            
            if metric_filter:
                filtered_df = filtered_df[filtered_df['METRIC_NAME'].str.contains(metric_filter, case=False, na=False)]
            
            if group_by:
                custom_analysis = filtered_df.groupby(group_by)['LIFT'].agg(['mean', 'std', 'count']).reset_index()
                st.dataframe(custom_analysis, use_container_width=True)
                
                # Simple bar chart
                if len(group_by) == 1:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    custom_analysis.set_index(group_by[0])['mean'].plot(kind='bar', ax=ax)
                    ax.set_ylabel('Average Lift (%)')
                    ax.set_title(f'Average Lift by {group_by[0]}')
                    plt.xticks(rotation=45, ha='right')
                    plt.tight_layout()
                    st.pyplot(fig)

def show_reports():
    """Report generation."""
    st.header("📄 Generate Reports")
    
    if st.session_state.analyzer is None or st.session_state.merged_data is None:
        st.warning("⚠️ Please load data and run analysis first.")
        return
    
    st.subheader("Report Generation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_charts = st.checkbox("Include Visualizations", value=True)
        include_summary = st.checkbox("Include Summary Statistics", value=True)
    
    with col2:
        include_patterns = st.checkbox("Include Pattern Analysis", value=True)
        include_significant = st.checkbox("Include Significant Results", value=True)
    
    if st.button("📄 Generate Full Report", type="primary", use_container_width=True):
        with st.spinner("Generating report..."):
            try:
                analyzer = st.session_state.analyzer
                script_dir = Path(__file__).parent
                output_dir = script_dir.parent / "output"
                output_dir.mkdir(exist_ok=True)
                
                report_path = analyzer.generate_report(output_dir=str(output_dir))
                st.success(f"✅ Report generated: {report_path}")
                
                # Show report preview
                if Path(report_path).exists():
                    with open(report_path, 'r') as f:
                        report_text = f.read()
                    st.text_area("Report Preview", report_text, height=300)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Report",
                        data=report_text,
                        file_name=Path(report_path).name,
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
    
    # Quick stats
    st.markdown("---")
    st.subheader("Quick Statistics")
    
    if st.session_state.merged_data is not None:
        df = st.session_state.merged_data
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Observations", f"{len(df):,}")
        with col2:
            st.metric("Average Lift", f"{df['LIFT'].mean():.2f}%")
        with col3:
            st.metric("Channels", df['CHANNEL'].nunique())
        with col4:
            st.metric("Metrics", df['METRIC_NAME'].nunique())

if __name__ == "__main__":
    main()

