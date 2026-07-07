import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "subscribers.db"))

def create_connection():
    return sqlite3.connect(DB_PATH)

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def add_subscriber(email):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print("Database error:", e)
        return False

def get_all_subscribers():
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM subscribers")
        emails = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return emails
    except Exception as e:
        print("Database error:", e)
        return []
