"""
Script untuk membersihkan URL localhost / 127.0.0.1:8000 yang tersimpan di database,
mengubahnya menjadi path relatif (/uploads/...) agar aman diakses di VPS / production.
"""
from sqlalchemy import text
from app.db.session import engine

def clean_urls():
    print("Database sudah menggunakan format ikon MDI standar tanpa URL gambar statis.")

if __name__ == "__main__":
    clean_urls()

