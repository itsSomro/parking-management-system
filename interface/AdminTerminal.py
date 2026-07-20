from core.Vehicle import VehicleSize
from interface.OperatorTerminal import OperatorTerminal

class AdminTerminal(OperatorTerminal):
    def __init__(self, parking_lot, db):
        super().__init__(parking_lot)
        self.db = db


    def launch(self):
        while True:
            print("\n" + "=" * 40)
            print("~ ADMINISTRATOR DASHBOARD ~")
            print("=" * 40 + "\n")

            print("1 -> View System Status (Map & Stats)\n"
                  "2 -> Edit Parking Spots Layout\n"
                  "3 -> Update Billing Rates\n"
                  "4 -> Create New User Account\n"
                  "5 -> Enter Operator Mode (Park/Remove Cars)\n"
                  "0 -> Logout & Exit")

            try:
                choice = int(input("\n Enter Option : "))
            except ValueError:
                print("Invalid input. Please enter a number.")
                continue

            match choice:
                case 1:
                    self.parking_lot.show_map()
                    stats = self.parking_lot.get_stats()

                    print(f"Total Spots: {self.parking_lot.get_total_spots_count()}")
                    print("=" * 40)

                    if stats:
                        print(f" 🛵 Scooters: {stats.get('S', [0, 0])[0]}/{stats.get('S', [0, 0])[1]} Free")
                        print(f" 🚗 Cars:     {stats.get('C', [0, 0])[0]}/{stats.get('C', [0, 0])[1]} Free")
                        print(f" 🚚 Trucks:   {stats.get('T', [0, 0])[0]}/{stats.get('T', [0, 0])[1]} Free")

                    print("-" * 40 + "\n")
                case 2:
                    self.edit_lot_flow()
                case 3:
                    self.update_rate_flow()
                case 4:
                    self.create_user_flow()
                case 5:
                    self.operator_dashboard()
                case 0:
                    print("Logging out Admin. . . Data Saved")
                    break

                case _:
                    print("Incorrect Choice. Please select again")


    def create_user_flow(self):
        print("\n--- Create New User ---")
        new_user = input("Enter new username: ").strip()
        new_pass = input("Enter new password: ").strip()

        print("\nSelect Role:")
        print("1. Operator")
        print("2. Admin")
        role_choice = input("Option (1/2): ").strip()

        role = "Operator" if role_choice == '1' else "Admin"

        success = self.db.add_new_user(new_user, new_pass, role)

        if success:
            print(f"\n[+] Successfully created {role} account for '{new_user}'")
        else:
            print(f"\n[!] Error: The username '{new_user}' is already taken!")


    def update_rate_flow(self):
        print("\n--- Update Billing Rates ---")
        vehicle_types = ['S', 'C', 'T']
        vehicle_types_str = ["Two Wheeler", "Car", "Heavy Vehicle"]
        user_data = {}
        i = 0

        for vehicle_str in vehicle_types_str:
            rate = float(input(f"Enter {vehicle_str} Rate: ₹"))
            user_data[vehicle_types[i]] = rate
            i += 1

        self.parking_lot.update_rates(user_data)
        print("\nRates Updated Successfully!")


    def edit_lot_flow(self):
        print("\n--- Edit Lot Layout ---")
        print("\nSelect Option:")
        print("1 -> Configure/Set New Lot")
        print("2 -> Edit Current Lot Layout")
        choice = int(input("Option (1/2): "))

        if choice == 1:
            print("\n--- Configuring New Lot Layout ---")
            v_types = {'Two Wheeler':'S', 'Car':'C', 'Heavy Vehicle':'T'}
            lot_config = {}

            floors = int(input("\nEnter floors: "))
            print("Enter Spots per Floor")

            for floor in range(floors):
                floor_layout = {}

                print(f"     Floor {floor}     ")
                for v_type_str,v_type in v_types.items():
                    spots_count = int(input(f"{v_type_str} [{v_type}]: "))
                    floor_layout[v_type] = spots_count

                lot_config[floor] = floor_layout

            self.parking_lot.configure_lot(lot_config)


        if choice == 2:
            self.edit_spots()


    def edit_spots(self):
        choice = int(input("1 - Add Spots | 2 - Remove Spots"))
        floor = int(input("Enter Floor (0,1,2): "))
        start = int(input("Start Value :"))
        stop = int(input("Stop Value :")) + 1
        raw_input = input("S - Scooter | C - Car | T - Truck :").upper().strip()
        v_type_str = raw_input[0] if raw_input else 'C'  #  Incase one misinputs Eg: Car/car/CARS etc

        if v_type_str not in ['S', 'C', 'T']:
            v_type_str = 'C'

        if choice == 1:
            self.parking_lot.add_spots(floor, start, stop, v_type_str)
            print("Spots Added Successfully.")
        elif choice == 2:
            self.parking_lot.remove_spots(floor, start, stop, v_type_str)
            print("Spots Removed Successfully.")









