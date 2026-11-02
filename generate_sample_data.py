from pathlib import Path

# Create directory if it doesn't exist
inbox_dir = Path("data/inbox")
inbox_dir.mkdir(parents=True, exist_ok=True)

files = {
    "branch_north.csv": """order_id,customer_id,product_id,order_date,quantity,price,region
1001,CUST_001,PROD_A,2026-10-10,2,29.99,North
1002,CUST_002,PROD_B,2026-10-11,1,150.00,North
1003,CUST_003,PROD_A,2026-10-11,5,29.99,North
1004,CUST_004,PROD_C,2026-10-12,3,12.50,North
1005,CUST_005,PROD_D,2026-10-13,1,89.99,North""",

    "branch_south.csv": """order_id,customer_id,product_id,order_date,quantity,price,region
1006, CUST_006 ,PROD_B,10/14/2026,1,150.00,South
1007,CUST_007,PROD_C,2026/10/14,4,12.50,South
1008,CUST_008,PROD_A,15-Oct-2026,2,29.99,South
1009,CUST_009,PROD_D,2026-10-15 14:30:00,1,89.99,South
1010,CUST_010,PROD_E,2026-10-16,10,5.00,South""",

    "branch_east.csv": """order_id,customer_id,product_id,order_date,quantity,price,region
1011,CUST_011,PROD_A,2026-10-12,2,29.99,East
1012,CUST_012,PROD_B,2026-10-13,,150.00,East
1013,CUST_013,PROD_C,2026-10-13,1,N/A,East
1014,CUST_014,PROD_D,2026-10-14,3,$89.99,East
1015,,PROD_A,2026-10-15,1,29.99,East""",

    "branch_west.csv": """order_id,customer_id,product_id,order_date,quantity,price,region
1016,CUST_015,PROD_A,2026-10-15,1,29.99,West
1016,CUST_015,PROD_A,2026-10-15,1,29.99,West
1017,CUST_016,PROD_C,2026-10-15,2,12.50,West
1018,CUST_017,PROD_B,2026-10-16,1,150.00,West
1018,CUST_017,PROD_B,2026-10-16,1,150.00,West""",

    "branch_central_invalid.csv": """order_id,customer_id,product_id,order_date,quantity,region
1019,CUST_018,PROD_A,2026-10-16,2,Central
1020,CUST_019,PROD_B,2026-10-16,1,Central
1021,CUST_020,PROD_C,2026-10-16,5,Central"""
}

for filename, content in files.items():
    file_path = inbox_dir / filename
    file_path.write_text(content)
    print(f"Created: {file_path}")