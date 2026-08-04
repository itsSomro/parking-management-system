import math
from datetime import datetime
from core.ParkingSpot import ParkingSpot
from core.Vehicle import VehicleSize, Scooter, Car, Truck


class ParkingLot:
    def __init__(self, db_instance):
        self.db = db_instance
        self.cursor = self.db.cursor
        self.conn = self.db.conn


    def add_spots(self, floor, start, stop, v_type_str):
        new_spots = [(f"{floor}-{v_type_str}-{i}", floor, v_type_str, i)
                     for i in range(start, stop)]

        self.cursor.executemany("""
            INSERT OR IGNORE INTO lot_inventory (spot_id, floor_no, v_type, spot_no)
            VALUES (?,?,?,?)
        """, new_spots)

        self.conn.commit()
        # print(f"Successfully added {stop-start} {v_type_str} spots to floor {floor}")


    def remove_spots(self, floor, start, stop, v_type_str):
        spots_to_delete = [(f"{floor}-{v_type_str}-{i}",)
                     for i in range(start, stop)]

        self.cursor.executemany("""
            DELETE FROM lot_inventory WHERE spot_id = ?
        """, spots_to_delete)

        self.conn.commit()
        # print(f"Successfully removed {stop - start} {v_type_str} spots from floor {floor}")


    def find_spot(self, vehicle):
        v_type_letter = vehicle.get_type().value

        self.cursor.execute("""
            SELECT m.spot_id, m.floor_no
            FROM lot_inventory m
            LEFT JOIN active_sessions a
            ON m.spot_id = a.spot_id
            WHERE m.v_type = ? AND a.plate_no is NULL
            ORDER BY m.floor_no ASC, m.spot_no ASC
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
            FROM lot_inventory WHERE spot_id = ?
        """, (spot_id,))

        spot_data = self.cursor.fetchone()
        if spot_data is None:
            return None

        floor, vtype, spot_no = spot_data

        v_enum = VehicleSize(vtype)

        new_spot = ParkingSpot(spot_id, v_enum, floor)

        self.cursor.execute("""
            SELECT plate_no, entry_time
            FROM active_sessions
            WHERE spot_id = ?
        """, (spot_id,))

        active_data = self.cursor.fetchone()
        # print(f"\n[DEBUG] active_data fetchone result: {active_data}")

        if active_data:
            plate_num, time_of_entry = active_data

            if vtype == "S":
                vehicle = Scooter(plate_num)
            elif vtype == "C":
                vehicle = Car(plate_num)
            elif vtype == "T":
                vehicle = Truck(plate_num)

            db_time = datetime.strptime(time_of_entry, "%Y-%m-%d %H:%M:%S")
            # print(f"[DEBUG] Attempting to park {vehicle.license_plate} into {new_spot.get_id}")
            new_spot.park_vehicle(vehicle, historical_datetime=db_time)
            # print(f"[DEBUG] Is spot free after parking? {new_spot.is_free()}\n")

        return new_spot


    def configure_lot(self, floor_configs):
        # floor_configs - Accepts in a 2d dictionary format: For eg: {0 : {'S':20, 'C':20, 'T':10}, 1 : {'S':20, 'C':20}
        for floor, vehicle_counts in floor_configs.items():
            for v_type, count in vehicle_counts.items():
                if count > 0:
                    start = 1
                    stop = 1 + count

                    self.add_spots(floor, start, stop, v_type)


    def get_spot_by_plate(self, license_plate):
        self.cursor.execute("""
                            SELECT v_type, spot_id, entry_time
                            FROM active_sessions
                            WHERE plate_no = ?
                            """, (license_plate,))

        active_data = self.cursor.fetchone()
        if active_data is None:
            return None

        vtype, spot_id, time_of_entry = active_data
        floor = int(spot_id.split('-')[0])

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


    def log_vehicle_entry(self, vtype, spot_id, plate_no):
        self.cursor.execute("""
            INSERT INTO active_sessions (v_type, spot_id, plate_no, entry_time)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (vtype, spot_id, plate_no))
        self.conn.commit()


    def log_vehicle_exit(self, exit_time, spot_id, fee):
        self.cursor.execute("""
            SELECT plate_no, entry_time, v_type, spot_id
            FROM active_sessions
            WHERE spot_id = ?
        """, (spot_id,))

        active_data = self.cursor.fetchone()
        if active_data:
            plate_no, entry_time, v_type, spot_id = active_data

            self.cursor.execute("""
                INSERT INTO session_logs (plate_no, entry_time, exit_time, v_type, spot_id, fee) 
                VALUES (?,?, ?, ?, ?, ?)
            """, (plate_no, entry_time, exit_time, v_type, spot_id, fee))

            self.cursor.execute("""
                DELETE FROM active_sessions
                WHERE v_type = ? AND spot_id = ?
            """, (v_type, spot_id))
            self.conn.commit()
            return True

        else:
            return False


    def show_map(self):
        print("\n" + "=" * 40)
        print("~ PARKING LOT LAYOUT ~")
        print("=" * 40)

        self.cursor.execute("""
            SELECT m.floor_no, m.v_type, m.spot_no, a.plate_no
            FROM lot_inventory m
            LEFT JOIN active_sessions a
            ON m.spot_id = a.spot_id
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
            FROM lot_inventory
            GROUP BY v_type 
        """)
        total_counts = dict(self.cursor.fetchall())

        self.cursor.execute("""
            SELECT v_type, COUNT(*)
            FROM active_sessions
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
            FROM lot_inventory
        """)

        count = self.cursor.fetchone()
        return count[0] if count else 0


    def are_rates_configured(self):
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM billing_rates
        """)

        rate_count = self.cursor.fetchone()[0]
        return rate_count > 0


    def update_rates(self, rate_configs):
        # rate_configs - Accepts in a 1d dictionary format: For eg: {'S':5, 'C':10, 'T':20}
        for v_type, rate in rate_configs.items():
            self.cursor.execute("""
                                INSERT OR REPLACE INTO billing_rates (v_type, hourly_rate)
                                VALUES (?, ?)
                                """, (v_type, rate))
        self.conn.commit()


    def get_floor_layout(self):
        """
        Retrieves the current spot counts per floor and vehicle type.
        Returns a 2D dictionary format perfectly matched for the Web UI:
        e.g., {0: {'C': 10, 'S': 5, 'T': 2}, 1: {'C': 15, 'S': 0, 'T': 0}}
        """
        self.cursor.execute("""
            SELECT floor_no, v_type, COUNT(*)
            FROM lot_inventory
            GROUP BY floor_no, v_type
        """)

        layout = {}

        for floor, v_type, count in self.cursor.fetchall():
            if floor not in layout:
                layout[floor] = {'C': 0, 'S': 0, 'T': 0}

            if v_type in layout[floor]:
                layout[floor][v_type] = count

        return layout


    def update_lot_layout(self, new_floor_configs):
        """
        Accepts a 2D dictionary from the Web UI: {0: {'C': 15, 'S': 5, 'T': 5}, ...}
        Compares it to the current layout and automatically adds/removes spots to match.
        """
        current_layout = self.get_floor_layout()

        for floor_str, vehicle_counts in new_floor_configs.items():
            floor = int(floor_str)

            for v_type, new_count in vehicle_counts.items():
                current_count = current_layout.get(floor, {}).get(v_type, 0)

                # SCENARIO 1: We need to ADD spots
                if new_count > current_count:
                    start = current_count + 1
                    stop = new_count + 1

                    self.add_spots(floor, start, stop, v_type)

                # SCENARIO 2: We need to REMOVE spots
                elif new_count < current_count:
                    start = new_count + 1
                    stop = current_count + 1

                    self.remove_spots(floor, start, stop, v_type)

                # SCENARIO 3: new_count == current_count
                # No changes needed for this vehicle type on this floor, so it safely skips!


    def calculate_bill(self, start_time, vehicle_type):
        v_type = vehicle_type.get_type()
        v_type_str = v_type.value if hasattr(v_type, "value") else v_type

        end_time = datetime.utcnow()
        duration = end_time - start_time
        hours = duration.total_seconds() / 3600

        # Rounding up (charging for the whole hour)
        billable_hours = math.ceil(hours)

        self.cursor.execute("""
            SELECT v_type, hourly_rate
            FROM billing_rates
                WHERE v_type = ?
        """, (v_type_str,))

        rate_data = self.cursor.fetchone()
        if rate_data:
            rate = rate_data[1]
        else:
            print(f"Warning: No rate found for {v_type_str}. Defaulting to ₹10/hr")
            rate = 10

        # ~~~ DIFFERENT RATE METHODS ~~~
        # (Use ONLY one: Comment the rest)

        #1. BILLING PER HOUR BASIS
        # if vehicle_type == VehicleSize.SCOOTER:
        #     rate = 5
        # elif vehicle_type == VehicleSize.CAR:
        #     rate = 10
        # else:
        #     rate = 20

        return billable_hours * rate, billable_hours, duration, end_time

        #2. BILLING ONCE PER TYPE BASIS
        # if vehicle_type == VehicleSize.SCOOTER:
        #     rate = 20
        # elif vehicle_type == VehicleSize.CAR:
        #     rate = 30
        # else:
        #     rate = 50
        #
        # return rate, billable_hours, duration

        #3. BILLING DEFAULT + OVERTIME FEE BASIS
        # if vehicle_type == VehicleSize.SCOOTER:
        #     rate = 10           # Excess Time Payment Rate
        #     std_rate = 20       # Standard Bracket Payment
        # elif vehicle_type == VehicleSize.CAR:
        #     rate = 20
        #     std_rate = 30
        # else:
        #     rate = 40
        #     std_rate = 50
        #
        # std_time = 5     # Standard Bracket = 5 hours
        #
        # if billable_hours > std_time:
        #     excess_time = billable_hours - std_time
        #     return std_rate + (excess_time * rate), billable_hours, duration
        #
        # else:
        #     return std_rate, billable_hours, duration