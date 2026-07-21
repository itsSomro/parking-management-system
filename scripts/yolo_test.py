from ultralytics import YOLO
import cv2


model = YOLO(r"/runs/detect/plate_detector_v19/weights/best.pt")

image_path = r"/yolo_dataset/images/test/0b24d6ed-d32f-420d-bc18-03deece29073___2015-Maruti-Ciaz-Test-Drive-Review.jpg.jpeg"
results = model(image_path)

for result in results:
    annotated_image = result.plot()

    cv2.imshow("YOLO Detection", annotated_image)
    cv2.waitKey(0)

cv2.destroyAllWindows()