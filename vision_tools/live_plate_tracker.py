import cv2
import easyocr
from ultralytics import YOLO
import re
import os

# --------------------------------------------------------------------------
# 1. SETUP & INITIALIZATION
URL = "http://username:password@192.168.1.X:8080/video"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "best.pt")

yolo_model = YOLO(MODEL_PATH)
ocr_reader = easyocr.Reader(['en'], gpu=True)

successfully_logged_ids = set()

# --------------------------------------------------------------------------
# 2. HELPER FUNCTIONS (Confusion Matrix & Compliance Filter)
def license_complies_format(text):
    letter_to_number = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'T': '1', 'Z': '2', 'J': '3', 'S': '5',
                        'G': '6', 'B': '8'}
    number_to_letter = {'8': 'B', '0': 'O', '1': 'I', '5': 'S', '2': 'Z', '6': 'G', '3': 'J', '4': 'L'}

    # print(f"DEBUG: RAW TEXT: {text}")
    text = text.upper()

    # SWAPS VERTICAL SYMBOLS TO '1' - COMMON OCR PROBLEM
    symbol_to_one = ['|', '\\', '/', '!', ']', '[']
    for symbol in symbol_to_one:
        text = text.replace(symbol, '1')


    text = re.sub(r'[^A-Z0-9]', '', text)
    clean_text = list(text)
    # print(f"DEBUG: CLEAN TEXT: {clean_text}")

    if len(clean_text) < 9:
        return None
    if len(clean_text) == 9:
        start, mid, end = 4, 5, 9
    elif len(clean_text) == 10:
        start, mid, end = 4, 6, 10
    else:  # len > 10
        return None

    # 1. State Code (Letters)
    for i in range(0, 2):
        letter = clean_text[i]
        if letter in number_to_letter:
            clean_text[i] = number_to_letter[letter]

    # 2. RTO Code (Numbers)
    for i in range(2, 4):
        number = clean_text[i]
        if number in letter_to_number:
            clean_text[i] = letter_to_number[number]

    # 3. Series Code (Letters)
    for i in range(start, mid):
        letter = clean_text[i]
        if letter in number_to_letter:
            clean_text[i] = number_to_letter[letter]

    # 4. Tail Digits (Numbers)
    for i in range(mid, end):
        number = clean_text[i]
        if number in letter_to_number:
            clean_text[i] = letter_to_number[number]

    result_str = "".join(clean_text)

    # FINAL SAFETY CHECK
    # Ensure state/series slots are strictly letters and RTO/tail slots are strictly numbers
    state_valid = result_str[0:2].isalpha()
    rto_valid = result_str[2:4].isdigit()
    series_valid = result_str[start:mid].isalpha()
    tail_valid = result_str[mid:end].isdigit()

    if state_valid and rto_valid and series_valid and tail_valid:
        return result_str

    return None

# --------------------------------------------------------------------------
# 3. MAIN STREAMING & TRACKING LOOP
cap = cv2.VideoCapture(URL)

if not cap.isOpened():
    print("[!] Error: Unable to open camera stream.")
    exit()

print("Live Parking System Active... Press 'q' to stop.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("[!] Error: Stream disconnected or lost frame.")
        break

    results = yolo_model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False)[0]

    if results.boxes is not None and results.boxes.id is not None:
        boxes = results.boxes.xyxy.cpu().numpy()
        track_ids = results.boxes.id.int().cpu().numpy()

        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = map(int, box)


            # Draw tracking bounding box on main feed
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


            # --------------------------------------------------------------
            # MEMORY CHECK: Skip heavy OCR processing if already logged
            if track_id in successfully_logged_ids:
                cv2.putText(frame, "LOGGED", (x1, y2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                continue


            # Cropping with Padding
            img_h, img_w, _ = frame.shape
            px1, py1 = max(0, x1 - 10), max(0, y1 - 5)
            px2, py2 = min(img_w, x2 + 10), min(img_h, y2 + 5)
            cropped_plate = frame[py1:py2, px1:px2]

            if cropped_plate.size == 0:
                continue


            # Upscaling crop using Cubic Interpolation
            resized_plate = cv2.resize(cropped_plate, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)


            # Running EasyOCR
            ocr_results = ocr_reader.readtext(resized_plate, detail=1)


            if len(ocr_results) > 0:
                # Sorts left-to-right
                ocr_results = sorted(ocr_results, key=lambda r: r[0][0][0])
                raw_text = "".join([res[1] for res in ocr_results])
                clean_text = raw_text.replace(" ", "").upper()


                # Applying confusion matrix & format check
                validated_plate = license_complies_format(clean_text)


                # SUCCESS: Valid Plate Found!
                if validated_plate is not None:
                    print(f"\n==========================================")
                    print(f"[SUCCESS] Vehicle Registered: {validated_plate}")
                    print(f"[TRACKER] Assigned ID #{track_id}")
                    print(f"==========================================\n")

                    # Lock ID in memory so OCR doesn't run again for this car
                    successfully_logged_ids.add(track_id)


    display_frame = cv2.resize(frame, (1080, 608))
    cv2.imshow("Live Parking Gate Feed - Tracking Engine", display_frame)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
