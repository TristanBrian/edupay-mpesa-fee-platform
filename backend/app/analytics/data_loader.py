import sqlite3
import pandas as pd
import os
import sys

# Ensure Python can find seed_data.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from seed_data import seed_data  # now works because BASE_DIR is in sys.path

DB_PATH = os.path.join(BASE_DIR, "flexifees.db")

def load_data():
    if not os.path.exists(DB_PATH):
        seed_data()  # create DB if missing

    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        invoices.id,
        invoices.total_amount,
        invoices.paid_amount,
        invoices.balance,
        invoices.due_date,
        invoices.created_at,
        invoices.school_id,
        students.class_name
    FROM invoices
    LEFT JOIN students ON invoices.student_id = students.id
    """
    try:
        df = pd.read_sql_query(query, conn)
    except pd.io.sql.DatabaseError:
        # If table missing, seed DB
        seed_data()
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df