# Multi-Branch Automated Sales ETL Pipeline

An automated, event-driven Extract, Transform, Load (ETL) pipeline built with Python, Pandas, PostgreSQL, and Watchdog. This system monitors an incoming directory for daily branch sales files (`.csv` and `.xlsx`), validates schema integrity, cleans and transforms dirty records, and loads normalized data into a PostgreSQL database while logging execution metrics and handling bad files.

---

## Architecture & Data Flow

```
               ┌──────────────────────────┐
               │    data/inbox/ Folder    │
               └────────────┬─────────────┘
                            │ (New File Event)
                            ▼
               ┌──────────────────────────┐
               │  Watchdog File Listener  │
               │       (monitor.py)       │
               └────────────┬─────────────┘
                            │
                            ▼
               ┌──────────────────────────┐
               │    Schema Validation     │
               └──────┬─────────────┬─────┘
           [Valid]    │             │    [Invalid]
                      ▼             ▼
   ┌────────────────────┐         ┌──────────────────────────┐
   │    data/valid/     │         │      data/rejected/      │
   │ (Validated Files)  │         └──────────────────────────┘
   └──────────┬─────────┘
              │
              ▼
   ┌────────────────────┐
   │Cleaning & Transform│
   └──────────┬─────────┘
              │
              ▼
   ┌────────────────────┐
   │  PostgreSQL Load   │
   └────────────────────┘
```

* Watchdog Event Handler: Continuously monitors data/inbox/ for new sales files.

* Extraction & Schema Validation: Verifies required columns and structure. Invalid files are logged and routed to data/rejected/.

* Data Transformation: Deduplicates rows, standardizes dates (YYYY-MM-DD), strips whitespace, cleans currency fields, and computes total revenue.

* Database Ingestion: Appends cleaned data to the PostgreSQL database using SQLAlchemy.

* Archiving & Logging: Moves successfully processed files to data/valid/ and records errors or events via utils/logger_config.py.


## Tech Stack

* Language & Package Management: Python (managed via uv / pyproject.toml)

* Data Manipulation: Pandas, OpenPyXL

* Database & ORM: PostgreSQL, SQLAlchemy, psycopg2

* File Monitoring: Watchdog

* Environment Configuration: python-dotenv


## Project Structure
```
automated-sales-etl-pipeline/
│
├── data/
│   ├── inbox/         # Drop incoming CSV/Excel files here
│   ├── rejected/      # Schema/validation failure records
│   └── valid/         # Successfully ingested files
│
├── logs/
│   └── pipeline_errors.log  # Error logs and execution metrics
│
├── src/
│   └── automated_sales_etl_pipeline/
│       ├── utils/
│       │   └── logger_config.py # Logging configuration
│       ├── __init__.py
│       ├── extract.py           # Ingestion & schema validation
│       ├── load.py              # PostgreSQL load operations
│       └── transform.py         # Data cleaning & transformation
│
├── .env                         # Environment variables (database credentials)
├── .env.example
├── .gitignore
├── .python-version
├── main.py                      # Manual batch processing entry point
├── monitor.py                   # File watcher script (Watchdog listener)
├── pyproject.toml               # Project dependencies and configuration
├── generate_sample_data.py      # Sample data generation script
├── README.md                    # Project documentation
└── uv.lock                      # Lockfile for reproducible builds
```

## Getting Started

### Prerequisites

* Python 3.10 or higher

* PostgreSQL installed and running locally or hosted remotely

### Installation & Environment Setup

Set up a virtual environment and install dependencies defined in pyproject.toml:

**Using uv (Recommended):**

Automatically creates .venv and syncs dependencies from pyproject.toml
`uv sync`

**Using standard Python venv & pip:**
```
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

### Generating Test Data

To create random CSV datasets (clean, dirty, and invalid schema files) inside data/inbox/:
```
uv run generate_sample_data.py
```

### Running Automated File Listener

Start `monitor.py` to continuously listen for new files landing in data/inbox/:

```
uv run monitor.py
```

### Running Batch Ingestion Manually
To execute a single batch run over all files currently sitting in data/inbox/:

```
uv run main.py
```

## Validation & Transformation Rules
1. Schema Validation: Verifies existence of required columns (order_id, customer_id, product_id, order_date, quantity, price, region).

2. Pre-Processing Staging: Confirmed valid files are logged into data/valid/ before running transformations.

3. Data Cleaning: Strips whitespace from identifiers, removes currency symbols, standardizes date formats, and casts data types cleanly.

4. Deduplication: Drops duplicate records across order and product keys.

5. Derived Fields: Calculates total_amount = quantity * price and appends processed_at timestamp.

6. Metrics & Audit: All error stack traces and rejection reasons are captured in logs/pipeline_errors.log.


## Sample Execution Log

```
[00:20:43] INFO    : 👀 Watchdog active. Monitoring directory: 'C:\Users\admin\Documents\PROJECTS\automated-sales-etl-pipeline\data\inbox'
[00:20:43] INFO    : 📥 New valid file detected: branch_west.csv
[00:20:43] INFO    : ⚙️ Triggering ETL pipeline execution for branch_west.csv...
[00:20:43] INFO    : 🚀 Pipeline startup initiated via main().
[00:20:43] INFO    : 🚀 Starting file extraction...
[00:20:43] INFO    : 🚀 Starting file validation...
[00:20:43] INFO    : Validated file branch_west.csv
[00:20:43] INFO    : 🚀 Starting file cleaning...
[00:20:43] INFO    : Successfully cleaned branch_west.csv
[00:20:43] INFO    : 🚀 Loading data into database...
[00:20:43] INFO    : Successfully loaded branch_west.csv
[00:20:43] INFO    : ✅ Pipeline execution completed successfully.
```