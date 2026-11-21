"""ขั้นที่ 3: อ่าน raw_data -> ทำความสะอาด -> สรุปตาราง -> เขียนลง schema production

ฟังก์ชัน clean() และ build_tables() ไม่ต่อฐานข้อมูล จึงทดสอบจาก CSV ได้โดยตรง
"""
import numpy as np
import pandas as pd

import config

# ตารางที่จะเขียนลง production (ชื่อตาราง -> ชื่อ worksheet ใน publish.py)
PRODUCTION_TABLES = [
    'monthly_sales', 'product_sales', 'product_sales_no_bulk', 'country_sales',
    'customer_summary', 'monthly_cancellations', 'product_cancellations',
    'data_quality_log',
]


def clean(raw: pd.DataFrame):
    """คืนค่า (df_clean, quality_log)"""
    log = {'rows_raw': len(raw)}
    df = raw.copy()

    # 1) ตัดแถวซ้ำทั้งแถว
    dup = df.duplicated().sum()
    df = df.drop_duplicates().reset_index(drop=True)
    log['duplicate_rows_removed'] = int(dup)

    # 2) แปลงวันที่จากข้อความ M/D/YYYY
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
    log['invalid_dates'] = int(df['Date'].isna().sum())

    # 3) ธุรกรรมยกเลิก: TransactionNo ขึ้นต้นด้วย C (Quantity ติดลบทุกแถว)
    df['TransactionNo'] = df['TransactionNo'].astype(str).str.strip()
    df['Is_Cancellation'] = df['TransactionNo'].str.startswith('C')
    log['cancellation_rows'] = int(df['Is_Cancellation'].sum())

    # 4) CustomerNo ว่าง -> Unknown (ไม่ตัดแถว เพราะยังใช้ในยอดขายและสินค้าได้)
    log['customer_missing_rows'] = int(df['CustomerNo'].isna().sum())
    df['CustomerNo'] = (df['CustomerNo'].astype('Int64').astype(str)
                        .replace('<NA>', 'Unknown'))

    # 5) มูลค่า: ไม่มีสกุลเงินในไฟล์ จึงเรียกว่า Revenue โดยไม่ระบุสกุล
    df['Revenue'] = df['Price'] * df['Quantity']
    df['Year_Month'] = df['Date'].dt.to_period('M').astype(str)
    return df, log


def build_tables(df: pd.DataFrame, log: dict):
    sales = df[~df['Is_Cancellation']]
    canc = df[df['Is_Cancellation']]

    monthly = (sales.groupby('Year_Month')
               .agg(Revenue=('Revenue', 'sum'), Units=('Quantity', 'sum'),
                    Transactions=('TransactionNo', 'nunique'),
                    Days_With_Data=('Date', 'nunique'))
               .reset_index())
    monthly['Revenue_Per_Day'] = (monthly['Revenue'] / monthly['Days_With_Data']).round(2)
    monthly['Is_Partial_Month'] = (
        monthly['Days_With_Data'] < pd.PeriodIndex(monthly['Year_Month'], freq='M').days_in_month)

    product = (sales.groupby('ProductName')
               .agg(Revenue=('Revenue', 'sum'), Units=('Quantity', 'sum'))
               .reset_index().sort_values('Revenue', ascending=False))

    # สินค้าไม่รวมรายการสั่งซื้อขนาดใหญ่ (>= 10,000 หน่วย/แถว) เพื่อไม่ให้ตัวเลขบิดเบือน
    product_nb = (sales[sales['Quantity'] < 10_000].groupby('ProductName')
                  .agg(Revenue=('Revenue', 'sum'), Units=('Quantity', 'sum'))
                  .reset_index().sort_values('Revenue', ascending=False))

    country = (sales.groupby('Country')
               .agg(Revenue=('Revenue', 'sum'), Units=('Quantity', 'sum'),
                    Customers=('CustomerNo', 'nunique'))
               .reset_index().sort_values('Revenue', ascending=False))

    known = sales[sales['CustomerNo'] != 'Unknown']
    cust = (known.groupby('CustomerNo')
            .agg(Revenue=('Revenue', 'sum'), Orders=('TransactionNo', 'nunique'),
                 Units=('Quantity', 'sum'), Country=('Country', 'first'))
            .reset_index().sort_values('Revenue', ascending=False))
    cust['Is_Repeat'] = cust['Orders'] >= 2

    cancel_m = (canc.groupby('Year_Month')
                .agg(Cancel_Lines=('TransactionNo', 'size'),
                     Cancel_Transactions=('TransactionNo', 'nunique'),
                     Cancel_Units=('Quantity', lambda s: int(-s.sum())),
                     Cancel_Value=('Revenue', lambda s: float(-s.sum())))
                .reset_index())

    cancel_p = (canc.groupby('ProductName')
                .agg(Cancel_Units=('Quantity', lambda s: int(-s.sum())),
                     Cancel_Value=('Revenue', lambda s: float(-s.sum())))
                .reset_index().sort_values('Cancel_Value', ascending=False))

    log.update({
        'rows_after_dedupe': len(df),
        'rows_sales': len(sales),
        'rows_cancellation': len(canc),
        'total_transactions': int(df['TransactionNo'].nunique()),
        'cancelled_transactions': int(canc['TransactionNo'].nunique()),
        'bulk_lines_qty_ge_10000': int((sales['Quantity'] >= 10000).sum()),
    })
    quality = pd.DataFrame(list(log.items()), columns=['Check', 'Value'])
    quality['Value'] = quality['Value'].astype(str)

    return {
        'monthly_sales': monthly,
        'product_sales': product,
        'product_sales_no_bulk': product_nb,
        'country_sales': country,
        'customer_summary': cust,
        'monthly_cancellations': cancel_m,
        'product_cancellations': cancel_p,
        'data_quality_log': quality,
    }


def write_production(tables: dict, engine):
    for name, frame in tables.items():
        frame.to_sql(name, engine, schema='production', if_exists='replace', index=False)
        print(f'[transform] production.{name}: {len(frame):,} rows')


def main():
    from sqlalchemy import create_engine
    engine = create_engine(config.DB_URL)
    raw = pd.read_sql_table(config.RAW_TABLE, engine, schema='raw_data')
    df, log = clean(raw)
    tables = build_tables(df, log)
    write_production(tables, engine)


if __name__ == '__main__':
    main()
