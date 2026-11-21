"""ขั้นที่ 2: โหลด CSV ดิบเข้า PostgreSQL schema raw_data"""
import pandas as pd
from sqlalchemy import create_engine

import config


def main():
    engine = create_engine(config.DB_URL)
    # อ่านรหัสเป็นข้อความทั้งหมดเพื่อไม่ให้ข้อมูลเสียรูป (เช่น 0 นำหน้า, ตัวอักษร C)
    df = pd.read_csv(config.CSV_PATH, dtype={'TransactionNo': str, 'ProductNo': str})
    df.to_sql(config.RAW_TABLE, engine, schema='raw_data', if_exists='replace',
              index=False, chunksize=10_000)
    print(f'[ingest] loaded {len(df):,} rows into raw_data.{config.RAW_TABLE}')


if __name__ == '__main__':
    main()
