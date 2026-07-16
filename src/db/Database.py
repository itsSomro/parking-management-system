import sqlite3
import os

class Database:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, "parking_data.db")
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("PRAGMA foreign_keys = ON;")

    def setup_database(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lot_inventory (
                spot_id TEXT PRIMARY KEY ,
                floor_no INTEGER,
                v_type TEXT,
                spot_no INTEGER
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_sessions (
                plate_no TEXT PRIMARY KEY,
                entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                v_type TEXT,
                spot_id TEXT REFERENCES lot_inventory(spot_id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_no TEXT,
                entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                exit_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                v_type TEXT,
                spot_id TEXT REFERENCES lot_inventory(spot_id),
                fee REAL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                role TEXT
            )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS billing_rates (
            rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
            v_type TEXT UNIQUE,
            hourly_rate REAL
            )
        """)

        self.conn.commit()

    def drop_old_tables(self):
        tables_to_drop = [
            'Master_Table', 'Active_Parking', 'Log_Table',  # old names
        ]

        for table in tables_to_drop:
            self.cursor.execute(f"DROP TABLE IF EXISTS {table}")

        self.conn.commit()
