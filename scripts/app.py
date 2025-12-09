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
if 'lift_by_month_group' not in st.session_state:
    st.session_state.lift_by_month_group = None
if 'top_bottom_filters' not in st.session_state:
    st.session_state.top_bottom_filters = None
if 'unstable_patterns' not in st.session_state:
    st.session_state.unstable_patterns = None

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
        if st.session_state.lift_by_month_group is not None:
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
            st.success("✅ Codebook mapping found")
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
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Transformed Data", f"{len(analyzer.transformed_data):,}" if analyzer.transformed_data is not None else "0")
        with col2:
            st.metric("Filter IDs", f"{len(analyzer.filter_ids):,}" if analyzer.filter_ids is not None else "0")
        with col3:
            st.metric("Filters", f"{len(analyzer.filters):,}" if analyzer.filters is not None else "0")

def show_analysis():
    """Analysis interface."""
    st.header("🔍 Analysis")
    
    if st.session_state.analyzer is None:
        st.warning("⚠️ Please load data first in the Data Loading section.")
        return
    
    st.subheader("Step 1: Merge Data and Extract Survey Month")
    
    if st.button("🔄 Merge Data", type="primary", use_container_width=True):
        with st.spinner("Merging data and extracting survey_month..."):
            try:
                analyzer = st.session_state.analyzer
                analyzer.merge_data()
                st.session_state.merged_data = analyzer.merged_data
                st.success("✅ Data merged successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
    
    if st.session_state.merged_data is not None:
        st.markdown("---")
        st.subheader("Step 2: Run Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Analyze Lift by Month & Group", type="primary", use_container_width=True):
                with st.spinner("Analyzing lift by month and group..."):
                    try:
                        analyzer = st.session_state.analyzer
                        lift_by_month_group = analyzer.analyze_lift_by_month_and_group()
                        st.session_state.lift_by_month_group = lift_by_month_group
                        st.success("✅ Analysis complete!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.exception(e)
            
            if st.button("🔝 Identify Top/Bottom Filters", type="primary", use_container_width=True):
                with st.spinner("Identifying top and bottom filters..."):
                    try:
                        analyzer = st.session_state.analyzer
                        top_bottom = analyzer.identify_top_bottom_filters()
                        st.session_state.top_bottom_filters = top_bottom
                        st.success("✅ Analysis complete!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.exception(e)
        
        with col2:
            if st.button("⚠️ Identify Unstable Patterns", type="primary", use_container_width=True):
                with st.spinner("Identifying unstable patterns..."):
                    try:
                        analyzer = st.session_state.analyzer
                        unstable = analyzer.identify_unstable_patterns()
                        st.session_state.unstable_patterns = unstable
                        st.success("✅ Analysis complete!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.exception(e)
            
            if st.button("📈 Create Visualizations", type="primary", use_container_width=True):
                with st.spinner("Creating visualizations..."):
                    try:
                        analyzer = st.session_state.analyzer
                        analyzer.create_visualizations()
                        st.success("✅ Visualizations created!")
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
            if 'survey_month' in df.columns:
                st.metric("Unique Months", f"{df['survey_month'].nunique():,}")
            else:
                st.metric("Unique Months", "N/A")
        with col3:
            if 'GROUP_NAME' in df.columns:
                st.metric("Unique Groups", f"{df['GROUP_NAME'].nunique():,}")
            else:
                st.metric("Unique Groups", "N/A")
        
        # Show sample data
        if st.checkbox("Show Sample Data"):
            st.dataframe(df.head(100), use_container_width=True)

def show_results():
    """Results display."""
    st.header("📈 Analysis Results")
    
    if st.session_state.lift_by_month_group is None:
        st.warning("⚠️ Please run analysis first in the Analysis section.")
        return
    
    lift_by_month_group = st.session_state.lift_by_month_group
    top_bottom = st.session_state.top_bottom_filters
    unstable = st.session_state.unstable_patterns
    
    # Tabs for different result types
    tab1, tab2, tab3, tab4 = st.tabs(["Lift by Month & Group", "Top/Bottom Filters", "Unstable Patterns", "Summary"])
    
    with tab1:
        if lift_by_month_group is not None and len(lift_by_month_group) > 0:
            st.subheader("Average Lift by Month and Group")
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                selected_month = st.selectbox("Filter by Month", ["All"] + sorted(lift_by_month_group['survey_month'].unique().tolist()))
            with col2:
                min_lift = st.number_input("Min Average Lift (%)", value=-100.0, step=1.0)
            
            # Filter data
            filtered = lift_by_month_group[lift_by_month_group['avg_lift'] >= min_lift].copy()
            if selected_month != "All":
                filtered = filtered[filtered['survey_month'] == selected_month]
            
            st.metric("Filtered Results", len(filtered))
            st.dataframe(filtered.head(500), use_container_width=True)
            
            # Download button
            csv = filtered.to_csv(index=False)
            st.download_button(
                label="📥 Download Lift by Month & Group CSV",
                data=csv,
                file_name=f"lift_by_month_group_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Run analysis to see results here.")
    
    with tab2:
        if top_bottom is not None:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Top 5 Filters")
                if 'top_5' in top_bottom:
                    st.dataframe(top_bottom['top_5'], use_container_width=True)
                    csv = top_bottom['top_5'].to_csv(index=False)
                    st.download_button(
                        label="📥 Download Top 5 CSV",
                        data=csv,
                        file_name=f"top_5_filters_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No top filters data available.")
            
            with col2:
                st.subheader("Bottom 5 Filters")
                if 'bottom_5' in top_bottom:
                    st.dataframe(top_bottom['bottom_5'], use_container_width=True)
                    csv = top_bottom['bottom_5'].to_csv(index=False)
                    st.download_button(
                        label="📥 Download Bottom 5 CSV",
                        data=csv,
                        file_name=f"bottom_5_filters_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No bottom filters data available.")
        else:
            st.info("Run top/bottom filter analysis to see results here.")
    
    with tab3:
        if unstable is not None and len(unstable) > 0:
            st.subheader("Unstable Patterns (High Standard Deviation)")
            
            st.markdown("Filters with high coefficient of variation (CV) or high range indicate unstable patterns.")
            
            # Filter options
            min_cv = st.slider("Min CV Threshold", 0.0, 10.0, 0.0, 0.1)
            
            filtered_unstable = unstable[unstable['cv'] >= min_cv].copy()
            
            st.metric("Unstable Filters", len(filtered_unstable))
            st.dataframe(filtered_unstable.head(100), use_container_width=True)
            
            # Download button
            csv = filtered_unstable.to_csv(index=False)
            st.download_button(
                label="📥 Download Unstable Patterns CSV",
                data=csv,
                file_name=f"unstable_patterns_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Run unstable pattern analysis to see results here.")
    
    with tab4:
        st.subheader("Analysis Summary")
        
        summary_text = []
        
        if lift_by_month_group is not None and len(lift_by_month_group) > 0:
            summary_text.append("**Lift by Month & Group:**")
            summary_text.append(f"- Total combinations: {len(lift_by_month_group)}")
            summary_text.append(f"- Average lift: {lift_by_month_group['avg_lift'].mean():.2f}%")
            summary_text.append(f"- Date range: {lift_by_month_group['survey_month'].min()} to {lift_by_month_group['survey_month'].max()}")
            summary_text.append("")
        
        if top_bottom is not None:
            if 'top_5' in top_bottom:
                summary_text.append("**Top 5 Filters:**")
                for i, (_, row) in enumerate(top_bottom['top_5'].iterrows(), 1):
                    summary_text.append(f"{i}. {row['FILTER_NAME']}: {row['avg_lift']:.2f}%")
                summary_text.append("")
        
        if unstable is not None and len(unstable) > 0:
            summary_text.append(f"**Unstable Patterns:**")
            summary_text.append(f"- Found {len(unstable)} unstable filters")
            summary_text.append(f"- Average CV: {unstable['cv'].mean():.2f}")
        
        if summary_text:
            st.markdown("\n".join(summary_text))
        else:
            st.info("Run analyses to see summary here.")

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
    
    if st.button("📄 Generate Full Report", type="primary", use_container_width=True):
        with st.spinner("Generating report..."):
            try:
                analyzer = st.session_state.analyzer
                
                # Generate report
                report_text = analyzer.generate_summary_report(
                    lift_by_month_group=st.session_state.lift_by_month_group,
                    top_bottom=st.session_state.top_bottom_filters,
                    unstable=st.session_state.unstable_patterns
                )
                
                st.success("✅ Report generated!")
                
                # Show report preview
                st.text_area("Report Preview", report_text, height=300)
                
                # Download button
                st.download_button(
                    label="📥 Download Report",
                    data=report_text,
                    file_name=f"kantar_analysis_summary_{datetime.now().strftime('%Y%m%d')}.txt",
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
            if 'LIFT_PERCENTAGE' in df.columns:
                st.metric("Average Lift", f"{df['LIFT_PERCENTAGE'].mean():.2f}%")
            else:
                st.metric("Average Lift", "N/A")
        with col3:
            if 'survey_month' in df.columns:
                st.metric("Survey Months", df['survey_month'].nunique())
            else:
                st.metric("Survey Months", "N/A")
        with col4:
            if 'GROUP_NAME' in df.columns:
                st.metric("Groups", df['GROUP_NAME'].nunique())
            else:
                st.metric("Groups", "N/A")

if __name__ == "__main__":
    main()

