# backend/seed_data.py
import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "flexifees.db")

def seed_data():
    """Create tables and insert sample students and invoices."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Create tables if they don't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT
    )
    """)

    # UPDATED: Added invoice_number column to the schema definition
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        invoice_number TEXT NOT NULL, 
        total_amount REAL,
        paid_amount REAL,
        balance REAL,
        school_id INTEGER,
        created_at TEXT,
        due_date TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    # 2. Insert sample students
    cursor.execute("INSERT OR IGNORE INTO students (id, class_name) VALUES (1, 'Grade 10')")
    cursor.execute("INSERT OR IGNORE INTO students (id, class_name) VALUES (2, 'Grade 11')")

    # 3. Insert sample invoices only if table empty
    cursor.execute("SELECT COUNT(*) FROM invoices")
    if cursor.fetchone()[0] == 0:
        now = datetime.now()
        
        # Row 1: Partial payment
        cursor.execute("""
        INSERT INTO invoices (student_id, total_amount, paid_amount, balance, school_id, created_at, due_date, invoice_number)
        VALUES (1, 10000, 8000, 2000, 1, ?, ?, ?)
        """, (now.isoformat(), (now + timedelta(days=30)).isoformat(), "INV-2026-001"))

        # Row 2: Fully paid
        cursor.execute("""
        INSERT INTO invoices (student_id, total_amount, paid_amount, balance, school_id, created_at, due_date, invoice_number)
        VALUES (2, 15000, 15000, 0, 2, ?, ?, ?)
        """, (now.isoformat(), (now + timedelta(days=30)).isoformat(), "INV-2026-002"))

    conn.commit()
    conn.close()
    print("✅ Sample data inserted successfully.")

if __name__ == "__main__":
    seed_data()