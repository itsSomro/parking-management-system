# 🚗 Smart Parking Management System

## 🌟 About
A Python-based Parking Management System designed to streamline vehicle entry, exit, and billing operations. This project serves as a comprehensive study of **Object-Oriented Programming (OOP)** principles and is currently evolving to include **Artificial Intelligence** for automated vehicle recognition and spot optimization.

**Current Status:** Core logic implemented; AI modules in development.

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **Data Persistence:** CSV (File Handling)
* **Core Concepts:** OOP (Inheritance, Polymorphism, Encapsulation, Abstraction)
* **Version Control:** Git & GitHub

## ⚡ Features
### ✅ Core Functionality
* **Smart Entry/Exit:** Terminals to manage vehicle flow.
* **Dynamic Billing:** algorithm calculates fees based on duration (rounding up to the nearest hour).
* **Vehicle Management:** Supports multiple vehicle types (Car, Bike, SUV) using Class Inheritance.
* **Search System:** Locate vehicles instantly by **Spot ID** or **License Plate**.
* **Data Persistence:** All parking sessions are saved to CSV, ensuring no data loss on shutdown.

### 🤖 AI Integration (Coming Soon)
* **License Plate Recognition (OCR):** Auto-detect plates from camera feeds.
* **Vehicle Classification:** AI-based detection of vehicle type.
* **Optimization:** Linear Regression model to predict peak hours and optimize spot allocation.

## 📂 Project Structure
```text
📂 ParkingSpaces/
├── 📂 src/                  # Main Application Source Code
│   ├── EntryTerminal.py     # Handle vehicle entry logic
│   ├── ParkingLot.py        # Core logic for floor/spot management
│   ├── ParkingSpot.py       # Individual spot attributes
│   ├── Vehicle.py           # Vehicle classes (Car, Bike, SUV)
│   └── main.py              # Entry point to run the app
│
├── 📂 data/                 # Data Storage
│   └── parking_data.csv     # Persistent storage for parking sessions
│
├── 📂 assets/               # Visual Assets
│   ├── ground_floor.png     # Blueprints for UI mapping
│   └── ...
│
├── 📂 playground/           # R&D and Testing
│   ├── ImageReaderTest.py   # OpenCV experiments
│   └── LicensePlateOCR.py   # AI integration tests
│
├── 📂 Datasets - LicensePlates/  # (Local Only - Not on GitHub)
│   └── ...                  # Training images for OCR
│
├── .gitignore               # Tells Git to ignore venv and datasets
└── README.md                # Project documentation
