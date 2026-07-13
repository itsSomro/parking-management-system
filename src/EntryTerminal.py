import time
from datetime import datetime
from Vehicle import Scooter, Truck, Car, VehicleSize
import math


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
            return  None
    return vehicle


class EntryTerminal:
    def __init__(self, parking_lot):
        self.parking_lot = parking_lot


    def slow_print(self, text, speed=0.02):
        import time
        import sys
        for char in text:
            print(char, end='', flush=True)
            time.sleep(speed)
        print()


    def find_my_car(self):
        plate = input("Enter License Plate:")
        check = self.parking_lot.get_spot_by_plate(plate)
        if check:
            print(f"Spot: {check.get_id}")
        else:
            print("Error: No spot found.")


    def edit_spots(self):
        choice = int(input("1 - Add Spots | 2 - Remove Spots"))
        floor = int(input("Enter Floor (0,1,2): "))
        start = int(input("Start Value :"))
        stop = int(input("Stop Value :")) + 1
        raw_input = input("S - Scooter | C - Car | T - Truck :").upper().strip()
        v_type_str = raw_input[0] if raw_input else 'C'  #  Incase one misinputs Eg: Car/car/CARS etc

        match v_type_str:
            case 'S':
                v_type_enum = VehicleSize.SCOOTER
            case 'C':
                v_type_enum = VehicleSize.CAR
            case 'T':
                v_type_enum = VehicleSize.TRUCK
            case _:
                v_type_enum = VehicleSize.CAR

        if choice == 1:
            self.parking_lot.add_spots(floor, start, stop, v_type_enum, v_type_str)
            print("Spots Added Successfully.")
        elif choice == 2:
            self.parking_lot.remove_spots(floor, start, stop, v_type_enum, v_type_str)
            print("Spots Removed Successfully.")


    def handle_arrival(self):
        self.slow_print("Initializing System...", speed=0.05)
        time.sleep(0.5)
        self.slow_print("Welcome to the Smart Parking Lot! 🅿️", speed=0.03)
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print("Please select Vehicle Type to Park")
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
                entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"Success! Parked in {spot.get_id} ")
                print(f"Time of Entry: {entry_time}")
                floor, v_type, spot_no = spot.get_id.split('-')
                self.parking_lot.log_vehicle_entry(floor, v_type, spot_no, v_plate)
            else:
                print("Sorry. No Parking Spots Available.")


    def handle_exit(self):
        print("\n ~~~ Exiting Terminal ~~~")
        user_input = input("Please enter your Spot ID (Eg: 0-S-17) or License Plate: ")
        spot = self.parking_lot.get_spot_by_id(user_input)

        if spot is None:
            #i.e., LicensePlate Input by User
            spot = self.parking_lot.get_spot_by_plate(user_input)

        if spot:
            removed_vehicle = spot.remove_vehicle()

            if removed_vehicle:
                vehicle_obj, start_time = removed_vehicle

                amount, billable_hours, duration = self.calculate_bill(start_time, vehicle_obj)
                print("\n" + "=" * 30)
                self.slow_print("      PRINTING RECEIPT...    ", speed=0.05)
                print("=" * 30)
                time.sleep(0.5)

                print(f"Vehicle:   {vehicle_obj.license_plate}")
                time.sleep(0.2)
                print(f"Spot ID:   {spot.get_id}")
                time.sleep(0.2)
                print(f"Duration:  {str(duration).split('.')[0]}")
                time.sleep(0.2)

                print("-" * 30)
                self.slow_print(f"TOTAL DUE: ₹{amount}", speed=0.1)
                print("=" * 30 + "\n")
                print("Thank you for parking with us!")

                floor, vtype, spot_no = spot.get_id.split('-')
                self.parking_lot.log_vehicle_exit(floor,vtype,spot_no)

            else:
                print(f"Error: Spot {spot.get_id} was already empty.")
        else:
            print(f"Error: Could not find vehicle or spot matching {user_input}")


    def calculate_bill(self, start_time, vehicle_type):
        end_time = datetime.utcnow()
        duration = end_time - start_time
        hours = duration.total_seconds() / 3600

        # Rounding up (charging for the whole hour)
        billable_hours = math.ceil(hours)

        # ~~~ DIFFERENT RATE METHODS ~~~
        # (Use ONLY one: Comment the rest)

        #1. BILLING PER HOUR BASIS
        if vehicle_type == VehicleSize.SCOOTER:
            rate = 5
        elif vehicle_type == VehicleSize.CAR:
            rate = 10
        else:
            rate = 20

        return billable_hours * rate, billable_hours, duration

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

