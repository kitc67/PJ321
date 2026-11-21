"""รันทั้งไปป์ไลน์: ingest -> transform -> publish

ใช้งาน: python run_pipeline.py
"""
import ingest
import transform
import publish


def main():
    ingest.main()
    transform.main()
    publish.main()
    print('[pipeline] เสร็จสิ้น')


if __name__ == '__main__':
    main()
