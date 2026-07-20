class AuthTerminal:
    def __init__(self, db):
        self.db = db

    def show_login_screen(self):
        while True:
            print("\n" + "="*40)
            print("     PARKING SPACES LOGIN PAGE    ")
            print("="*40)
            print("Type '0' in username to shut down")

            username = input("\nUsername: ").strip()
            if username == '0':
                return False, None

            password = input("Password: ").strip()

            verification, role = self.db.verify_login(username, password)

            if verification:
                return True, role
            else:
                print("\n[!] Access Denied: Invalid Username or Password. Please Try Again")