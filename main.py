from Vehicle import VehicleSize
from ParkingSpot import ParkingSpot
from ParkingLot import ParkingLot
from EntryTerminal import EntryTerminal


my_parking_lot = ParkingLot()
try:
    my_parking_lot.load_from_csv("parking_data.csv")
    print("Data Loaded Successfully!")

except FileNotFoundError:
    print("Data File could not be opened.")
    print("Initializing Parking Data without file ~~~")
    # INITIALIZING WITHOUT CSV FILE
    ParkingLot.initialize_parking_lot(my_parking_lot)
    print(f"Parking Lot initialized with {len(my_parking_lot.spots)} spots.")


entry_terminal = EntryTerminal(my_parking_lot)

while True:
    stats = my_parking_lot.get_stats()

    print("\n" + "="*40)
    print("~ PARKING MANAGEMENT SYSTEM ~")
    print(f"Total Spots: {len(my_parking_lot.spots)}")
    print("="*40 + "\n")
    # Display Live Counts
    print(f" 🛵 Scooters: {stats['S'][0]}/{stats['S'][1]} Free")
    print(f" 🚗 Cars:     {stats['C'][0]}/{stats['C'][1]} Free")
    print(f" 🚚 Trucks:   {stats['T'][0]}/{stats['T'][1]} Free")
    print("-"*40 + "\n")

    print("1 -> Park a Vehicle\n"
          "2 -> Remove a Vehicle\n"
          "3 -> Show Map\n"
          "4 -> Find My Car\n"
          "9 -> Admin: Edit Spots\n"
          "0 -> Exit Program")
    choice = int(input("\n Enter Option :"))
    match choice:
        case 1:
            entry_terminal.handle_arrival()
        case 2:
            entry_terminal.handle_exit()
        case 3:
            my_parking_lot.show_map()
        case 4:
            entry_terminal.find_my_car()
        case 0:
            print("Exiting Program... Data Saved.")
            break
        case 9:
            entry_terminal.edit_spots()
        case _:
            print("Incorrect Choice. Please select again.")

