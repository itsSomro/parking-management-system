from db.Database import Database
from core.ParkingLot import ParkingLot
from interface.AuthTerminal import AuthTerminal
from interface.AdminTerminal import AdminTerminal
from interface.OperatorTerminal import OperatorTerminal

def main():
    # --------------------------------------------------------------------------
    # 1. INITIALIZING DATABASE
    db = Database()
    my_parking_lot = ParkingLot(db)

    print("Checking system security...")
    admin_created = db.setup_admin_account()
    if admin_created:
        print("No Admin found. Default Admin account secured and saved")

    # --------------------------------------------------------------------------
    # 2. INITIALIZING PARKING DATA
    total_spots = my_parking_lot.get_total_spots_count()

    #Checks if parking lot is already created (on 1st open it will resort to default)
    if total_spots > 0:
        print("Database Loaded Successfully")
        print(f"Parking Lot loaded with {total_spots} spots")
    else:
        print("No existing parking spots found")
        print("Initializing Default Parking Data Layout...")

        default_layout = {
            0: {'S': 20, 'C': 20, 'T': 10},
            1: {'S': 20, 'C': 20, 'T': 0},
            2: {'S': 0, 'C': 10, 'T': 0}
        }
        my_parking_lot.configure_lot(default_layout)
        print(f"Parking Lot initialized with {my_parking_lot.get_total_spots_count()} spots")

    #Similar like parking lot check (on 1st open it will resort to default)
    if not my_parking_lot.are_rates_configured():
        print("No existing billing rates found")
        print("Initializing Default Billing Rates...")
        default_rate = {'S': 5, 'C': 10, 'T': 20}
        my_parking_lot.update_rates(default_rate)
        print("Billing Rates initialized successfully")

    # --------------------------------------------------------------------------
    # 3. AUTHENTICATION AND UI LAUNCH
    authenticator = AuthTerminal(db)
    login_success, user_role = authenticator.show_login_screen()

    if login_success:
        print(f"\nLogin Successful. Welcome, {user_role}")

        if user_role == "Admin":
            admin_board = AdminTerminal(my_parking_lot, db)
            admin_board.launch()

        elif user_role == "Operator":
            operator_board = OperatorTerminal()
            operator_board.operator_dashboard()

    else:
        print("\nProgram terminated gracefully. Data Saved")

if __name__ == "__main__":
    main()



