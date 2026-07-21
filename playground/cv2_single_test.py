import cv2
import imutils
from PIL import Image
import pytesseract

# image_path = "State-wise_OLX/MH/MH1.jpg"
image_path = "Datasets - LicensePlates/State-wise_OLX/AN/AN1.jpg"
#IMAGE PRE-PROCESSING
image = cv2.imread(image_path)
# image = imutils.resize(image, width = 600)
cv2.imshow("Original Image",image)

gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
cv2.imshow("Gray-Scale Image", gray_image)

bfilter_image = cv2.bilateralFilter(gray_image, 11, 17, 17)
cv2.imshow("Bilateral-Filter Image", bfilter_image)

edged_image = cv2.Canny(bfilter_image, 30, 150)
cv2.imshow("Canny Edges", edged_image)


#Dilating - removes white gaps by thickening lines
#Using a 3x3 brush
brush = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
dilated_edged_image = cv2.dilate(edged_image, brush, iterations=1)
cv2.imshow("Dilated Edges", dilated_edged_image)

#Using to close gaps incase the whole numberplate isn't detected
edge_closed_image = cv2.morphologyEx(edged_image, cv2.MORPH_CLOSE, brush)
cv2.imshow("Edge Closed Image", edge_closed_image)

# retrieves all shapes or contours in the image
contours, hierarchy = cv2.findContours(edge_closed_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#Sorting by area cause numberplate is usually biggest
contours = sorted(contours, key=cv2.contourArea, reverse=True)[:30]
debug_image = image.copy()
cv2.drawContours(debug_image, contours, -1, (0,255,0), 1)
cv2.imshow("All Contours Found", debug_image)
print(f"Total Contours found: {len(contours)}")

#FILTERING FOR NUMBERPLATE
plate_contour = None

for contour in contours:
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)

    if 4 <= len(approx) <= 8:
        (x,y,w,h) = cv2.boundingRect(approx)
        aspect_ratio = w / float(h)
        area = cv2.contourArea(contour)
        #Std Indian Plates are 4:1 ratio,accepting range from 2.0 to 6.0
        if 2.0 <= aspect_ratio <= 6.0:
            if  3000 > area > 1500:
                print(f" FOUND CANDIDATE! Area: {area} | Ratio: {aspect_ratio:.2f}")
                plate_contour = approx
                break

if plate_contour is not None:
    print(f" License Plate Found! Area: {cv2.contourArea(plate_contour)}")

    final_image = image.copy()
    cv2.drawContours(final_image, [plate_contour], -1, (0,255,0), 3)
    # (x, y, w, h) = cv2.boundingRect(plate_contour)
    # cv2.rectangle(final_image, (x, y), (x + w, y + h), (0, 0, 255), 3)
    cv2.imshow("Final Detected Plate", final_image)
    cv2.waitKey(0)

else:
    print("❌ No plate found.")

cv2.waitKey(0)


