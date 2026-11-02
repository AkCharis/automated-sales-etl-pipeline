import pandas as pd
from pathlib import Path
import logging
from pandas.api.types import is_numeric_dtype, is_object_dtype
from src.automated_sales_etl_pipeline.utils.logger_config import setup_pipeline_logging

logger = logging.getLogger(__name__)
setup_pipeline_logging()

import pandas as pd
from pathlib import Path

def load_single_df(path: Path) -> pd.DataFrame:
    """Helper function to load a single tabular file into a Pandas DataFrame.

    Supports CSV (`.csv`) and Excel (`.xlsx`, `.xls`) file formats. Standardizes
    common missing value representations (e.g., 'N/A', 'null', '-') into NaN.

    Args:
        path (Path): Pathlib path pointing to the file to be ingested.

    Returns:
        pd.DataFrame: Loaded dataset as a Pandas DataFrame.

    Raises:
        ValueError: If the file extension is not supported by the ingestion rules.
        FileNotFoundError: If the specified file path does not exist.
    """
    ext = path.suffix.lower()

    # Define standard missing value representations across file formats
    missing_value_formats = ["N/A", "None", "-", "null"]
    
    # Ingest standard CSV files
    if ext == '.csv':
        return pd.read_csv(path, na_values=missing_value_formats)

    # Ingest Excel files (.xlsx, .xls)
    elif ext in ['.xlsx', '.xls']:
        return pd.read_excel(path, na_values=missing_value_formats)
    
    raise ValueError(f"Unsupported file type: {ext}")


def read_files_dict(folder_path: Path, file_path: Path = None) -> dict[str, pd.DataFrame]:
    """Ingests tabular daily sales files into a dictionary mapping filenames to DataFrames.

    Operates in two modes:
    1. Single File Ingestion: Triggered when `file_path` is supplied by an automated event 
       listener (e.g., Watchdog). Reads and returns only that file.
    2. Batch Directory Scan: Triggered when `file_path` is None (e.g., manual batch execution). 
       Iterates over all valid files in `folder_path`.

    Args:
        folder_path (Path): Base directory containing incoming files (e.g., `data/inbox`).
        file_path (Optional[Path], optional): Specific file path passed by file monitors. 
            Defaults to None.

    Returns:
        dict[str, pd.DataFrame]: Dictionary where keys are filenames (e.g., 'branch_north.csv') 
            and values are the corresponding loaded DataFrames.
    """
    valid_extensions = {'.csv', '.xlsx', '.xls'}

    # Case 1: Monitor / Event Listener Ingestion (Single File Execution)
    if file_path:
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            logger.info(f"Ingesting single file event: {file_path.name}")
            return {file_path.name: load_single_df(file_path)}
        
        logger.warning(f"File skipped (invalid format or missing): {file_path}")
        return {}

    # Case 2: Batch Execution / Folder Scan
    data_dict = {}
    
    for path in folder_path.iterdir():
        # Skip directories, non-files, and unsupported file extensions
        if path.is_file() and path.suffix.lower() in valid_extensions:
            try:
                data_dict[path.name] = load_single_df(path)
                logger.info(f"Successfully read file into memory: {path.name}")
            except Exception as e:
                # Capture bad reads without stopping the rest of the batch scan
                logger.error(f"Failed to read file '{path.name}': {e}")

    return data_dict


def check_valid_files(df_dict: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Validates schema structure and data types for a collection of DataFrames.

    Iterates through a dictionary of ingested DataFrames, validating required column 
    presence and basic data type compatibility. Valid files are exported to `data/valid/` 
    and returned in a dictionary, while invalid files are routed to `data/rejected/` 
    with rejection notes logged.

    Args:
        df_dict (dict[str, pd.DataFrame]): Dictionary mapping filenames to raw Pandas DataFrames.

    Returns:
        dict[str, pd.DataFrame]: Dictionary containing only the DataFrames that passed all schema validation checks.
    """
    # Define expected columns and target Pandas data types
    expected_schema = pd.Series({
    'order_id': 'Int64',
    'customer_id': 'object',
    'product_id': 'object',
    'order_date': 'object',
    'quantity': 'Int64',
    'price': 'float64',
    'region': 'object',
    })

    valid = {}

    # Initialize staging directories for pipeline routing
    rejected_dir = Path("data/rejected")
    rejected_dir.mkdir(parents=True, exist_ok=True)

    # Initialize staging directory for valid files
    valid_dir = Path("data/valid")
    valid_dir.mkdir(parents=True, exist_ok=True)

    
    for filename, data in df_dict.items():
        # Step 1: Column Schema Validation
        if set(data.columns) != set(expected_schema.index):
            missing_cols = expected_schema.index.difference(data.columns).tolist()
            extra_cols = data.columns.difference(expected_schema.index).tolist()
            
            reasons = []
            if missing_cols:
                reasons.append(f"missing columns {missing_cols}")
            if extra_cols:
                reasons.append(f"unexpected extra columns {extra_cols}")

            # Route invalid file to rejected directory and skip further processing    
            log_bad_file(filename, data, " and ".join(reasons), rejected_dir)
            logger.info(f'Logged invalid file: {filename}')
            continue 

        # Step 2: Column Data Type Compatibility Validation
        invalid_cols = []
        for col, expected_type in expected_schema.items():
            actual_dtype = data[col].dtype
                
            # Allow integer columns to accept float64 (handles NaN/missing value coercion)
            if expected_type in ['int64', 'Int64', 'float64']:
                if not is_numeric_dtype(actual_dtype):
                    invalid_cols.append(f"{col} (got {actual_dtype}, expected numeric)")
                
            # Expect object/string types
            elif expected_type == 'object':
                if not is_object_dtype(actual_dtype):
                    invalid_cols.append(f"{col} (got {actual_dtype}, expected text/object)")

        # Step 3: File Routing & Staging
        if invalid_cols:
            reason = f"Invalid Column types for: {', '.join(invalid_cols)}"
            log_bad_file(filename, data, reason, rejected_dir)
            logger.info(f'Logged invalid file {filename}')
        else:
            valid[f'{filename}'] = data
            logger.info(f'Validated file {filename}')
            log_valid_file(filename, data, valid_dir)

    return valid


def log_bad_file(filename: str, df: pd.DataFrame, reason: str, output_dir: Path) -> None:
    """Exports an invalid DataFrame to the rejected directory with a rejection reason column.

    Args:
        filename (str): Target filename to export (e.g., 'branch_central.csv').
        df (pd.DataFrame): The failing DataFrame.
        reason (str): Description of why schema validation failed.
        output_dir (Path): Directory path where the rejected file will be saved.
    """
    filepath = output_dir/filename

    # Append 'reason' column using assign() to avoid mutating the original DataFrame in-place
    rejected_df = df.assign(reason=reason)
    rejected_df.to_csv(filepath, index=False)


def log_valid_file(filename, df, output_dir):
    """Exports a validated DataFrame to the valid staging directory prior to transformation.

    Args:
        filename (str): Target filename to export (e.g., 'branch_north.csv').
        df (pd.DataFrame): The validated DataFrame.
        output_dir (Path): Directory path where the valid file will be staged.
    """
    filepath = output_dir / filename
    df.to_csv(filepath, index=False)