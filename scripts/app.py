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
if 'stability' not in st.session_state:
    st.session_state.stability = None
if 'ts_data' not in st.session_state:
    st.session_state.ts_data = None
if 'filter_results' not in st.session_state:
    st.session_state.filter_results = None

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
        if st.session_state.stability is not None:
            st.success("✅ Analysis Complete")
        else:
            st.info("⏳ Analysis Pending")
    
    with col3:
        data_dir = Path(__file__).parent.parent / "data"
        if (data_dir / "kantar_bls_transformed_data.csv").exists():
            st.success("✅ Transformed Data Available")
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
        "kantar_bls_transformed_data.csv",
        "bls_metrics.csv",
        "kantar_bls_filter_ids.csv",
        "kantar_bls_filters.csv"
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
                analyzer = ComprehensiveBLSAnalyzer()
                analyzer.load_all_data()
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
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Transformed Data", f"{len(analyzer.transformed_data):,}" if analyzer.transformed_data is not None else "0")
        with col2:
            st.metric("Metrics", f"{len(analyzer.metrics):,}" if analyzer.metrics is not None else "0")
        with col3:
            st.metric("Answers", f"{len(analyzer.answers):,}" if analyzer.answers is not None else "0")
        with col4:
            st.metric("Filters", f"{len(analyzer.filters):,}" if analyzer.filters is not None else "0")
        with col5:
            st.metric("Filter IDs", f"{len(analyzer.filter_ids):,}" if analyzer.filter_ids is not None else "0")

