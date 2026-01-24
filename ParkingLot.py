import csv
from datetime import datetime
from ParkingSpot import ParkingSpot
from Vehicle import VehicleSize, Scooter, Car, Truck


class ParkingLot:
    def __init__(self):
        self.spots = {}


    def add_spot(self, spot):
        self.spots[spot.get_id] = spot


    def remove_spot(self, spot_id):
        if spot_id in self.spots:
            spot = self.spots[spot_id]

            if not spot.is_free():
                print(f"Error: Spot {spot_id} is occupied! Remove vehicle first.")
                return False

            del self.spots[spot_id]
            print(f"Spot {spot_id} removed successfully.")
            return True
        else:
            print(f"Error: Spot {spot_id} does not exist")
            return False


    def add_spots(self, start, stop, v_type_enum, v_type_str):
        for i in range(start, stop):
            self.add_spot(ParkingSpot(f"{v_type_str}-{i}", v_type_enum))


    def remove_spots(self, start, stop, v_type_enum, v_type_str):
        for i in range(start, stop):
            self.remove_spot(ParkingSpot(f"{v_type_str}-{i}", v_type_enum))


    def find_spot(self, vehicle):
        for spot in self.spots.values():
            if spot.is_free() and spot.can_fit_vehicle(vehicle):
                return spot
        return None


    def get_spot_by_id(self, spot_id):
        return self.spots.get(spot_id)


    def initialize_parking_lot(self):
        for i in range(1, 6):
            self.add_spot(ParkingSpot(f"S-{i}", VehicleSize.SCOOTER))

        for i in range(1, 11):
            self.add_spot(ParkingSpot(f"C-{i}", VehicleSize.CAR))

        for i in range(1, 6):
            self.add_spot(ParkingSpot(f"T-{i}", VehicleSize.TRUCK))


    def get_spot_by_plate(self, license_plate):
        for spot in self.spots.values():
            if not spot.is_free():
                if spot.vehicle.license_plate.upper() == license_plate.upper():
                    return spot
        return None


    def save_to_csv(self, filename="parking_data.csv"):
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["SpotID", "SpotType", "Occupancy", "LicensePlate", "EntryTime"])

            # SORTING
            def get_sort_key(spot):
                s_id = spot.get_id

                try:
                    prefix, number = s_id.split('-')
                    return prefix, int(number)

                except ValueError:
                    return s_id, 0

            sorted_spots = sorted(self.spots.values(), key=get_sort_key)

            for spot in sorted_spots:
                s_id = spot.get_id
                s_type = spot.spot_type
                s_occupancy = not spot.is_free()

                if s_occupancy:
                    s_plate = spot.vehicle.license_plate
                    s_time = spot.entry_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    s_plate = "None"
                    s_time = "None"

                writer.writerow([s_id,s_type,s_occupancy,s_plate,s_time])

        print("Parking Lot Data Sorted and Saved!")


    def load_from_csv(self, filename="parking_data.csv"):
        self.spots = {}

        with open(filename, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                spot_id = row["SpotID"]
                spot_type_str = row["SpotType"]
                spot_type_enum = VehicleSize[spot_type_str]
                new_spot = ParkingSpot(spot_id, spot_type_enum)

                if row["Occupancy"] == "True":
                    plate = row["LicensePlate"]
                    time_str = row["EntryTime"]

                    try:
                        loaded_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # SAFETY FEATURE INCASE PARKED VEHICLE DOESN'T HAVE TIME OF PARKING
                        # If time is "None" or broken, just use NOW to prevent crash
                        loaded_time = datetime.now()

                    if spot_type_enum == VehicleSize.SCOOTER:
                        vehicle = Scooter(plate)
                    elif spot_type_enum == VehicleSize.CAR:
                        vehicle = Car(plate)
                    else:
                        vehicle = Truck(plate)

                    new_spot.park_vehicle(vehicle)
                    new_spot._entry_time = loaded_time

                self.add_spot(new_spot)


    def show_map(self):
        print("\n ~~~ PARKING LOT MAP ~~~")

        def get_sort_key(spot):
            s_id = spot.get_id
            try:
                prefix, number = s_id.split('-')
                return prefix, int(number)
            except ValueError:
                return s_id, 0

        sorted_spots = sorted(self.spots.values(), key=get_sort_key)

        for spot in sorted_spots:
            status = "Occupied" if not spot.is_free() else "Free"
            print(f"{spot.get_id} -> {status}")

        print("~~~~~~~~~~~~~~~~~~~~~~~~~~")


    def get_stats(self):
        total_scooter = 0
        free_scooter = 0

        total_car = 0
        free_car = 0

        total_truck = 0
        free_truck = 0

        for spot in self.spots.values():
            # Check Type: SCOOTER
            if spot.spot_type == "SCOOTER":
                total_scooter += 1
                if spot.is_free():
                    free_scooter += 1

            # Check Type: CAR
            elif spot.spot_type == "CAR":
                total_car += 1
                if spot.is_free():
                    free_car += 1

            # Check Type: TRUCK
            elif spot.spot_type == "TRUCK":
                total_truck += 1
                if spot.is_free():
                    free_truck += 1

        return {
            "S": (free_scooter, total_scooter),
            "C": (free_car, total_car),
            "T": (free_truck, total_truck)
        }

