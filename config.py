"""อ่านค่าตั้งค่าจากไฟล์ .env หรือ environment variables"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv  # ไม่บังคับ: ติดตั้ง python-dotenv ถ้าต้องการ
    load_dotenv(Path(__file__).with_name('.env'))
except ImportError:
    pass

PG_USER = os.getenv('PG_USER', 'kaggle')
PG_PASSWORD = os.getenv('PG_PASSWORD', 'kaggle_pw')
PG_DB = os.getenv('PG_DB', 'kaggle_dw')
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = os.getenv('PG_PORT', '5432')
CSV_PATH = os.getenv('CSV_PATH', 'data/sales_transaction_v4a.csv')
RAW_TABLE = os.getenv('RAW_TABLE', 'sales_transaction_v4a')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', '')
CREDENTIALS_FILE = os.getenv('CREDENTIALS_FILE', 'credentials.json')

DB_URL = f'postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}'
