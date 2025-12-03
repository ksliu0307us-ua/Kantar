# Project Structure

This document describes the organization of the Kantar BLS analysis project.

## Directory Layout

```
kantar bls/
├── data/                          # Data files (CSV)
│   ├── bls_metrics.csv
│   ├── bls_answers.csv
│   ├── bls_metrics_with_filters.csv
│   ├── kantar_bls_filters.csv
│   ├── kantar_bls_filter_ids.csv
│   └── kantar_codebook_mapping_table*.csv
│
├── scripts/                        # Analysis scripts
│   ├── analyze.py                 # Main analysis module
│   ├── example_usage.py           # Example usage scripts
│   └── test.py                    # Test/exploratory scripts
│
├── output/                         # Generated reports and visualizations
│   └── (created automatically)
│
├── docs/                           # Documentation files
│   ├── Brand Measurement Framework [Ax 2025].docx
│   ├── LIFT API Insights - Quick Start.docx
│   ├── Wavemaker DoorDash Core LIFT 2025 Q2 Scorecard - 8.13.25.xlsx
│   └── kantar_data_architecture.xlsx
│
├── README.md                       # Main documentation
├── PROJECT_STRUCTURE.md            # This file
├── requirements.txt                # Python dependencies
└── .gitignore                      # Git ignore rules
```

## File Organization

### Data Directory (`data/`)

All CSV data files are stored here:

**Required Files:**
- **bls_metrics.csv**: Aggregate lift metrics
- **kantar_bls_filters.csv**: Filter metadata
- **kantar_bls_filter_ids.csv**: Filter-to-survey crosswalk
- **kantar_codebook_mapping_table*.csv**: Question code mappings

**Optional Files:**
- **bls_metrics_with_filters.csv**: Pre-merged metrics with filter data. If this file exists, the analyzer will automatically use it for faster processing (skips merge step).
- **bls_answers.csv**: User-level survey responses (optional, for detailed analysis)

### Scripts Directory (`scripts/`)

All Python analysis scripts:
- **analyze.py**: Main `KantarBLSAnalyzer` class with full analysis pipeline
- **example_usage.py**: Example scripts demonstrating different use cases
- **test.py**: Quick test/exploratory analysis scripts

### Output Directory (`output/`)

Generated files (created automatically):
- Analysis reports (`.txt`)
- Visualization charts (`.png`)
- Any other generated outputs

### Docs Directory (`docs/`)

Documentation and reference materials:
- Framework documents
- API documentation
- Data architecture files
- Scorecards and reports

## Path Resolution

The scripts use relative paths based on their location:

- Scripts in `scripts/` automatically look for data in `../data/`
- Output is written to `../output/` by default
- This allows scripts to work whether run from project root or scripts directory

## Usage

### Running from Project Root

```bash
python scripts/analyze.py
```

### Running from Scripts Directory

```bash
cd scripts
python analyze.py
```

Both approaches work because the scripts resolve paths relative to their own location.

## Notes

- If CSV files appear in the root directory, they are likely locked (open in Excel). 
  The scripts will use the copies in `data/` directory.
- The `output/` directory is created automatically if it doesn't exist.
- All scripts default to using `data/` for input and `output/` for results.

