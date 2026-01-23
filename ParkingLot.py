import csv
from Vehicle import Vehicle, VehicleSize, Scooter, Car, Truck
from ParkingSpot import ParkingSpot

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


    def save_to_csv(self, filename="parking_data.csv"):
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["SpotID", "SpotType", "Occupancy", "LicensePlate"])

            for spot in self.spots.values():
                s_id = spot.get_id
                s_type = spot.spot_type
                s_occupancy = not spot.is_free()

                if s_occupancy:
                    s_plate = spot.vehicle.license_plate
                else:
                    s_plate = "None"

                writer.writerow([s_id,s_type,s_occupancy,s_plate])

        print("Parking Lot Data has been saved on file.")


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

                    if spot_type_enum == VehicleSize.SCOOTER:
                        vehicle = Scooter(plate)
                    elif spot_type_enum == VehicleSize.CAR:
                        vehicle = Car(plate)
                    else:
                        vehicle = Truck(plate)

                    new_spot.park_vehicle(vehicle)

                self.add_spot(new_spot)


    def show_map(self):
        for spot in self.spots.values():
            status = "Occupied" if not spot.is_free() else "Free"
            print(f" {spot.get_id} -> {status}")

