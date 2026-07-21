import cv2


url = "http://username:password@192.168.1.X:8080/video"

print(f"Attempting to connect to: {url}")
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("[!] Error: Could not connect to the camera stream.")
    print("Check your Wi-Fi connection and the IP address.")
    exit()

print("Connection successful! Press 'q' to quit.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("[!] Failed to grab frame. Stream might have dropped.")
        break

    display_frame = cv2.resize(frame, (960, 540))
    cv2.imshow("Live Camera Feed", display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()