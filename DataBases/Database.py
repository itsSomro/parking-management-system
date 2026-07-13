import sqlite3


class Database:
    def __init__(self):
        self.conn = sqlite3.connect("parking_data.db")
        self.cursor = self.conn.cursor()

    def setup_database(self):
        self.cursor.execute("""
           CREATE TABLE IF NOT EXISTS Master_Table (
              spot_id TEXT PRIMARY KEY ,
              floor_no INTEGER,
              v_type TEXT,
              spot_no INTEGER
           )
        """)

        self.cursor.execute("""
           CREATE TABLE IF NOT EXISTS Active_Parking (
              plate_no TEXT PRIMARY KEY,
              entry_time DATETIME DEFAULT CURRENT_TIMESTAMP,
              floor_no INTEGER,
              v_type TEXT,
              spot_no INTEGER)
        """)

        self.conn.commit()

