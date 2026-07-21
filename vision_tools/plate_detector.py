import cv2
import easyocr
from ultralytics import YOLO
import numpy as np
import re
import os


def nothing(x): pass
letter_to_number = {'O':'0', 'Q':'0', 'D':'0', 'I':'1', 'L':'1', 'T':'1','Z':'2', 'J':'3', 'S':'5', 'G':'6', 'B':'8'}
number_to_letter = {'8':'B', '0':'O', '1':'I', '5':'S', '2':'Z', '6':'G', '3':'J', '4':'L'}


def main():
    # --------------------------------------------------------------------------
    # 1. LOADING MODELS
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
    MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "best.pt")

    yolo_model = YOLO(MODEL_PATH)
    ocr_reader = easyocr.Reader(['en'], gpu=True)

    # --------------------------------------------------------------------------
    # 2. LOADING TEST DATA
    FOLDER_PATH = os.path.join(PROJECT_ROOT, "yolo_dataset", "images", "test")

    # --------------------------------------------------------------------------
    # 3. LOOPING THRU EVERY IMAGE
    cv2.namedWindow("Display Image", cv2.WINDOW_NORMAL)
    for file_name in os.listdir(FOLDER_PATH):
        img_path = os.path.join(FOLDER_PATH, file_name)
        image = cv2.imread(img_path)

        if image is None:
            continue

        display_image = image.copy() #to not overwrite on the original image
        # --------------------------------------------------------------------------
        # 4. DETECTING LICENSE PLATE (USING YOLO MODEL)
        yolo_result = yolo_model(image)[0]

        if len(yolo_result) == 0:
            print("[!] No License Plate Detected!")
            continue

        for box in yolo_result.boxes.xyxy:
            x1, y1, x2, y2 = box.cpu().numpy()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            pad_x = 10
            pad_y = 5
            img_h, img_w, _ = image.shape

            px1 = max(0, x1 - pad_x)
            py1 = max(0, y1 - pad_y)
            px2 = min(img_w, x2 + pad_x)
            py2 = min(img_h, y2 + pad_y)

            cropped_plate = image[py1:py2, px1:px2]
            cropped_plate = cv2.resize(cropped_plate, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            flat_plate = deskew_plate(cropped_plate)

            cv2.imshow("Flattened Plate", flat_plate)
            cv2.resizeWindow("Flattened Plate", 300, 100)

            # --------------------------------------------------------------------------
            # 5. PRE-PROCESSING PLATE IMG (FOR OCR READER)
            #Using AdaptiveThresholding instead of GlobalThresholding
            final_image = cv2.cvtColor(flat_plate, cv2.COLOR_BGR2GRAY)
            # final_image = cv2.adaptiveThreshold(gray_image,
            #                                     maxValue=255,
            #                                     adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            #                                     thresholdType=cv2.THRESH_BINARY_INV,
            #                                     blockSize=15,
            #                                     C=4)
            # cv2.imshow("PlateImage", final_image)

            # --------------------------------------------------------------------------
            # 6. READING THE FINAL IMG
            # (Using detail=1 gives us the bbox, text, and score)
            ocr_results = ocr_reader.readtext(final_image, detail=1, mag_ratio = 2)

            if len(ocr_results) > 0:
                ocr_results = sorted(ocr_results, key=lambda r: r[0][0][0])
                combined_raw_text = "".join([result[1] for result in ocr_results])
                clean_raw_text = combined_raw_text.replace(" ", "").upper()

                avg_score = sum([result[2] for result in ocr_results]) / len(ocr_results)

                validated_plate = license_complies_format(clean_raw_text)

                if validated_plate is not None:
                    print(f"[SUCCESS] Image: {img_path}")
                    print(f"          Raw OCR: {clean_raw_text}")
                    print(f"          Cleaned: {validated_plate}")
                    print(f"          Confidence: {avg_score:.2f}\n")

                    # --------------------------------------------------------------------------
                    # 7. OUTPUTTING IMG WITH DETECTED PLATE & CONFIDENCE SCORE
                    display_text = f"{validated_plate} ({avg_score:.2f})"

                    cv2.putText(display_image, display_text, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36,255,12), 2)

                    cv2.rectangle(display_image, (x1, y1), (x2, y2), (36, 255, 12), 2)

            cv2.imshow("Display Image", display_image)
            key = cv2.waitKey(0) & 0xFF
            if key == ord('q'):
                break


def license_complies_format(text):
    print(f"DEBUG: RAW TEXT: {text}")
    text = text.upper()
    text = re.sub(r'[^A-Z0-9]', '', text)
    clean_text = list(text)
    print(f"DEBUG: CLEAN TEXT: {clean_text}")

    if len(clean_text) < 9:
        return None
    if len(clean_text) == 9:
        start, mid, end = 4, 5, 9

    elif len(clean_text) == 10:
        start, mid, end = 4, 6, 10
    else: # len > 10
        return None

    for i in range(0,2):
        letter = clean_text[i]
        if letter in number_to_letter:
            clean_text[i] = number_to_letter[letter]

    for i in range(2,4):
        number = clean_text[i]
        if number in letter_to_number:
            clean_text[i] = letter_to_number[number]

    for i in range(start,mid):
        letter = clean_text[i]
        if letter in number_to_letter:
            clean_text[i] = number_to_letter[letter]

    for i in range(mid,end):
        number = clean_text[i]
        if number in letter_to_number:
            clean_text[i] = letter_to_number[number]

    return "".join(clean_text)


def tune_threshold(gray_image):
    cv2.namedWindow('PlateImage', cv2.WINDOW_NORMAL)
    cv2.createTrackbar('C', 'PlateImage', 2, 8, nothing)
    cv2.createTrackbar('BlockSize', 'PlateImage', 11, 21, nothing)
    cv2.resizeWindow('PlateImage', 600, 300)

    while True:
        current_val_c = cv2.getTrackbarPos('C', 'PlateImage')
        current_val_blocksize = cv2.getTrackbarPos('BlockSize', 'PlateImage')

        if current_val_blocksize % 2 == 0:
            current_val_blocksize += 1

        if current_val_blocksize < 3:
            current_val_blocksize = 3

        final_image = cv2.adaptiveThreshold(gray_image,
                                            maxValue=255,
                                            adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            thresholdType=cv2.THRESH_BINARY_INV,
                                            blockSize=current_val_blocksize,
                                            C=current_val_c)
        cv2.imshow("PlateImage", final_image)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    cv2.destroyAllWindows()


def order_points(pts):
    rect = np.zeros((4,2), dtype='float32')

    s = pts.sum(axis=1)
    # Sum of (x, y) coordinates:
    # Top-Left has the smallest sum, Bottom-Right has the largest
    rect[0] = pts[np.argmin(s)] #tl
    rect[2] = pts[np.argmax(s)] #br

    # Difference of (y - x):
    # Top-Right has the smallest diff, Bottom-Left has the largest
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] #tr
    rect[3] = pts[np.argmax(diff)] #bl

    return rect


def deskew_plate(cropped_plate):
    gray = cv2.cvtColor(cropped_plate, cv2.COLOR_BGR2GRAY)
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17)
    edged = cv2.Canny(bfilter, 30, 200)

    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    plate_contour = None

    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if len(approx) == 4:
            plate_contour = approx
            break

    if plate_contour is None:
        return cropped_plate

    pts = plate_contour.reshape(4,2)
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0,0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype = "float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    flat_plate = cv2.warpPerspective(cropped_plate, M, (maxWidth, maxHeight))

    return flat_plate


if __name__ == "__main__":
    main()