def show_analysis():
    """Analysis interface."""
    st.header("🔍 Analysis")
    
    if st.session_state.analyzer is None:
        st.warning("⚠️ Please load data first in the Data Loading section.")
        return
    
    st.subheader("Step 1: Clean and Standardize Data")
    
    if st.button("🧹 Clean and Standardize", type="primary", use_container_width=True):
        with st.spinner("Cleaning and standardizing data..."):
            try:
                analyzer = st.session_state.analyzer
                analyzer.clean_and_standardize()
                st.session_state.merged_data = analyzer.merged_data
                st.success("✅ Data cleaned and standardized!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
    
    if st.session_state.merged_data is not None:
        st.markdown("---")
        st.subheader("Step 2: Run Time Series Analysis")
        
        if st.button("📊 Run Time Series Analysis", type="primary", use_container_width=True):
            with st.spinner("Running time series analysis..."):
                try:
                    analyzer = st.session_state.analyzer
                    stability, ts_data = analyzer.time_series_analysis()
                    st.session_state.stability = stability
                    st.session_state.ts_data = ts_data
                    st.success("✅ Time series analysis complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)
        
        st.markdown("---")
        st.subheader("Step 3: Run Filter-Level Analysis")
        
        if st.button("🔍 Run Filter Analysis", type="primary", use_container_width=True):
            with st.spinner("Running filter-level analysis..."):
                try:
                    analyzer = st.session_state.analyzer
                    filter_results = analyzer.filter_level_analysis()
                    st.session_state.filter_results = filter_results
                    st.success("✅ Filter analysis complete!")
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
            if 'METRIC_NAME' in df.columns:
                st.metric("Unique Metrics", f"{df['METRIC_NAME'].nunique():,}")
            else:
                st.metric("Unique Metrics", "N/A")
        with col3:
            if 'CHANNEL' in df.columns:
                st.metric("Unique Channels", f"{df['CHANNEL'].nunique():,}")
            else:
                st.metric("Unique Channels", "N/A")
        
        # Show sample data
        if st.checkbox("Show Sample Data"):
            st.dataframe(df.head(100), use_container_width=True)

def show_results():
    """Results display."""
    st.header("📈 Analysis Results")
    
    if st.session_state.stability is None:
        st.warning("⚠️ Please run time series analysis first in the Analysis section.")
        return
    
    stability = st.session_state.stability
    ts_data = st.session_state.ts_data
    filter_results = st.session_state.filter_results
    
    # Tabs for different result types
    tab1, tab2, tab3, tab4 = st.tabs(["Stability Analysis", "Time Series Data", "Filter Analysis", "Signal vs Noise"])
    
    with tab1:
        if stability is not None and len(stability) > 0:
            st.subheader("Metric Stability Analysis")
            
            # Find metric column name
            metric_col = 'METRIC_NAME' if 'METRIC_NAME' in stability.columns else ('METRIC' if 'METRIC' in stability.columns else 'metric_name')
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                min_stability = st.slider("Min Stability Score", 0.0, 1.0, 0.0, 0.01)
            with col2:
                signal_type_filter = st.selectbox("Signal Type", ["All", "Signal", "Uncertain", "Noise"])
            
            # Filter data
            filtered = stability[stability['stability_score'] >= min_stability].copy()
            if signal_type_filter != "All" and 'signal_type' in filtered.columns:
                filtered = filtered[filtered['signal_type'] == signal_type_filter]
            
            st.metric("Filtered Results", len(filtered))
            st.dataframe(filtered.head(500), use_container_width=True)
            
            # Download button
            csv = filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download Stability Analysis CSV",
                data=csv,
                file_name=f"stability_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Run time series analysis to see results here.")
    
    with tab2:
        if ts_data is not None and len(ts_data) > 0:
            st.subheader("Time Series Data")
            
            # Find metric column name
            metric_col = 'METRIC_NAME' if 'METRIC_NAME' in ts_data.columns else ('METRIC' if 'METRIC' in ts_data.columns else 'metric_name')
            time_col = 'timestamp' if 'timestamp' in ts_data.columns else None
            
            if metric_col and metric_col in ts_data.columns:
                # Metric selector
                metrics_list = sorted(ts_data[metric_col].unique())
                selected_metric = st.selectbox("Select Metric", metrics_list)
                
                metric_ts = ts_data[ts_data[metric_col] == selected_metric].sort_values(time_col if time_col else metric_col)
                st.dataframe(metric_ts, use_container_width=True)
                
                # Download button
                csv = metric_ts.to_csv(index=False)
                st.download_button(
                    label="📥 Download Time Series CSV",
                    data=csv,
                    file_name=f"time_series_{selected_metric[:50]}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.dataframe(ts_data.head(500), use_container_width=True)
        else:
            st.info("Run time series analysis to see results here.")
    
    with tab3:
        if filter_results is not None and len(filter_results) > 0:
            st.subheader("Filter-Level Analysis")
            
            filter_type = st.selectbox("Select Filter Type", list(filter_results.keys()))
            
            if filter_type in filter_results:
                results = filter_results[filter_type]
                
                st.markdown(f"**Analysis by {filter_type}**")
                
                if 'by_filter' in results:
                    st.dataframe(results['by_filter'].head(500), use_container_width=True)
                
                st.markdown("---")
                st.markdown(f"**Stability by {filter_type}**")
                
                if 'stability' in results:
                    st.dataframe(results['stability'], use_container_width=True)
        else:
            st.info("Run filter-level analysis to see results here.")
    
    with tab4:
        if stability is not None and len(stability) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Signal Metrics")
                signal_metrics = stability[stability['signal_type'] == 'Signal'] if 'signal_type' in stability.columns else pd.DataFrame()
                if len(signal_metrics) > 0:
                    metric_col = 'METRIC_NAME' if 'METRIC_NAME' in signal_metrics.columns else ('METRIC' if 'METRIC' in signal_metrics.columns else 'metric_name')
                    st.metric("Count", len(signal_metrics))
                    st.dataframe(signal_metrics.head(20), use_container_width=True)
                else:
                    st.info("No signal metrics identified.")
            
            with col2:
                st.subheader("Noise Metrics")
                noise_metrics = stability[stability['signal_type'] == 'Noise'] if 'signal_type' in stability.columns else pd.DataFrame()
                if len(noise_metrics) > 0:
                    st.metric("Count", len(noise_metrics))
                    st.dataframe(noise_metrics.head(20), use_container_width=True)
                else:
                    st.info("No noise metrics identified.")
        else:
            st.info("Run time series analysis to see signal vs noise classification.")

def show_visualizations():
    """Visualizations."""
    st.header("📊 Visualizations")
    
    if st.session_state.merged_data is None:
        st.warning("⚠️ Please load and process data first.")
        return
    
    df = st.session_state.merged_data
    
    # Find column names
    metric_col = 'METRIC_NAME' if 'METRIC_NAME' in df.columns else ('METRIC' if 'METRIC' in df.columns else 'metric_name')
    lift_col = 'LIFT' if 'LIFT' in df.columns else ('lift' if 'lift' in df.columns else None)
    channel_col = 'CHANNEL' if 'CHANNEL' in df.columns else ('channel' if 'channel' in df.columns else None)
    
    if not lift_col or lift_col not in df.columns:
        st.error("⚠️ Lift column not found in data.")
        return
    
    # Visualization options
    viz_type = st.selectbox(
        "Select Visualization",
        ["Lift by Channel", "Top Metrics", "Lift Heatmap", "Custom Analysis"]
    )
    
    if viz_type == "Lift by Channel":
        if channel_col and channel_col in df.columns:
            st.subheader("Average Lift by Channel")
            
            channel_lift = df.groupby(channel_col)[lift_col].mean().sort_values()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            channel_lift.plot(kind='barh', ax=ax, color='steelblue')
            ax.set_xlabel('Average Lift (%)')
            ax.set_title('Average Brand Lift by Channel')
            ax.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("Channel column not found in data.")
    
    elif viz_type == "Top Metrics":
        if metric_col and metric_col in df.columns:
            st.subheader("Top Metrics by Average Lift")
            
            n_metrics = st.slider("Number of Metrics", 5, 30, 15)
            
            metric_lift = df.groupby(metric_col)[lift_col].mean().sort_values(ascending=False).head(n_metrics)
            
            fig, ax = plt.subplots(figsize=(12, max(6, n_metrics * 0.4)))
            ax.barh(range(len(metric_lift)), metric_lift.values)
            ax.set_yticks(range(len(metric_lift)))
            ax.set_yticklabels(metric_lift.index, fontsize=9)
            ax.set_xlabel('Average Lift (%)')
            ax.set_title(f'Top {n_metrics} Metrics by Average Lift')
            ax.axvline(x=0, color='black', linestyle='--', linewidth=0.5)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("Metric column not found in data.")
    
    elif viz_type == "Lift Heatmap":
        if channel_col and metric_col and channel_col in df.columns and metric_col in df.columns:
            st.subheader("Lift Heatmap: Metrics by Channel")
            
            # Create pivot table
            pivot = df.pivot_table(
                index=metric_col,
                columns=channel_col,
                values=lift_col,
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
        else:
            st.warning("Required columns (channel, metric) not found in data.")
    
    elif viz_type == "Custom Analysis":
        st.subheader("Custom Analysis")
        
        available_cols = [col for col in df.columns if col not in [lift_col]]
        group_by = st.multiselect(
            "Group By",
            available_cols,
            default=[channel_col] if channel_col and channel_col in available_cols else []
        )
        
        metric_filter = st.text_input("Filter Metric Name (optional)", "")
        
        if st.button("Generate Custom Visualization"):
            filtered_df = df.copy()
            
            if metric_filter and metric_col and metric_col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[metric_col].str.contains(metric_filter, case=False, na=False)]
            
            if group_by:
                custom_analysis = filtered_df.groupby(group_by)[lift_col].agg(['mean', 'std', 'count']).reset_index()
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
        include_visualizations = st.checkbox("Generate Visualizations", value=True)
        include_summary = st.checkbox("Include Summary Statistics", value=True)
    
    with col2:
        include_filter_analysis = st.checkbox("Include Filter Analysis", value=True)
        include_stability = st.checkbox("Include Stability Analysis", value=True)
    
    if st.button("📄 Generate Full Report", type="primary", use_container_width=True):
        with st.spinner("Generating report..."):
            try:
                analyzer = st.session_state.analyzer
                
                # Generate visualizations if requested
                if include_visualizations:
                    analyzer.generate_visualizations(
                        stability=st.session_state.stability,
                        ts_data=st.session_state.ts_data
                    )
                
                # Generate report
                report_text = analyzer.export_summary_report(
                    stability=st.session_state.stability,
                    filter_results=st.session_state.filter_results
                )
                
                st.success("✅ Report generated!")
                
                # Show report preview
                st.text_area("Report Preview", report_text, height=300)
                
                # Download button
                st.download_button(
                    label="📥 Download Report",
                    data=report_text,
                    file_name=f"comprehensive_analysis_report_{datetime.now().strftime('%Y%m%d')}.txt",
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
        
        metric_col = 'METRIC_NAME' if 'METRIC_NAME' in df.columns else ('METRIC' if 'METRIC' in df.columns else None)
        lift_col = 'LIFT' if 'LIFT' in df.columns else ('lift' if 'lift' in df.columns else None)
        channel_col = 'CHANNEL' if 'CHANNEL' in df.columns else ('channel' if 'channel' in df.columns else None)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Observations", f"{len(df):,}")
        with col2:
            if lift_col and lift_col in df.columns:
                st.metric("Average Lift", f"{df[lift_col].mean():.2f}%")
            else:
                st.metric("Average Lift", "N/A")
        with col3:
            if channel_col and channel_col in df.columns:
                st.metric("Channels", df[channel_col].nunique())
            else:
                st.metric("Channels", "N/A")
        with col4:
            if metric_col and metric_col in df.columns:
                st.metric("Metrics", df[metric_col].nunique())
            else:
                st.metric("Metrics", "N/A")

if __name__ == "__main__":
    main()

