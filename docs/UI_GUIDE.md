# Kantar BLS Analysis - Web UI Guide

## Overview

The web UI provides an interactive interface for running Kantar BLS analysis without writing code. It's built with Streamlit, making it accessible to non-technical team members.

## Getting Started

### Installation

Make sure Streamlit is installed:
```bash
pip install -r requirements.txt
```

### Running the UI

**Option 1: From project root**
```bash
streamlit run scripts/app.py
```

**Option 2: Using the launcher**
```bash
python scripts/run_app.py
```

**Option 3: From scripts directory**
```bash
cd scripts
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

## Features

### 1. Home Page
- Overview of the tool's capabilities
- Current status of data loading and analysis
- Quick start guide

### 2. Data Loading
- View available files in the data directory
- Check which files are present/missing
- One-click data loading
- Summary of loaded data

### 3. Analysis
- Clean and merge data with one click
- Run different types of analysis:
  - Trend analysis
  - Significance detection
  - Pattern identification
- Configure analysis parameters
- Preview processed data

### 4. Results
- **Trends Tab**: View trend analysis results
- **Significant Results Tab**: Filter and explore statistically significant findings
- **Patterns Tab**: Channel consistency analysis
- **Signal vs Noise Tab**: Classification of reliable vs unreliable metrics
- Download results as CSV

### 5. Visualizations
- **Lift by Channel**: Bar chart of average lift by channel
- **Top Metrics**: Horizontal bar chart of top-performing metrics
- **Lift Heatmap**: Heatmap showing lift by metric and channel
- **Custom Analysis**: Build custom visualizations with filters

### 6. Reports
- Generate comprehensive reports
- Configure what to include
- Preview and download reports
- Quick statistics dashboard

## Usage Workflow

### Basic Workflow

1. **Start the app**
   ```bash
   streamlit run scripts/app.py
   ```

2. **Load Data** (Data Loading page)
   - Check file availability
   - Click "Load Data" button
   - Wait for confirmation

3. **Run Analysis** (Analysis page)
   - Click "Clean and Merge"
   - Select analysis options
   - Click "Run Analysis"
   - Wait for completion

4. **Explore Results** (Results page)
   - Browse different tabs
   - Filter and search
   - Download CSV files

5. **View Visualizations** (Visualizations page)
   - Select visualization type
   - Customize parameters
   - View charts

6. **Generate Reports** (Reports page)
   - Configure report options
   - Click "Generate Full Report"
   - Download report file

## Tips & Tricks

### Performance
- The app uses session state to cache data
- Reloading data is only needed when files change
- Analysis results are cached until you rerun

### Data Updates
- If you update CSV files, refresh the app or reload data
- The app automatically detects pre-merged files

### Customization
- Adjust visualization parameters using sliders and inputs
- Filter results using the search and filter options
- Export any table as CSV

### Troubleshooting

**App won't start**
- Make sure Streamlit is installed: `pip install streamlit`
- Check that you're in the correct directory

**Data not loading**
- Verify files are in the `data/` directory
- Check file names match expected names
- Look for error messages in the app

**Visualizations not showing**
- Make sure data is loaded and analysis is run
- Check that you have enough data for the visualization
- Try a different visualization type

## Advantages of the UI

### For Non-Technical Users
- ✅ No coding required
- ✅ Point-and-click interface
- ✅ Visual feedback at each step
- ✅ Easy to explore results

### For Technical Users
- ✅ Quick exploration without writing code
- ✅ Shareable with team members
- ✅ Can still use Python scripts for advanced analysis
- ✅ Good for demos and presentations

### For Teams
- ✅ Standardized analysis process
- ✅ Reproducible results
- ✅ Easy to share findings
- ✅ Can be deployed for wider access

## Deployment Options

### Local Use
- Run on your machine for personal use
- Access at `http://localhost:8501`

### Team Sharing
- Deploy to Streamlit Cloud (free)
- Deploy to internal server
- Share via network (if on same network)

### Production Deployment
- Streamlit Cloud (streamlit.io)
- Docker container
- Internal web server

## Next Steps

1. **Customize the UI**: Modify `scripts/app.py` to add features
2. **Deploy**: Set up for team access
3. **Integrate**: Connect to Snowflake for live data
4. **Extend**: Add new visualizations or analysis types

## Support

For issues or questions:
- Check the main README.md
- Review DESIGN_DOCUMENTATION.md
- Contact the Brand Measurement Team

