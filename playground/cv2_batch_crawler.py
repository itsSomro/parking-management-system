import os
import cv2
import imutils
import numpy as np

DATASET_ROOT_PATH = r"/State-wise_OLX"
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png")

# ----------------- AUTO CANNY -----------------
def auto_canny(image, sigma=0.33):
    # Sets Canny threshold based on image brightness automatically
    v = np.median(image)
    # v -> median of pixel intensity used as a baseline brightness
    lower = int(max(0, (1.0 - sigma) * v))      # sets lower limit threshold for canny
    upper = int(max(255, (1.0 + sigma) * v))        # sets upper limit threshold for canny

    return cv2.Canny(image, lower, upper)


# ----------------- PLATE DETECTION LOGIC -----------------
def detect_plate(image_path):
    original = cv2.imread(image_path)
    if original is None:
        print(f"❌ Could not load {image_path}")
        return

    # 1. RE-SIZING to 600 width for brush sizes to work on all images
    image = imutils.resize(original, width=600)

    # 2. PRE-PROCESSING
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    bfilter = cv2.bilateralFilter(gray, 11, 17, 17)

    # 2.1 AUTO-EDGE DETECTION
    edged = auto_canny(bfilter)

    # 3. DYNAMIC SEARCH
    candidates = []

    # Pass 1: Rectangle Glue (for single line number plates)
    brush_rect = cv2.getStructuringElement(cv2.MORPH_RECT, (10,3))
    # Pass 2: Square Glue (for double line number plates)
    brush_sq = cv2.getStructuringElement(cv2.MORPH_RECT, (4,4))

    for brush_type, brush in [("Rectangle", brush_rect), ("Square", brush_sq)]:
        dilated = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, brush)

        contours, _ = cv2.findContours(dilated.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        for contour in contours:
            # GEOMETRY CHECK
            (x,y,w,h) = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            area = cv2.contourArea(contour)

            # FILTERING SETTINGS:
            # 1. Aspect Ratio: Between 2.0 to 6.0
            # 2. Area: > 1000 after resize
            if 2.0 <= aspect_ratio >= 6.0 and area > 1000:
                #SOLIDITY CHECK
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                if hull_area > 0:
                    solidity = area / float(hull_area)
                else:
                    solidity = 0

                if solidity > 0.4:
                    candidates.append((contour, area, aspect_ratio))

    # SELECTION OF THE BEST CANDIDATE
    if candidates:
        #Sorting by Area (Big to Small)
        candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
        best_contour = candidates[0][0]

        #Calculating scale ratio
        ratio = original.shape[1] / 600.0
        best_contour = best_contour.astype("float")
        best_contour *= ratio
        best_contour = best_contour.astype("int")

        result_image = original.copy()
        cv2.drawContours(result_image, [best_contour], -1, (0,255,0), 3)

        return result_image

    else:
        return None


# ----------------- DATASET CRAWLER -----------------
print(f"📂 Scanning: {DATASET_ROOT_PATH}")

count = 0
found = 0

for root, dirs, files in os.walk(DATASET_ROOT_PATH):
    for file in files:
        # FILTERING image files only
        if file.lower().endswith(VALID_EXTENSIONS):

            full_path = os.path.join(root,file)
            print(f"Processing: {file}...", end="")

            result = detect_plate(full_path)

            if result is not None:
                print("✅ Found")
                found += 1

                cv2.imshow("Result (Press 'q' to quit, any key for next)", imutils.resize(result, width=800))

                key = cv2.waitKey(0)
                if key == ord('q'):
                    print("Exiting...")
                    exit()
            else:
                print("❌ Failed")

            count += 1

            print(f"\n🎉 Finished! Processed {count} images. Found plates in {found}.")
            cv2.destroyAllWindows()


