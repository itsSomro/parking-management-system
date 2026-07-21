from torch.cuda import device
from ultralytics import YOLO
import os


if __name__ == '__main__':
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
    MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "yolov8n.pt")

    model = YOLO(MODEL_PATH)

    print("Starting YOLO Custom Training...")

    model.train(
        data="data.yaml",
        epochs=30,
        imgsz=640,  # Standard resolution for YOLO
        batch=8,
        name="plate_detector_v1",  # Folder name where new weights will be saved
        device=0,
        workers=2
    )

    print("Training complete!")