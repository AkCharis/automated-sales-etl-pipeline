import pandas as pd
from typing import Any
import logging
from src.automated_sales_etl_pipeline.utils.logger_config import setup_pipeline_logging

logger = logging.getLogger(__name__)
setup_pipeline_logging()

def transform(df_dict: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Cleans, standardizes, and enriches validated sales DataFrames.

    Performs the following ETL transformation steps:
    1. Currency Cleaning: Strips symbols ('$', ',') and coercively converts `price` to float.
    2. Date Normalization: Converts `order_date` using flexible date parsing and removes time components.
    3. Missing Data Handling: Drops rows missing key identifiers (`order_id`, `customer_id`, 
       `product_id`, `order_date`) and imputes defaults for optional fields (`quantity`, `price`, `region`).
    4. Deduplication: Drops duplicate orders based on `order_id`.
    5. String Formatting: Strips leading/trailing whitespace from string fields.
    6. Feature Engineering: Computes `total_sales_amount` and appends a `processed_at` execution timestamp.

    Args:
        df_dict (dict[str, pd.DataFrame]): Dictionary mapping filenames to 
            pre-validated Pandas DataFrames (e.g., from the `check_valid_files` output).

    Returns:
        dict[str, pd.DataFrame]: Dictionary mapping filenames to fully transformed and 
            cleaned DataFrames ready for database loading.
    """
    # Default values for optional fields missing values
    default_imputations: dict[str, Any] = {
        'quantity': 1,
        'price': 0.0,
        'region': 'Unknown'
    }

    transformed_dict: dict[str, pd.DataFrame] = {}

    for filename, raw_data in df_dict.items():
        # Operate on an explicit copy to prevent modifying input data
        data = raw_data.copy()

        # Step 1: Numeric Currency Cleaning
        # Convert to string to safely strip '$' and ',' symbols, then coerce unparseable rows to NaN
        data['price'] = (
            data['price']
            .astype(str)
            .str.replace('$', '', regex=False)
            .str.replace(',', '', regex=False)
        )
        data['price'] = pd.to_numeric(data['price'], errors='coerce')

        # Step 2: Date Parsing & Standardization
        # Parse mixed date formats and strip timestamp components (normalize to YYYY-MM-DD 00:00:00)
        data['order_date'] = pd.to_datetime(
            data['order_date'], 
            format='mixed', 
            errors='coerce'
        ).dt.normalize()

        # Step 3: Critical Identifier Validation & Missing Data Imputation
        # Drop rows missing primary keys or essential attributes
        data = data.dropna(subset=['order_id', 'customer_id', 'product_id', 'order_date'])

        # Remove duplicate orders and fill remaining NaN values in optional columns
        data = (
            data.drop_duplicates(subset=['order_id'])
            .fillna(default_imputations)
            .reset_index(drop=True)
        )

        # Step 4: String Normalization
        data['customer_id'] = data['customer_id'].astype(str).str.strip()
        data['product_id'] = data['product_id'].astype(str).str.strip()

        # Step 5: Feature Engineering & Derived Fields
        data['total_sales_amount'] = data['quantity'] * data['price']
        data['processed_at'] = pd.Timestamp.now()

        # Save transformed DataFrame to output collection
        transformed_dict[filename] = data
        logger.info(f"Successfully cleaned and transformed dataset: {filename}")

    return transformed_dict