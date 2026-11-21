# Kaggle Data Pipeline: E-commerce Sales Transaction

ไปป์ไลน์ข้อมูลอัตโนมัติแบบครบวงจรบนเครื่องของตัวเอง ตั้งแต่ไฟล์ CSV จาก Kaggle ไปจนถึง Dashboard บน Looker Studio

- **ชุดข้อมูล:** [E-commerce Business Transaction](https://www.kaggle.com/) (ไฟล์ `Sales Transaction v.4a.csv`) ธุรกรรมขายสินค้าของร้านออนไลน์ในสหราชอาณาจักร 1 ธ.ค. 2018 ถึง 9 ธ.ค. 2019 จำนวน 536,350 แถว
- **ผู้จัดทำ:** นายมนัญชัย กิจฉลอง รหัสนักศึกษา 1670903101
- **Dashboard:** `[ใส่ลิงก์ Looker Studio ที่ตั้งแชร์เป็น Anyone with the link can view]`

## สถาปัตยกรรม

```
Kaggle CSV
    │  ingest.py   (pandas, sqlalchemy)
    ▼
PostgreSQL (Docker)  schema raw_data
    │  transform.py   (pandas)
    ▼
PostgreSQL (Docker)  schema production
    │  publish.py   (gspread)
    ▼
Google Sheets
    │
    ▼
Looker Studio Dashboard
```

สั่งงานทั้งหมดด้วยคำสั่งเดียว: `python run_pipeline.py`

## โครงสร้างโปรเจกต์

```
docker-compose.yml   PostgreSQL 16 บน Docker (มี healthcheck)
sql/init.sql         สร้าง schema raw_data และ production
config.py            อ่านค่าตั้งค่าจาก .env
ingest.py            โหลด CSV เข้า raw_data
transform.py         ทำความสะอาดและสรุปข้อมูลเข้า production
publish.py           ส่งตาราง production ขึ้น Google Sheets
run_pipeline.py      รัน ingest -> transform -> publish
requirements.txt     แพ็กเกจ Python
.env.example         ตัวอย่างค่าตั้งค่า
data/                วางไฟล์ CSV ที่นี่ (ไม่ถูก commit)
```

## สิ่งที่ต้องมีก่อน

- Python 3.10 ขึ้นไป
- Docker Desktop (หรือ Docker Engine พร้อม Docker Compose v2)
- บัญชี Google และไฟล์ CSV จาก Kaggle

## วิธีรัน

**1. วางไฟล์ข้อมูล** ดาวน์โหลด `Sales Transaction v.4a.csv` จาก Kaggle (แตก zip ถ้ามี) แล้ววางที่ `data/sales_transaction_v4a.csv` โดยสร้างโฟลเดอร์ `data` เองและเปลี่ยนชื่อไฟล์ให้ตรง

**2. ตั้งค่า `.env`** คัดลอกไฟล์ตัวอย่าง แล้วแก้ `SPREADSHEET_ID`

```bash
cp .env.example .env          # Windows: copy .env.example .env
```

`SPREADSHEET_ID` คือส่วนระหว่าง `/d/` กับ `/edit` ใน URL ของ Google Sheets

**3. ตั้งค่า Google Credentials**

1. สร้างโปรเจกต์ใน [Google Cloud Console](https://console.cloud.google.com)
2. เปิดใช้ **Google Sheets API** และ **Google Drive API** (APIs & Services → Library)
3. สร้าง **Service Account** (IAM & Admin → Service Accounts) แล้วสร้าง JSON key ที่แท็บ Keys
4. บันทึกไฟล์เป็น `credentials.json` ไว้ในโฟลเดอร์โปรเจกต์
5. สร้าง Google Sheets ใหม่ แล้วแชร์ให้อีเมล `client_email` ในไฟล์ `credentials.json` ด้วยสิทธิ์ **Editor**

> **ห้าม commit `credentials.json` และ `.env`** ทั้งสองไฟล์ถูกใส่ไว้ใน `.gitignore` แล้ว ถ้า key หลุดให้ลบแล้วสร้างใหม่ทันที

**4. เริ่ม PostgreSQL**

```bash
docker compose up -d --wait
```

**5. ติดตั้งแพ็กเกจ Python**

```bash
pip install -r requirements.txt
```

**6. รันไปป์ไลน์** (รันจากโฟลเดอร์โปรเจกต์เสมอ เพราะ path ของ CSV เป็นแบบ relative)

```bash
python run_pipeline.py
```

ผลลัพธ์ที่ควรเห็นคือ `[ingest]`, `[transform]` และ `[publish]` ตามลำดับ จบด้วย `[pipeline] เสร็จสิ้น` จากนั้นจะมี worksheet ใหม่ 8 แผ่นใน Google Sheets ซึ่งรันซ้ำได้ทุกครั้ง เพราะ ingest ใช้ replace และ publish ล้างข้อมูลเดิมก่อนเขียนทับ

ถ้าจะรันทีละขั้น: `python ingest.py`, `python transform.py`, `python publish.py`

## ตารางใน schema production

| ตาราง | เนื้อหา | ใช้ตอบคำถาม |
|---|---|---|
| `monthly_sales` | ยอดขาย หน่วย ธุรกรรม วันที่มีข้อมูล `Revenue_Per_Day` และ `Is_Partial_Month` | ข้อ 1 |
| `product_sales` | ยอดขายและจำนวนหน่วยรายสินค้า | ข้อ 2 |
| `product_sales_no_bulk` | เหมือน `product_sales` แต่ไม่รวมแถวที่ Quantity ≥ 10,000 | ข้อ 2 |
| `country_sales` | ยอดขาย หน่วย และจำนวนลูกค้ารายประเทศ | ข้อ 3 |
| `monthly_cancellations` | ธุรกรรม หน่วย และมูลค่าที่ยกเลิกรายเดือน | ข้อ 4 |
| `product_cancellations` | หน่วยและมูลค่าที่ยกเลิกรายสินค้า | ข้อ 4 |
| `customer_summary` | ยอดขาย จำนวนครั้งที่ซื้อ และสถานะซื้อซ้ำรายลูกค้า | ข้อ 5 |
| `data_quality_log` | ผลตรวจคุณภาพข้อมูลระหว่าง transform | - |

## คำถามทางธุรกิจ

1. ยอดขายรายเดือนมีแนวโน้มอย่างไร และเดือนไหนสูงหรือต่ำ
2. สินค้า 10 อันดับแรกที่ทำรายได้สูงสุดคืออะไร และตรงกับสินค้าที่ขายได้จำนวนชิ้นมากสุดหรือไม่
3. นอกจากสหราชอาณาจักร ประเทศไหนสร้างรายได้สูงสุด
4. อัตราการยกเลิกสินค้าและเดือนไหนถูกยกเลิกมากที่สุด
5. ลูกค้ากลุ่มไหนซื้อบ่อยและมีมูลค่าสูง ควรได้รับโปรโมชันหรือการดูแลพิเศษ

## การจัดการข้อมูล (สรุป)

- ตัดแถวซ้ำทั้งแถว 5,200 แถว
- แปลง `Date` จากข้อความรูปแบบ M/D/YYYY เป็นวันที่
- ระบุธุรกรรมยกเลิกจาก `TransactionNo` ที่ขึ้นต้นด้วย `C` แล้วแยกออกจากยอดขาย
- `CustomerNo` ที่ว่าง 55 แถวระบุเป็น `Unknown` และยังคงอยู่ในยอดขายและสินค้า
- `Revenue = Price × Quantity` ไฟล์ไม่ระบุสกุลเงิน จึงไม่ระบุสกุลในผลลัพธ์
- สรุปข้อมูลก่อนส่งขึ้น Google Sheets เพื่อไม่ให้เกินขีดจำกัดจำนวน cell

## ข้อจำกัดของข้อมูล

- ไม่มีข้อมูลสกุลเงิน
- เดือน ธ.ค. 2019 มีข้อมูลเพียง 8 วัน จึงไม่ควรเทียบกับเดือนเต็มโดยตรง (ใช้ `Revenue_Per_Day` แทน)
- ข้อมูลเอียงไปที่สหราชอาณาจักร (ประมาณ 90.4% ของแถว)
- คำสั่งซื้อขนาดใหญ่ 3 รายการมีผลต่อการจัดอันดับสินค้าและลูกค้ามาก
- ไม่มีข้อมูลเวลาในการสั่งซื้อ จึงวิเคราะห์รายชั่วโมงไม่ได้

## แก้ปัญหาที่พบบ่อย

| อาการ | วิธีแก้ |
|---|---|
| `ModuleNotFoundError: No module named 'sqlalchemy'` | รัน `pip install -r requirements.txt` (หรือ `python -m pip install -r requirements.txt`) |
| `FileNotFoundError: data/sales_transaction_v4a.csv` | เช็กชื่อและตำแหน่งไฟล์ และรันจากโฟลเดอร์โปรเจกต์ บน Windows ระวังชื่อซ้อน `.csv.csv` |
| `connection refused` | Postgres ยังไม่พร้อม ตรวจด้วย `docker compose ps` ว่า `healthy` และเปิด Docker Desktop อยู่ |
| พอร์ต 5432 ถูกใช้อยู่แล้ว | ตั้ง `PG_PORT=5433` ใน `.env` แล้วรัน `docker compose up -d --wait` ใหม่ |
| แก้ `sql/init.sql` แล้วไม่มีผล | ไฟล์นี้รันตอนสร้าง volume ครั้งแรกเท่านั้น รัน `docker compose down -v` แล้วเริ่มใหม่ (ข้อมูลใน DB จะถูกลบ) |
| `403 The caller does not have permission` | ยังไม่ได้แชร์ Google Sheets ให้ `client_email` ด้วยสิทธิ์ Editor หรือ `SPREADSHEET_ID` ผิด หรือยังไม่ได้เปิด Sheets API / Drive API |
| `SPREADSHEET_ID` ยังเป็นค่าตัวอย่าง | แก้ในไฟล์ `.env` (ไม่ใช่ `.env.example`) |

หยุดฐานข้อมูล: `docker compose down` (เก็บข้อมูลไว้) หรือ `docker compose down -v` (ลบข้อมูลด้วย)

## ลิงก์

- Dashboard: `[ใส่ลิงก์ Looker Studio]`
- รายงานโปรเจกต์: `[ใส่ลิงก์หรือชื่อไฟล์]`
