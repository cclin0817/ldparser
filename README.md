# DEF/LEF Parser and Quality Checker

A comprehensive Python framework for parsing and validating DEF (Design Exchange Format) and LEF (Library Exchange Format) files used in IC design.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
  - [Step 1: Parse DEF Files](#step-1-parse-def-files)
  - [Step 2: Parse LEF Files](#step-2-parse-lef-files)
  - [Step 3: Run Quality Checks](#step-3-run-quality-checks)
- [Quality Checker Features](#quality-checker-features)
- [Command Line Usage](#command-line-usage)
- [API Usage](#api-usage)
- [File Structure](#file-structure)
- [Contributing](#contributing)

## Features

### DEF/LEF Parsing
- **DEF Parser**: Parses design files including components, nets, pins, and placement information
- **LEF Parser**: Extracts cell library information including pin definitions and directions
- **Pickle Support**: Saves parsed data for fast reloading and analysis

### Quality Control Framework
- **DEF File Structure Validation**: Checks for proper section delimiters (COMPONENTS/END COMPONENTS, NETS/END NETS)
- **DEF Unit Tests**: Component and net validation with detailed error reporting
- **LEF Unit Tests**: Cell structure and pin definition validation
- **Integration Tests**: Cross-validation between DEF and LEF data
- **Comprehensive Reporting**: Hierarchical severity levels (ERROR, WARNING, INFO)

## Installation

### Prerequisites
- Python 3.7+
- Conda environment (recommended)

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd def_lef_py

# Activate conda environment
conda activate def_lef_parser

# Install dependencies (if needed)
pip install loguru tqdm
```

## Quick Start

### Complete Workflow Example
```bash
# Parse DEF file and save to pickle
python def_parser.py --def_path test_data/complete.5.8.def --output_dir ./tmp

# Parse LEF file and save to pickle
python lef_parser.py --lef_path test_data/complete.5.8.lef --output_dir ./tmp

# Run the qc
python -m src.qc.qc --def_pickle ./tmp/def_outputs.pkl --lef_pickle ./tmp/lef_outputs.pkl --def_file ./test_data/complete.5.8.def --lef_file ./test_data/complete.5.8.lef


```

## Usage Guide

### Step 1: Parse DEF Files

#### Command Line
```bash
# Parse DEF file and save to pickle
python def_parser.py --def_path test_data/complete.5.8.def --output_dir ./tmp
```

#### Python API
```python
from def_parser import DefParser

# Configure parser
Header_list = {"VERSION", "DESIGN", "UNITS DISTANCE MICRONS", ...}
WithEndBlockList = {"COMPONENTS", "NETS", "PINS", ...}
NoEndBlockList = {"DIEAREA", "ROW", "TRACKS", ...}
used_prefix = ['COMPONENTS', 'NETS']

# Parse DEF file
parser = DefParser(def_path, Header_list, NoEndBlockList, WithEndBlockList, used_prefix)
def_content = parser.parse()

print(f"Found {len(def_content['components'])} components")
print(f"Found {len(def_content['nets'])} nets")
```

### Step 2: Parse LEF Files

#### Command Line
```bash
# Parse LEF file and save to pickle
python lef_parser.py --lef_path test_data/complete.5.8.lef --output_dir ./tmp
```

#### Python API
```python
from lef_parser import get_cell_dict

# Parse LEF file
cell_dict = get_cell_dict(lef_path)
print(f"Found {len(cell_dict)} cells in LEF library")

# Access cell information
for cell_name, cell_data in cell_dict.items():
    print(f"Cell: {cell_name}")
    if 'pins' in cell_data:
        print(f"  Pins: {list(cell_data['pins'].keys())}")
```

### Step 3: Run Quality Checks

#### Option A: Direct Command Line (Recommended)
```bash
# Run quality check on existing pickle files
python -m src.qc.qc --def_pickle ./tmp/def_outputs.pkl --lef_pickle ./tmp/lef_outputs.pkl --output_report ./tmp/qc_report.txt

# With custom paths
python -m src.qc.qc --def_pickle /path/to/your/def_outputs.pkl --lef_pickle /path/to/your/lef_outputs.pkl
```

#### Option B: Complete Demo Workflow
```bash
# Parse files and run quality check in one step
python qc_demo.py --def_path test_data/complete.5.8.def --lef_path test_data/complete.5.8.lef

# Skip parsing if pickle files already exist
python qc_demo.py --skip_parsing --output_dir ./tmp
```

#### Option C: Python API
```python
from src.qc import QualityController
import pickle

# Load parsed data
with open('./tmp/def_outputs.pkl', 'rb') as f:
    def_data = pickle.load(f)
with open('./tmp/lef_outputs.pkl', 'rb') as f:
    lef_data = pickle.load(f)

# Run quality checks
qc = QualityController()
report = qc.run_full_quality_check(def_data, lef_data, def_file_path="test_data/complete.5.8.def")

# Print summary
qc.print_report_summary(report)
qc.save_report_to_file(report, "quality_report.txt")
```

## Quality Checker Features

### Test Categories

#### DEF File Structure Tests ✅
- **Section Delimiters**: Validates COMPONENTS/END COMPONENTS, NETS/END NETS
- **Count Declarations**: Checks declared vs actual counts (e.g., "COMPONENTS 13 ;")
- **Section Integrity**: Ensures proper opening and closing of all sections

#### DEF Unit Tests ✅
- **Components Validation**: Existence, count, structure, duplicates
- **Nets Validation**: Existence, count, connections, dangling nets
- **Placement Information**: Instance placement and orientation checks

#### LEF Unit Tests ✅
- **Cell Structure**: Validates cell dictionary and definitions
- **Cell Uniqueness**: Ensures no duplicate cell definitions
- **Pin Validation**: Checks pin directions and definitions

#### Integration Tests ✅
- **Instance Mapping**: All net instances exist in components
- **Pin Cross-Reference**: All instance pins exist in LEF definitions
- **Cell Type Consistency**: All DEF cell types are defined in LEF

### Severity Levels
- **ERROR**: Critical issues that must be fixed
- **WARNING**: Issues that should be reviewed
- **INFO**: Informational messages and statistics

### Sample Output
```
================================================================================
QUALITY CHECK REPORT SUMMARY
================================================================================

Total Issues: 45
Summary by Severity:
  ERROR: 3
  WARNING: 12
  INFO: 30

Issues by Category:
  FILE_STRUCTURE: 8 issues
  COMPONENTS: 15 issues
  NETS: 10 issues
  INTEGRATION: 12 issues

ERRORS (3):
----------------------------------------
  [FILE_STRUCTURE] Section COMPONENTS declares 43 items
  [INTEGRATION] Cell type CHK3A used in DEF but not found in LEF
  [NETS] Duplicate net name: SCAN
```


## File Structure

```
def_lef_py/
├── README.md                 # This file
├── QC_README.md             # Detailed QC framework documentation
├── qc_demo.py               # Complete workflow demonstration
├── def_parser.py            # DEF file parser
├── lef_parser.py            # LEF file parser
├── test_data/               # Sample DEF/LEF files
│   ├── complete.5.8.def
│   └── complete.5.8.lef
├── src/
│   ├── qc/                  # Quality control framework
│   │   ├── __init__.py
│   │   ├── models.py        # Data structures
│   │   ├── def_checker.py   # DEF validation
│   │   ├── lef_checker.py   # LEF validation
│   │   ├── integration_checker.py  # Cross-validation
│   │   └── qc.py           # Main controller
│   └── parser/             # Parser utilities
└── tmp/                    # Output directory
    ├── def_outputs.pkl     # Parsed DEF data
    ├── lef_outputs.pkl     # Parsed LEF data
    └── qc_report.txt       # Quality check report
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## License

[Add your license information here]

---

For detailed quality checker documentation, see [QC_README.md](QC_README.md). 