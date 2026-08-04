# 🚗 ParkSmart - A Smart Parking Management System

### 🌟 About

A full-stack Python Parking Management System designed to streamline vehicle entry, exit, and billing operations. What began as a comprehensive study of Object-Oriented Programming (OOP) has rapidly evolved into a scalable, web-based application integrated with an AI-driven automated gate system. 

**Current Status:** The core OOP logic has been successfully migrated to a FastAPI backend. Administrative and Operator dashboards are live via a responsive web UI, complete with real-time parking maps and financial tracking. The live computer vision pipeline (YOLO object tracking + OCR validation) runs concurrently, pushing plate data directly to the web operator terminals.

---

### 🛠️ Tech Stack

* **Backend:** Python 3.11+, FastAPI, Uvicorn
* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Cinzel/Dark Theme)
* **Computer Vision:** OpenCV, Ultralytics YOLOv8
* **Object Tracking:** ByteTrack
* **Optical Character Recognition:** EasyOCR (GPU-accelerated)
* **Database:** SQLite3
* **Core Concepts:** OOP, RESTful APIs, Machine Learning Pipelines, CSS Grids, Environment Variable Security

---

### ⚡ Features

#### ✅ Web-Based Dashboards (Live)
* **Smart Terminals:** Isolated Operator and Admin web interfaces to manage vehicle flow, monitor capacity, and handle checkouts.
* **Live Parking Map:** Dynamic CSS-grid visualization mapping out all floors, visually flagging available and occupied spots in real-time.
* **Financial Analytics:** Live session logging calculating daily accrued revenue and total vehicle turnover.
* **Dynamic Billing:** Object-oriented algorithm calculating fees based on parked duration and specific vehicle classifications.
* **Robust Data Persistence:** Completely migrated to a relational SQLite database structure ensuring zero data loss and fast querying.

#### ✅ AI Vision Pipeline (Live)
* **Dual-Camera ANPR Setup:** Isolated tracking scripts for both Gate Entry and Gate Exit using real-time video buffering.
* **YOLO Tracking Engine:** Dynamically detects license plates and assigns persistent IDs across frames using ByteTrack, ensuring zero duplicate processing.
* **Smart Plate Extraction:** Automatically crops, pads, upscales (cubic interpolation), and reads license plates using EasyOCR.
* **Strict Format Gatekeeper:** Employs a custom algorithmic regex and dynamic confusion matrix (e.g., auto-correcting vertical artifacts `|` to `1`) to strictly validate standard plate formats.

---

### ⚙️ Setup & Installation

#### 1. Environment Variables (.env)
This project uses secure environment variables to manage camera streams and database credentials. You must create a `.env` file before running the AI trackers.

1. Create a file named `.env` in the root folder (`ParkingSpaces/`).
2. Add your camera credentials (do not use quotes or spaces around the `=`):
   ```env
   CAMERA_URL=http://YOUR_CAMERA_IP:8080/video
   CAMERA_USER=your_username
   CAMERA_PASS=your_password
