#Turn every color into either black or white (major white) requires CUDA acceleration

import cv2
import time
import numpy as np

# Open the video file or webcam (use 0 for webcam)
cap = cv2.VideoCapture(0)  # Replace with 0 for webcam

# Check if the video opened properly
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

# Get original frame width and height
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))

# Reduce resolution for performance
scale_factor = 0.5  # Adjust for speed vs. quality
resized_width = int(frame_width * scale_factor)
resized_height = int(frame_height * scale_factor)

gpu_frame = cv2.cuda_GpuMat()

while cap.isOpened():
    start_time = time.time()  # Measure processing time per frame

    ret, frame = cap.read()
    if not ret:
        break  # Exit loop if no more frames

    # Resize frame for performance
    frame = cv2.resize(frame, (resized_width, resized_height))
    # Upload frame to GPU
    gpu_frame.upload(frame)

    gpu_gray = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2GRAY)

    gray = gpu_gray.download()

    canny=cv2.Canny(gray,127,255)
    _,thresh=cv2.threshold(gray,127,255,cv2.THRESH_BINARY) #any pixel above 127 becomes white, below becomes black

    Addition=cv2.add(canny,thresh)
    cv2.imshow("addition",Addition)
    
    elapsed_time = time.time() - start_time
    wait_time = max(1, int(1000 / fps - elapsed_time * 1000))  # Limit FPS processing
    if cv2.waitKey(wait_time) & 0xFF == ord('q'):
        break  # Press 'q' to exit
cap.release()
cv2.destroyAllWindows()   
