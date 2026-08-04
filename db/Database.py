import sqlite3
import os
import bcrypt
import pandas as pd


class Database:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, "parking_data.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
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
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
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


    def setup_admin_account(self):
        self.cursor.execute("""
            SELECT COUNT(*) 
            FROM users
            WHERE username = 'admin'
        """)
        admin_check = self.cursor.fetchone()[0]

        if admin_check == 0:
            raw_password = "admin123"
            hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())

            self.cursor.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            """, ('admin', hashed_password.decode('utf-8'), 'Admin'))

            self.conn.commit()
            return True #to tell admin acc has been generated

        return False #incase admin acc alr present


    def add_new_user(self, username, raw_password, role):
        try:
            hashed_password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())

            self.cursor.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            """, (username, hashed_password.decode('utf-8'), role))

            self.conn.commit()
            return True

        except sqlite3.IntegrityError:
            return False


    def verify_login(self, username, entered_password):
        self.cursor.execute("""
            SELECT password_hash, role
            FROM users
            WHERE username = ?
        """, (username,))

        user_data = self.cursor.fetchone()

        if user_data:
            stored_hash, role = user_data

            entered_bytes = entered_password.encode('utf-8')
            stored_bytes = stored_hash.encode('utf-8')

            if bcrypt.checkpw(entered_bytes, stored_bytes):
                return True, role

        return False, None


    def get_financial_history(self):
        query = """
            SELECT entry_time, fee
            FROM session_logs 
                """

        df = pd.read_sql_query(query, self.conn)

        if not df.empty:
            df['entry_time'] = pd.to_datetime(df['entry_time'])

        return df


    def get_current_rates(self):
        self.cursor.execute("""
            SELECT v_type, hourly_rate
            FROM billing_rates
        """)
        rates = self.cursor.fetchall()

        rate_dict = {'S': 0.0, 'C': 0.0, 'T': 0.0}

        for v_type, rate in rates:
            if v_type in rate_dict:
                rate_dict[v_type] = rate

        return rate_dict

    def get_all_users(self):
        self.cursor.execute("""
            SELECT user_id, username, role
            FROM users
            ORDER BY user_id ASC
        """)
        return [{"user_id": row[0], "username": row[1], "role": row[2]} for row in self.cursor.fetchall()]


    def delete_user(self, user_id):
        self.cursor.execute("""
            DELETE
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        self.conn.commit()

