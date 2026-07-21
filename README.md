# 🚗 Smart Parking Management System

### 🌟 About

A Python-based Parking Management System designed to streamline vehicle entry, exit, and billing operations. What began as a comprehensive study of Object-Oriented Programming (OOP) has rapidly evolved into an AI-driven automated gate system. 

**Current Status:** The core OOP logic, administrative terminal interfaces, and data persistence modules are fully implemented. The live computer vision pipeline (YOLO object tracking + OCR validation) is now successfully deployed and ready to be linked to the core system.

---

### 🛠️ Tech Stack

* **Language:** Python 3.11+
* **Computer Vision:** OpenCV, Ultralytics YOLOv8
* **Object Tracking:** ByteTrack
* **Optical Character Recognition:** EasyOCR (GPU-accelerated)
* **Data Persistence:** Python File Handling / Database Logic
* **Core Concepts:** OOP (Inheritance, Polymorphism, Encapsulation), Machine Learning pipeline integration, cross-platform dynamic pathing, Version Control

---

### ⚡ Features

#### ✅ Core System & Terminals (Live)
* **Smart Entry/Exit Terminals:** Isolated Operator and Admin dashboard interfaces to manage vehicle flow and monitor capacity.
* **Dynamic Billing:** Algorithm calculates fees based on parked duration (rounding up to the nearest hour).
* **Vehicle Management:** Supports multiple vehicle types (Car, Bike, Bus) using Class Inheritance.
* **Data Persistence:** All parking sessions are actively managed and saved to ensure zero data loss upon shutdown.

#### ✅ AI Vision Pipeline (Live)
* **Real-Time Video Processing:** Captures and buffers live camera streams for seamless real-time monitoring.
* **YOLO Tracking Engine:** Dynamically detects license plates and assigns persistent IDs across frames using ByteTrack, ensuring zero duplicate processing of the same vehicle.
* **Smart Plate Extraction:** Automatically crops, pads, upscales (cubic interpolation), and reads license plates using EasyOCR.
* **Strict Format Gatekeeper:** Employs a custom algorithmic regex and dynamic confusion matrix (e.g., auto-correcting vertical artifacts `|` to `1`) to strictly validate standard plate formats before logging them.
* **Cross-Platform Readiness:** Uses dynamic `os.path` logic, ensuring the project can be cloned and run on any machine without pathing errors.

#### 🤖 Next Phases (Coming Soon)
* **Pipeline Integration:** Connecting the live vision engine directly to the Operator terminal for automated, hands-free entry/exit logging.
* **Web App & API Launch:** Transitioning the local application to a full web-based portal with RESTful APIs to allow remote management and external service integration.
* **Predictive Optimization:** Linear Regression modeling to predict peak parking hours and optimize spot allocation.

---

### 📂 Project Structure

```text
📂 ParkingSpaces/
├── 📂 core/                 # Core OOP Logic 
│   ├── ParkingLot.py        # Core logic for floor/spot management
│   ├── ParkingSpot.py       # Individual spot attributes
│   └── Vehicle.py           # Vehicle classes (Car, Bike, SUV)
│
├── 📂 db/                   # Database operations and persistence
│   ├── database.py          # Database connection and queries
│   └── parking_data.csv     # Persistent local storage for sessions
│
├── 📂 interface/            # Operator and Admin dashboard interfaces
│   ├── AdminTerminal.py     # UI/Logic for admin override and analytics
│   ├── AuthTerminal.py      # Logic for autheticating logins and ids      
│   └── OperatorTerminal.py  # UI/Logic for operator controls
│
├── 📂 models/               # YOLO Weights ⚠️ Ignored by Git
│   ├── best.pt              # Custom trained license plate detector
│   └── yolov8n.pt           # Base YOLOv8 nano model
│
├── 📂 scripts/              # AI Development & Training tools
│   ├── camera_test.py       # Diagnostics for stream connections
│   ├── data.yaml            # YOLO dataset configuration
│   ├── train_model.py       # Script to initiate YOLO model training
│   ├── yolo_dataset_prep.py # Utilities for formatting XML/TXT datasets
│   └── yolo_test.py         # Sandbox testing for object tracking
│
├── 📂 vision_tools/         # Production AI Engine
│   ├── live_plate_tracker.py # Real-time camera tracking and OCR engine
│   └── plate_detector.py     # Static image testing logic
│
├── .gitignore               # Secures heavy datasets, weights, and virtual environments
├── main.py                  # Master entry point for the application
└── README.md                # Project documentation
