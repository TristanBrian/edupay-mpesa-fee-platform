import sqlite3
import pandas as pd
import os
import sys

# Ensure Python can find seed_data.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from seed_data import seed_data 

DB_PATH = os.path.join(BASE_DIR, "flexifees.db")

def load_data():
    if not os.path.exists(DB_PATH):
        seed_data()

    conn = sqlite3.connect(DB_PATH)
    # ADDED: invoices.student_id to the SELECT statement
    query = """
    SELECT 
        invoices.id,
        invoices.student_id,
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
        seed_data()
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df