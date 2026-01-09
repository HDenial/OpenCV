#simple video capture
import cv2

# Use the correct device ID (check with ls /dev/video*)
device_id = 0  # Change if necessary, e.g., /dev/video1

# Open the camera with Video4Linux2 backend for low latency
cap = cv2.VideoCapture(device_id, cv2.CAP_V4L2)

# Set resolution (adjust as needed)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Reduce resolution for faster processing
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 60)  # High FPS for low latency
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # Use MJPEG if supported

if not cap.isOpened():
    print("Camera not detected!")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    cv2.imshow("Low Latency Video", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()