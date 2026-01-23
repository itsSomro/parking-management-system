from Vehicle import Scooter, Truck, Car, VehicleSize


def create_vehicle_instance(v_type, v_plate):
    vehicle = None
    match v_type:
        case 1:
            vehicle = Scooter(v_plate)
        case 2:
            vehicle = Car(v_plate)
        case 3:
            vehicle = Truck(v_plate)
        case _:
            print("Invalid Vehicle Type Selected!")
            return  None
    return vehicle


class EntryTerminal:
    def __init__(self, parking_lot):
        self.parking_lot = parking_lot


    def edit_spots(self):
        choice = int(input("1 - Add Spots | 2 - Remove Spots"))
        start = int(input("Start Value :"))
        stop = int(input("Stop Value :")) + 1
        v_type_str = input("S - Scooter | C - Car | T - Truck :").upper()
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
            self.parking_lot.add_spots(start, stop, v_type_enum, v_type_str)
            print("Spots Added Successfully.")
        elif choice == 2:
            self.parking_lot.remove_spots(start, stop, v_type_enum, v_type_str)
            print("Spots Removed Successfully.")
        self.parking_lot.save_to_csv()


    def handle_arrival(self):
        print("Welcome to the Smart Parking Lot!~\n")
        print("Please select Vehicle Type to Park")
        print("1 - Two Wheeler (Scooter/Bike) \n2 - Car (Mini/SUV/Van) \n3 - Heavy Vehicle (Bus/Truck)")
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        v_type = int(input("Type : "))

        print("Please Input Vehicle License Plate No.")
        v_plate = str(input("License Plate : "))

        vehicle_obj = create_vehicle_instance(v_type, v_plate)

        if vehicle_obj is not None:
            spot = self.parking_lot.find_spot(vehicle_obj)

            if spot:
                spot.park_vehicle(vehicle_obj)
                print(f"Success! Parked in {spot.get_id}")
                self.parking_lot.save_to_csv()
            else:
                print("Sorry. No Parking Spots Available.")


    def handle_exit(self):
        print("\n ~~~ Exiting Terminal ~~~")
        spot_id = input("Please enter your Spot ID : ")
        spot = self.parking_lot.get_spot_by_id(spot_id)

        if spot:
            removed_vehicle = spot.remove_vehicle()

            if removed_vehicle:
                print(f"Vehicle {removed_vehicle.license_plate} has left {spot.get_id}.")
                print("Thank you for parking with us!")
                self.parking_lot.save_to_csv()

            else:
                print(f"Error: Spot {spot.get_id} was already empty.")
        else:
            print("Error: Spot ID not found.")
