import time
from datetime import datetime

from core.ParkingLot import ParkingLot
from core.Vehicle import Scooter, Truck, Car, VehicleSize
from db.Database import Database


def create_vehicle_instance(v_type, v_plate):
    vehicle = None
    match v_type:
        case 'S':
            vehicle = Scooter(v_plate)
        case 'C':
            vehicle = Car(v_plate)
        case 'T':
            vehicle = Truck(v_plate)
        case _:
            print("Invalid Vehicle Type Selected!")
            return None
    return vehicle


class OperatorTerminal:
    parking_lot = None

    def __init__(self):
        db = Database()
        OperatorTerminal.parking_lot = ParkingLot(db)


    def operator_dashboard(self):
        # Pressing 0 returns Admin to Admin Menu but logs out if user is Operator
        while True:
            stats = self.parking_lot.get_stats()

            print("\n" + "=" * 40)
            print("~ OPERATOR DASHBOARD ~")
            print(f"Total Spots: {self.parking_lot.get_total_spots_count()}")
            print("=" * 40)

            if stats:
                print(f" 🛵 Scooters: {stats.get('S', [0, 0])[0]}/{stats.get('S', [0, 0])[1]} Free")
                print(f" 🚗 Cars:     {stats.get('C', [0, 0])[0]}/{stats.get('C', [0, 0])[1]} Free")
                print(f" 🚚 Trucks:   {stats.get('T', [0, 0])[0]}/{stats.get('T', [0, 0])[1]} Free")

            print("-" * 40 + "\n")

            print("1 -> Park a Vehicle\n"
                  "2 -> Remove a Vehicle\n"
                  "3 -> Show Map\n"
                  "4 -> Search for Vehicle\n"
                  "0 -> Return / Logout")

            try:
                choice = int(input("\n Enter Option : "))
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            match choice:
                case 1:
                    self.handle_arrival()
                case 2:
                    self.handle_exit()
                case 3:
                    self.parking_lot.show_map()
                case 4:
                    self.find_my_car()
                case 0:
                    print("Exiting Operator Mode...")
                    break
                case _:
                    print("Incorrect Choice. Please select again")


    def find_my_car(self):
        print("\n--- Find a Vehicle ---")
        plate = input("\nEnter License Plate:")
        check = self.parking_lot.get_spot_by_plate(plate)
        if check:
            print(f"Spot: {check.get_id}")
        else:
            print("Error: No spot found.")


    def handle_arrival(self):
        print("\n--- Park a Vehicle ---")
        print("\nPlease select Vehicle Type to Park")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("S - Two Wheeler (Scooter/Bike) \nC - Car (Mini/SUV/Van) \nT - Heavy Vehicle (Bus/Truck)")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        raw_input = str(input("Type : ")).upper().strip()
        v_type = raw_input[0]

        print("Please Input Vehicle License Plate No.")
        v_plate = str(input("License Plate : "))

        vehicle_obj = create_vehicle_instance(v_type, v_plate)

        if vehicle_obj is not None:
            spot = self.parking_lot.find_spot(vehicle_obj)

            if spot:
                spot.park_vehicle(vehicle_obj)
                entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
                print(f"Success! Parked in {spot.get_id} ")
                print(f"Time of Entry: {entry_time}")
                floor, v_type, spot_no = spot.get_id.split('-')
                self.parking_lot.log_vehicle_entry(v_type, spot.get_id, v_plate)
            else:
                print("Sorry. No Parking Spots Available.")


    def handle_exit(self):
        print("\n--- Remove a Vehicle ---")
        user_input = input("\nPlease enter your Spot ID (Eg: 0-S-17) or License Plate: ")
        spot = self.parking_lot.get_spot_by_id(user_input)

        if spot is None:
            #i.e., LicensePlate Input by User
            spot = self.parking_lot.get_spot_by_plate(user_input)

        if spot:
            removed_vehicle = spot.remove_vehicle()

            if removed_vehicle:
                vehicle_obj, start_time = removed_vehicle

                amount, billable_hours, duration, exit_time = self.parking_lot.calculate_bill(start_time, vehicle_obj)
                print("\n" + "=" * 30)
                print("      PRINTING RECEIPT...    ")
                print("=" * 30)
                time.sleep(0.5)

                print(f"Vehicle:   {vehicle_obj.license_plate}")
                time.sleep(0.2)
                print(f"Spot ID:   {spot.get_id}")
                time.sleep(0.2)
                print(f"Duration:  {str(duration).split('.')[0]}")
                time.sleep(0.2)

                print("-" * 30)
                print(f"TOTAL DUE: ₹{amount}")
                print("=" * 30 + "\n")
                print("Thank you for parking with us!")

                log_success = self.parking_lot.log_vehicle_exit(exit_time, spot.get_id, amount)
                if not log_success:
                    print(f"Warning: No record found for {spot.get_id}")

            else:
                print(f"Error: Spot {spot.get_id} was already empty.")
        else:
            print(f"Error: Could not find vehicle or spot matching {user_input}")


    @classmethod
    def process_web_arrival(cls, v_type, v_plate):
        """
        Web-safe version of handle_arrival.
        Takes inputs directly from FastAPI and returns a dictionary response.
        """
        vehicle_obj = create_vehicle_instance(v_type, v_plate)
        v_plate = v_plate.upper()

        if vehicle_obj is not None:
            spot = cls.parking_lot.find_spot(vehicle_obj)

            if spot:
                spot.park_vehicle(vehicle_obj)
                entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cls.parking_lot.log_vehicle_entry(v_type, spot.get_id, v_plate)

                return {
                    "status": "success",
                    "spot_id": spot.get_id,
                    "entry_time": entry_time
                }
            else:
                return {"status": "error", "message": "Sorry. No Parking Spots Available for this vehicle type."}
        else:
            return {"status": "error", "message": "Failed to create vehicle instance."}


    @classmethod
    def process_web_exit_lookup(cls, search_query):
        """
        STEP 1: Safely fetches vehicle session data and calculates the CURRENT bill
        without actually removing the vehicle from the spot.
        """
        # 1. Direct DB check to avoid altering OOP spot states prematurely
        cls.parking_lot.cursor.execute("""
            SELECT plate_no, spot_id, entry_time, v_type
            FROM active_sessions
            WHERE plate_no = ?
            OR spot_id = ?
        """, (search_query, search_query))

        session = cls.parking_lot.cursor.fetchone()
        if not session:
            return {"status": "error", "message": "Vehicle not found in active sessions."}

        plate_no, spot_id, entry_time_str, vtype = session

        start_time = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
        if vtype == "S":
            vehicle_obj = Scooter(plate_no)
        elif vtype == "C":
            vehicle_obj = Car(plate_no)
        else:
            vehicle_obj = Truck(plate_no)

        # 3. Calculate current bill (does not save to DB)
        amount, billable_hours, duration, exit_time = cls.parking_lot.calculate_bill(start_time, vehicle_obj)

        return {
            "status": "success",
            "plate": plate_no,
            "spot": spot_id,
            "entry": entry_time_str,
            "duration": str(duration).split('.')[0],
            "fee": amount,
            "type": vtype
        }


    @classmethod
    def process_web_exit_checkout(cls, search_query):
        """
        STEP 2: The final confirmation. Removes the vehicle from memory,
        logs the exit, and finalizes the transaction in the database.
        """
        spot = cls.parking_lot.get_spot_by_id(search_query)
        if not spot:
            spot = cls.parking_lot.get_spot_by_plate(search_query)

        if spot:
            removed_vehicle = spot.remove_vehicle()

            if removed_vehicle:
                vehicle_obj, start_time = removed_vehicle
                amount, billable_hours, duration, exit_time = cls.parking_lot.calculate_bill(start_time, vehicle_obj)
                log_success = cls.parking_lot.log_vehicle_exit(exit_time, spot.get_id, amount)

                if log_success:
                    return {
                        "status": "success",
                        "fee": amount,
                        "duration": str(duration).split('.')[0],
                        "plate": vehicle_obj.license_plate
                    }
                else:
                    return {"status": "error", "message": "Database failed to log exit."}
            else:
                return {"status": "error", "message": f"Spot {spot.get_id} is already empty."}
        else:
            return {"status": "error", "message": "Could not locate active vehicle session."}


    @classmethod
    def process_web_search(cls, search_query):
        """
        Uses OOP ParkingLot functions to locate a vehicle by Spot ID or License Plate.
        Calculates live accrued fee without removing the vehicle from memory.
        """

        spot = cls.parking_lot.get_spot_by_id(search_query)

        if spot is None:
            spot = cls.parking_lot.get_spot_by_plate(search_query)

        if spot:
            cls.parking_lot.cursor.execute("""
                SELECT plate_no, entry_time, v_type
                FROM active_sessions
                WHERE spot_id = ?
            """, (spot.get_id,))

            session = cls.parking_lot.cursor.fetchone()
            if session:
                plate_no, entry_time_str, vtype = session

                start_time = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")

                if vtype == "S":
                    vehicle_obj = Scooter(plate_no)
                elif vtype == "C":
                    vehicle_obj = Car(plate_no)
                else:
                    vehicle_obj = Truck(plate_no)

                amount, billable_hours, duration, exit_time = cls.parking_lot.calculate_bill(start_time, vehicle_obj)

                return {
                    "status": "success",
                    "plate": plate_no,
                    "spot": spot.get_id,
                    "entry": entry_time_str,
                    "duration": str(duration).split('.')[0],  # Strips microseconds
                    "fee": amount,
                    "type": vtype
                }

        return {"status": "error", "message": "Vehicle not found. It may not be parked here."}


