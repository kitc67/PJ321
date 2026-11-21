"""ขั้นที่ 4: อ่าน schema production จาก PostgreSQL แล้วเขียนลง Google Sheets

ใช้ gspread เชื่อมต่อ Google Sheets (ต้องมี credentials.json จาก Service Account)
แต่ละตารางจะเขียนลงคนละ worksheet และล้างข้อมูลเดิมก่อนเขียนทับ
"""
import pandas as pd
import gspread
from sqlalchemy import create_engine, inspect

import config
from transform import PRODUCTION_TABLES

CELL_LIMIT_PER_SHEET = 10_000_000  # ขีดจำกัดรวมของ Google Sheets ต่อไฟล์


def df_to_worksheet(spreadsheet, title, frame: pd.DataFrame):
    values = [frame.columns.tolist()] + frame.astype(object).where(frame.notna(), '').values.tolist()
    cells = len(values) * len(values[0])
    if cells > CELL_LIMIT_PER_SHEET:
        raise ValueError(f'{title}: {cells:,} cells เกินขีดจำกัด')
    try:
        ws = spreadsheet.worksheet(title)
        ws.clear()
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=len(values), cols=len(values[0]))
    ws.resize(rows=len(values), cols=len(values[0]))
    ws.update(values=values, range_name='A1', value_input_option='RAW')
    print(f'[publish] {title}: {len(frame):,} rows -> worksheet "{title}"')


def main():
    if (not config.SPREADSHEET_ID or config.SPREADSHEET_ID.startswith('your_')
            or not config.SPREADSHEET_ID.isascii()):
        raise SystemExit('ยังไม่ได้ตั้งค่า SPREADSHEET_ID ใน .env')
    engine = create_engine(config.DB_URL)
    available = set(inspect(engine).get_table_names(schema='production'))
    gc = gspread.service_account(filename=config.CREDENTIALS_FILE)
    spreadsheet = gc.open_by_key(config.SPREADSHEET_ID)

    for name in PRODUCTION_TABLES:
        if name not in available:
            raise SystemExit(f'ไม่พบ production.{name} ให้รัน transform ก่อน')
        frame = pd.read_sql_table(name, engine, schema='production')
        df_to_worksheet(spreadsheet, name, frame)


if __name__ == '__main__':
    main()
