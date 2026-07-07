import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "subscribers.db"))

def get_cloud_db_params():
    try:
        import psycopg2
    except ImportError:
        return None

    db_host = os.getenv("DB_HOST")
    if not db_host:
        supabase_url = os.getenv("SUPABASE_URL", "")
        if supabase_url and "supabase.co" in supabase_url:
            ref = supabase_url.replace("https://", "").replace("http://", "").split(".")[0]
            db_host = f"db.{ref}.supabase.co"
    
    db_pass = os.getenv("db_pass") or os.getenv("DB_PASSWORD") or os.getenv("DB_PASS")
    
    if db_host and db_pass:
        return {
            "host": db_host,
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER", "postgres"),
            "password": db_pass,
            "dbname": os.getenv("DB_NAME", "postgres"),
            "sslmode": "require"
        }
    return None

def create_connection():
    cloud_params = get_cloud_db_params()
    if cloud_params:
        try:
            import psycopg2
            conn = psycopg2.connect(**cloud_params)
            return conn, "postgres"
        except Exception as e:
            print(f"[WARNING] Could not connect to cloud database ({e}). Falling back to SQLite.")
    
    return sqlite3.connect(DB_PATH), "sqlite"

def create_table():
    conn, db_type = create_connection()
    cursor = conn.cursor()
    if db_type == "postgres":
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        # Automatically sync/migrate local SQLite subscribers to Supabase cloud if local DB exists
        if os.path.exists(DB_PATH):
            try:
                sqlite_conn = sqlite3.connect(DB_PATH)
                sqlite_cur = sqlite_conn.cursor()
                sqlite_cur.execute("SELECT email FROM subscribers")
                local_emails = [r[0] for r in sqlite_cur.fetchall()]
                sqlite_cur.close()
                sqlite_conn.close()
                
                for email in local_emails:
                    try:
                        cursor.execute("INSERT INTO subscribers (email) VALUES (%s) ON CONFLICT (email) DO NOTHING", (email,))
                    except Exception:
                        conn.rollback()
                conn.commit()
            except Exception as e:
                print(f"[INFO] Local SQLite sync note: {e}")
    else:
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
        conn, db_type = create_connection()
        cursor = conn.cursor()
        if db_type == "postgres":
            cursor.execute("INSERT INTO subscribers (email) VALUES (%s)", (email,))
        else:
            cursor.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        if "unique" in str(e).lower() or "integrity" in str(e).lower() or "duplicate" in str(e).lower():
            return False
        print("Database error:", e)
        return False

def get_all_subscribers():
    try:
        conn, db_type = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM subscribers")
        emails = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return emails
    except Exception as e:
        print("Database error:", e)
        return []

def get_active_db_info():
    cloud_params = get_cloud_db_params()
    if cloud_params:
        try:
            import psycopg2
            conn = psycopg2.connect(**cloud_params)
            conn.close()
            return {"type": "PostgreSQL (Supabase Cloud)", "host": cloud_params["host"], "status": "Connected"}
        except Exception as e:
            return {"type": "SQLite (Local Fallback)", "path": DB_PATH, "status": f"Cloud failed ({e})"}
    return {"type": "SQLite (Local)", "path": DB_PATH, "status": "Active"}

