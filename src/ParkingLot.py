from datetime import datetime
from shapely.speedups import available
from ParkingSpot import ParkingSpot
from Vehicle import VehicleSize, Scooter, Car, Truck
import sqlite3


class ParkingLot:
    def __init__(self, db_instance):
        self.db = db_instance
        self.cursor = self.db.cursor
        self.conn = self.db.conn

    def add_spots(self, floor, start, stop, v_type_enum, v_type_str):
        new_spots = [(f"{floor}-{v_type_str}-{i}", floor, v_type_str, i)
                     for i in range(start, stop)]

        self.cursor.executemany("""
            INSERT OR IGNORE INTO Master_Table (spot_id, floor_no, v_type, spot_no)
            VALUES (?,?,?,?)
        """, new_spots)

        self.conn.commit()
        # print(f"Successfully added {stop-start} {v_type_str} spots to floor {floor}")


    def remove_spots(self, floor, start, stop, v_type_enum, v_type_str):
        spots_to_delete = [(f"{floor}-{v_type_str}-{i}",)
                     for i in range(start, stop)]

        self.cursor.executemany("""
            DELETE FROM Master_Table WHERE spot_id = ?
        """, spots_to_delete)

        self.conn.commit()
        # print(f"Successfully removed {stop - start} {v_type_str} spots from floor {floor}")

    def find_spot(self, vehicle):
        v_type_letter = vehicle.get_type().value

        self.cursor.execute("""
            SELECT m.spot_id, m.floor_no
            FROM Master_Table m
            LEFT JOIN Active_Parking a
            ON m.floor_no = a.floor_no AND m.v_type = a.v_type AND m.spot_no = a.spot_no
            WHERE m.v_type = ? AND a.plate_no is NULL
            LIMIT 1
        """, (v_type_letter,))

        available_spot = self.cursor.fetchone()

        if available_spot:
            spot_id, floor = available_spot
            return ParkingSpot(spot_id, vehicle.get_type(), floor)

        return None

    def get_spot_by_id(self, spot_id):
        self.cursor.execute("""
            SELECT floor_no, v_type, spot_no
            FROM Master_Table WHERE spot_id = ?
        """, (spot_id,))

        spot_data = self.cursor.fetchone()
        if spot_data is None:
            return None

        floor, vtype, spot_no = spot_data

        v_enum = VehicleSize(vtype)

        new_spot = ParkingSpot(spot_id, v_enum, floor)

        self.cursor.execute("""
            SELECT plate_no, entry_time
            FROM Active_Parking
            WHERE floor_no = ? AND v_type = ? AND spot_no = ?
        """, (floor, vtype, spot_no))

        active_data = self.cursor.fetchone()

        if active_data:
            plate_num, time_of_entry = active_data

            if vtype == "S":
                vehicle = Scooter(plate_num)
            elif vtype == "C":
                vehicle = Car(plate_num)
            elif vtype == "T":
                vehicle = Truck(plate_num)

            db_time = datetime.strptime(time_of_entry, "%Y-%m-%d %H:%M:%S")
            new_spot.park_vehicle(vehicle, historical_datetime=db_time)

        return new_spot


    def initialize_parking_lot(self):
        for i in range(1, 6):
            self.add_spot(ParkingSpot(f"S-{i}", VehicleSize.SCOOTER))

        for i in range(1, 11):
            self.add_spot(ParkingSpot(f"C-{i}", VehicleSize.CAR))

        for i in range(1, 6):
            self.add_spot(ParkingSpot(f"T-{i}", VehicleSize.TRUCK))


    def get_spot_by_plate(self, license_plate):
        self.cursor.execute("""
            SELECT floor_no, v_type, spot_no, entry_time 
            FROM Active_Parking 
            WHERE plate_no = ?
        """, (license_plate,))

        active_data = self.cursor.fetchone()
        if active_data is None:
            return None

        floor, vtype, spot_no, time_of_entry = active_data
        spot_id = f"{floor}-{vtype}-{spot_no}"

        v_enum = VehicleSize(vtype)
        if vtype == "S":
            vehicle = Scooter(license_plate)
        elif vtype == "C":
            vehicle = Car(license_plate)
        elif vtype == "T":
            vehicle = Truck(license_plate)

        new_spot = ParkingSpot(spot_id, v_enum, floor)
        db_time = datetime.strptime(time_of_entry, "%Y-%m-%d %H:%M:%S")
        new_spot.park_vehicle(vehicle, historical_datetime=db_time)

        return new_spot


    def log_vehicle_entry(self, floor, vtype, spot_no, plate_no):
        self.cursor.execute("""
            INSERT INTO Active_Parking (floor_no, v_type, spot_no, plate_no, entry_time)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (floor, vtype, spot_no, plate_no))
        self.conn.commit()


    def log_vehicle_exit(self, floor, vtype, spot_no):
        self.cursor.execute("""
            DELETE FROM Active_Parking
            WHERE floor_no = ? AND v_type = ? AND spot_no = ?
        """, (floor, vtype, spot_no))
        self.conn.commit()


    def show_map(self):
        print("\n" + "=" * 40)
        print("~ PARKING LOT LAYOUT ~")
        print("=" * 40)

        self.cursor.execute("""
            SELECT m.floor_no, m.v_type, m.spot_no, a.plate_no
            FROM Master_Table m
            LEFT JOIN Active_Parking a
            ON m.floor_no == a.floor_no AND m.v_type == a.v_type AND m.spot_no == a.spot_no
            ORDER BY m.floor_no, m.v_type, m.spot_no
        """)

        all_spots = self.cursor.fetchall()

        floors = {}
        # Floor-wise View
        for floor, vtype, spot_no, plate in all_spots:
            if floor not in floors:
                floors[floor] = []

            spot_name = f"{vtype}-{spot_no}"
            if plate is None:
                # Free: Green Text
                colored_spot = f"\033[92m[ {spot_name:^5} ]\033[0m"
            else:
                # Occupied: Red Text
                colored_spot = f"\033[91m[ {spot_name:^5} ]\033[0m"

            floors[floor].append(colored_spot)

        for floor, spots in floors.items():
            print(f"\nFloor {floor}:")
            # Replacing last no. gies u x spots per line in terminal (default 5)
            for i in range(0, len(spots), 5):
                print(" ".join(spots[i:i+5]))

        print("\n" + "="*40)


    def get_stats(self):
        self.cursor.execute("""
            SELECT v_type, COUNT(*)
            FROM Master_Table
            GROUP BY v_type 
        """)
        total_counts = dict(self.cursor.fetchall())

        self.cursor.execute("""
            SELECT v_type, COUNT(*)
            FROM Active_Parking
            GROUP BY v_type 
        """)
        occupied_counts = dict(self.cursor.fetchall())

        stats = {}
        for v_type in ['S','C','T']:
            total = total_counts.get(v_type, 0)
            occupied = occupied_counts.get(v_type, 0)
            free = total - occupied
            stats[v_type] = (free,total)

        return stats


    def get_total_spots_count(self):
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM Master_Table
        """)

        count = self.cursor.fetchone()
        return count[0] if count else 0


