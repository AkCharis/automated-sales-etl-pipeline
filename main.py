from typing import Optional
from sqlalchemy import create_engine, text
from pathlib import Path

import logging
from src.automated_sales_etl_pipeline.extract import read_files_dict, check_valid_files
from src.automated_sales_etl_pipeline.transform import transform
from src.automated_sales_etl_pipeline.load import load
from src.automated_sales_etl_pipeline.utils.logger_config import setup_pipeline_logging


# 1. Instantiate the logger placeholder for this specific file
logger = logging.getLogger(__name__)

def run_pipeline(file_path: Optional[Path] = None) -> None:
    """Orchestrates the end-to-end Automated Sales ETL Pipeline workflow.

    Executes a multi-stage data processing pipeline:
    1. Extraction: Ingests single-file event data or scans the raw inbox directory.
    2. Schema Validation: Checks structural integrity, routes invalid files to 
       `data/rejected/`, and stages valid files into `data/valid/`.
    3. Transformation: Cleans, standardizes, deduplicates, and enriches valid records.
    4. Database Ingestion: Upserts transformed data into PostgreSQL target tables.

    Args:
        file_path (Optional[Path], optional): Explicit path to a single file 
            passed by a file watcher (e.g., Watchdog). If None, the pipeline runs 
            a batch scan across all files in `data/inbox`. Defaults to None.
    """
    # Initialize logging channels for terminal progress and file error tracking
    setup_pipeline_logging()
    
    logger.info("🚀 Pipeline startup initiated via main().")

    try:
        # Stage 1: Extraction & File Reading
        logger.info("🚀 Starting file extraction...")
        raw_dir = Path('data/inbox')
        files = read_files_dict(folder_path=raw_dir, file_path=file_path)

        # Stage 2: Schema Validation & Staging
        logger.info("🚀 Starting file validation...")
        valid_files = check_valid_files(files)

        # Halt processing gracefully if no valid datasets passed validation
        if not valid_files:
            logger.warning("❌ File failed validation check. Dropping from processing loop.")
            return
        
        # Stage 3: Cleaning & Data Transformation
        logger.info("🚀 Starting file cleaning...")
        cleaned_files = transform(valid_files)

        # Early exit check if cleaning produced no output records
        if not cleaned_files:
            logger.warning("❌ No cleaned files returned. Dropping from processing loop.")
            return
        
        # Stage 4: Database Loading & Upsert
        logger.info("🚀 Loading data into database...")
        load(cleaned_files)

    except Exception as e:
        # Capture unexpected pipeline crashes with complete stack trace logging
        logger.error("❌ Critical failure during main pipeline loop.")
        logger.exception(e)


if __name__ == "__main__":
    # Execute batch processing mode over all files currently sitting in inbox
    run_pipeline()