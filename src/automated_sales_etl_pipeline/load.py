import os
import logging
from urllib.parse import quote_plus
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.automated_sales_etl_pipeline.utils.logger_config import setup_pipeline_logging

logger = logging.getLogger(__name__)
setup_pipeline_logging()

def load(df_dict: dict[str, pd.DataFrame]) -> None:
    """Loads transformed DataFrames into a PostgreSQL target table using an upsert strategy.

    Utilizes a temporary staging table (`stg_orders`) to stage incoming records 
    before executing an `INSERT ... ON CONFLICT (order_id) DO UPDATE` query against 
    the target `sales` table. This prevents duplicate key errors while keeping 
    records updated.

    Args:
        df_dict (dict[str, pd.DataFrame]): Dictionary mapping filenames to 
            cleaned, transformed DataFrames ready for database ingestion.

    Raises:
        KeyError: If required database environment variables are missing.
        Exception: Captures and logs database connection or execution failures.
    """
    # --------------------------------------------------------------------------
    # Step 1: Environment & Connection Initialization
    # --------------------------------------------------------------------------
    load_dotenv()

    # Retrieve database environment credentials with sensible defaults
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME')
    db_username = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')

    # Safely escape special characters in password for PostgreSQL connection URL
    escaped_password = quote_plus(db_password) if db_password else ""

    connection_url = (
        f"postgresql+psycopg2://{db_username}:{escaped_password}@"
        f"{db_host}:{db_port}/{db_name}"
    )

    # Instantiate database engine (reuses connection pool across files)
    engine = create_engine(connection_url, pool_pre_ping=True)

    # --------------------------------------------------------------------------
    # Step 2: Database Staging & Upsert Execution
    # --------------------------------------------------------------------------
    for filename, data in df_dict.items():
        if data.empty:
            logger.warning(f"Skipping database load for empty DataFrame: {filename}")
            continue

        try:
            # Open transactional database connection block (auto-commits on exit)
            with engine.begin() as conn:
                # 1. Load batch records into temporary staging table
                data.to_sql(
                    name='stg_orders', 
                    con=conn, 
                    if_exists='replace', 
                    index=False, 
                    method='multi'
                )
                upsert_query = """
                    INSERT INTO sales(order_id, customer_id, product_id, order_date, quantity, price, region, total_sales_amount, processed_at)
                    SELECT order_id, customer_id, product_id, order_date, quantity, price, region, total_sales_amount, processed_at FROM stg_orders
                    ON CONFLICT (order_id)
                    DO UPDATE SET 
                        quantity = EXCLUDED.quantity,
                        price = EXCLUDED.price,
                        total_sales_amount = EXCLUDED.total_sales_amount;
                    """

                conn.execute(text(upsert_query))
            logger.info(f"Successfully upserted data from file into 'sales' table: {filename}")

        except Exception as e:
            logger.error(f"Failed to load dataset '{filename}' into database: {e}")
            raise