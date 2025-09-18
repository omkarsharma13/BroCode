from server import request_ride

def main():
    print("🚖 Welcome to Mini Uber - User Client")

    while True:
        try:
            print("\n📋 Menu:")
            print("1. Request a Ride")
            print("2. Exit")

            choice = input("Enter choice (1/2): ").strip()

            if choice == "1":
                try:
                    user_id = int(input("Enter your user_id (number): "))
                except ValueError:
                    print("❌ Invalid user_id. Must be a number.")
                    continue

                pickup = input("Enter Pickup Location: ").strip()
                destination = input("Enter Destination: ").strip()

                ride = request_ride(user_id, pickup, destination)
                print("✅ Ride Request Result:", ride)

            elif choice == "2":
                print("👋 Exiting Mini Uber - Goodbye!")
                break

            else:
                print("❌ Invalid choice. Please enter 1 or 2.")

        except KeyboardInterrupt:
            print("\n👋 Exiting Mini Uber - Goodbye!")
            break


if __name__ == "__main__":
    main()
