import logging
from pathlib import Path


def setup_pipeline_logging() -> logging.Logger:
    """Configures and initializes dual-stream logging for the ETL pipeline.

    Sets up a root logger with two distinct outputs:
    1. Console Handler (stdout): Streamlines live execution status (`DEBUG` level and above)
       with a clean, timestamped format for interactive terminal monitoring.
    2. File Handler (`logs/pipeline_errors.log`): Exclusively captures failures (`ERROR` 
       and `CRITICAL` levels) with detailed context (filename, line number, logger name) 
       for deep debugging.

    Side Effects:
        - Creates a `logs/` directory in the current working directory if it does not exist.
        - Clears any pre-existing handlers on the root logger to avoid duplicated log lines.

    Returns:
        logging.Logger: A configured package-specific logger instance named 
            `"automated_sales_etl_pipeline"`.
    """
    # Step 1: Directory Initialization
    # Ensure target directory exists for output error logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Step 2: Root Logger Setup & Handler Reset
    # Retrieve the root logger and set verbosity threshold to lowest level
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture everything at the root level
    
    # Clear any pre-existing default handlers to prevent duplicate output records
    if logger.hasHandlers():
        logger.handlers.clear()

    # Step 3: Handler Creation
    # Console Handler: Streams live execution updates directly to stdout/stderr
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Show DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # File Handler: Appends persistent records specifically for errors
    error_file_handler = logging.FileHandler(log_dir / "pipeline_errors.log", mode="a")
    error_file_handler.setLevel(logging.ERROR)  # Show ONLY ERROR and CRITICAL

    # Step 4: Output Formatting
    # Clean and lightweight formatter optimized for terminal viewing
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s: %(message)s", 
        datefmt="%H:%M:%S"
    )
    
    # Detailed formatter with line numbers and scope for production debugging
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s [Line: %(lineno)d] - %(message)s"
    )

    # Bind respective formatters to individual handlers
    console_handler.setFormatter(console_formatter)
    error_file_handler.setFormatter(file_formatter)

    # Step 5: Handler Attachment & Package Scope Return
    # Register configured handlers back to the root logger
    logger.addHandler(console_handler)
    logger.addHandler(error_file_handler)

    # Return package-scoped logger instance for application-wide consistency
    return logging.getLogger("automated_sales_etl_pipeline")