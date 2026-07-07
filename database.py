import sqlite3
import os
import requests
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

def get_supabase_rest_config():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY") or os.getenv("SUPABASE_KEY")
    if url and key:
        return url.rstrip("/"), key
    return None, None

def create_connection():
    # Tier 1: Direct TCP PostgreSQL Connection (psycopg2)
    cloud_params = get_cloud_db_params()
    if cloud_params:
        try:
            import psycopg2
            conn = psycopg2.connect(**cloud_params)
            return conn, "postgres"
        except Exception as e:
            # Check if failure is due to IPv6 routing / network unreachable
            print(f"[INFO] Direct TCP Postgres connection failed ({e}). Checking HTTPS REST API fallback...")
    
    # Tier 2: Supabase HTTPS REST API (Port 443 - Works across all IPv4/IPv6 networks)
    rest_url, rest_key = get_supabase_rest_config()
    if rest_url and rest_key:
        try:
            endpoint = f"{rest_url}/rest/v1/subscribers?select=email"
            headers = {"apikey": rest_key, "Authorization": f"Bearer {rest_key}"}
            res = requests.get(endpoint, headers=headers, timeout=5)
            if res.status_code == 200:
                print("[SUCCESS] Connected to Supabase Cloud Database via HTTPS REST API (IPv4/IPv6 compatible).")
                return (rest_url, rest_key), "rest"
        except Exception as e:
            print(f"[WARNING] HTTPS REST API fallback failed ({e}).")

    # Tier 3: Local SQLite Fallback
    print("[INFO] Using local SQLite database fallback.")
    return sqlite3.connect(DB_PATH), "sqlite"

def create_table():
    conn, db_type = create_connection()
    
    if db_type == "postgres":
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        # Automatically sync local SQLite subscribers to Supabase cloud if local DB exists
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
        cursor.close()
        conn.close()
        
    elif db_type == "rest":
        rest_url, rest_key = conn
        # Sync local SQLite subscribers over REST API
        if os.path.exists(DB_PATH):
            try:
                sqlite_conn = sqlite3.connect(DB_PATH)
                sqlite_cur = sqlite_conn.cursor()
                sqlite_cur.execute("SELECT email FROM subscribers")
                local_emails = [r[0] for r in sqlite_cur.fetchall()]
                sqlite_cur.close()
                sqlite_conn.close()
                
                endpoint = f"{rest_url}/rest/v1/subscribers"
                headers = {
                    "apikey": rest_key,
                    "Authorization": f"Bearer {rest_key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                }
                for email in local_emails:
                    try:
                        requests.post(endpoint, json={"email": email}, headers=headers, timeout=5)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[INFO] Local SQLite REST sync note: {e}")
                
    else:
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
        conn, db_type = create_connection()
        if db_type == "postgres":
            cursor = conn.cursor()
            cursor.execute("INSERT INTO subscribers (email) VALUES (%s)", (email,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        elif db_type == "rest":
            rest_url, rest_key = conn
            endpoint = f"{rest_url}/rest/v1/subscribers"
            headers = {
                "apikey": rest_key,
                "Authorization": f"Bearer {rest_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal"
            }
            res = requests.post(endpoint, json={"email": email}, headers=headers, timeout=10)
            if res.status_code in (200, 201, 204):
                return True
            elif res.status_code == 409 or "duplicate" in res.text.lower() or "unique" in res.text.lower():
                return False
            else:
                print(f"[WARNING] Supabase REST error ({res.status_code}): {res.text}")
                return False
                
        else:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
    except Exception as e:
        if "unique" in str(e).lower() or "integrity" in str(e).lower() or "duplicate" in str(e).lower() or "409" in str(e):
            return False
        print("Database error:", e)
        return False

def get_all_subscribers():
    try:
        conn, db_type = create_connection()
        if db_type == "postgres":
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM subscribers")
            emails = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return emails
            
        elif db_type == "rest":
            rest_url, rest_key = conn
            endpoint = f"{rest_url}/rest/v1/subscribers?select=email"
            headers = {"apikey": rest_key, "Authorization": f"Bearer {rest_key}"}
            res = requests.get(endpoint, headers=headers, timeout=10)
            if res.status_code == 200:
                return [row["email"] for row in res.json() if "email" in row]
            else:
                print(f"[WARNING] REST fetch error: {res.status_code} - {res.text}")
                return []
                
        else:
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
            return {"type": "PostgreSQL (Supabase Cloud - TCP)", "host": cloud_params["host"], "status": "Connected via TCP (Port 5432)"}
        except Exception as e:
            # Check HTTPS REST API
            rest_url, rest_key = get_supabase_rest_config()
            if rest_url and rest_key:
                try:
                    endpoint = f"{rest_url}/rest/v1/subscribers?select=email"
                    headers = {"apikey": rest_key, "Authorization": f"Bearer {rest_key}"}
                    res = requests.get(endpoint, headers=headers, timeout=5)
                    if res.status_code == 200:
                        return {"type": "PostgreSQL (Supabase Cloud - HTTPS API)", "host": rest_url, "status": "Connected via HTTPS (Port 443 - IPv4/IPv6 compatible)"}
                except Exception:
                    pass
            return {"type": "SQLite (Local Fallback)", "path": DB_PATH, "status": f"Cloud failed ({e})"}
            
    rest_url, rest_key = get_supabase_rest_config()
    if rest_url and rest_key:
        try:
            endpoint = f"{rest_url}/rest/v1/subscribers?select=email"
            headers = {"apikey": rest_key, "Authorization": f"Bearer {rest_key}"}
            res = requests.get(endpoint, headers=headers, timeout=5)
            if res.status_code == 200:
                return {"type": "PostgreSQL (Supabase Cloud - HTTPS API)", "host": rest_url, "status": "Connected via HTTPS (Port 443 - IPv4/IPv6 compatible)"}
        except Exception:
            pass
            
    return {"type": "SQLite (Local)", "path": DB_PATH, "status": "Active"}


