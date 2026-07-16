from Vehicle import VehicleSize
from ParkingSpot import ParkingSpot
from ParkingLot import ParkingLot
from EntryTerminal import EntryTerminal
from db.Database import Database


db = Database()
my_parking_lot = ParkingLot(db)

# # TEMPORARY CLEANUP SCRIPT (use incase of wrong vehicle type entered into lot
# my_parking_lot.cursor.execute("DELETE FROM Master_Table WHERE v_type = 'CAR'")
# my_parking_lot.conn.commit()
# print("Corrupted spots deleted!")

total_spots = my_parking_lot.get_total_spots_count()

if total_spots > 0:
    print("Database Loaded Successfully")
    print(f"Parking Lot loaded with {total_spots} spots")
else:
    print("No existing parking spots found")
    print("Initializing Parking Data for 1st time-")

    default_layout = {
        0: {'S':20, 'C':20, 'T':10},
        1: {'S':20, 'C':20, 'T':0},
        2: {'S':0, 'C':10, 'T':0}
    }

    my_parking_lot.configure_lot(default_layout)
    print(f"Parking Lot initialized with {my_parking_lot.get_total_spots_count()} spots")

entry_terminal = EntryTerminal(my_parking_lot)

while True:
    stats = my_parking_lot.get_stats()

    print("\n" + "="*40)
    print("~ PARKING MANAGEMENT SYSTEM ~")
    print(f"Total Spots: {my_parking_lot.get_total_spots_count()}")
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

