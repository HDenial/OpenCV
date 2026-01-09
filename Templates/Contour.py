#Create contours around objects

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

# Define VideoWriter if saving output
#fourcc = cv2.VideoWriter_fourcc(*'XVID')
#out = cv2.VideoWriter('output_contours_improved.avi', fourcc, 20.0, (resized_width, resized_height), False)

# Initialize CUDA GpuMat
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

    # Convert to grayscale (CUDA-accelerated)
    gpu_gray = cv2.cuda.cvtColor(gpu_frame, cv2.COLOR_BGR2GRAY)

    # Download grayscale image back to CPU
    gray = gpu_gray.download()

    # Apply Gaussian Blur (to reduce noise)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Adaptive Thresholding for better separation (last 2 values, the bigger, less detailed)
    adaptive_thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                           cv2.THRESH_BINARY, 21, 8)

    # Use Canny edge detection for more distinct edges(bigger values, less mixing)
    edges = cv2.Canny(adaptive_thresh, 100, 200)#100, 200

    # Apply dilation to connect close contours
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=1)

    # Find contours (use RETR_TREE to detect nested contours)
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Draw contours on the frame
    frame_with_contours = cv2.drawContours(frame.copy(), contours, -1, (0, 255, 0), 2)

    # Show the output
    cv2.imshow("Improved Contours", frame_with_contours)

    # Save the frame with contours
    #out.write(cv2.cvtColor(frame_with_contours, cv2.COLOR_BGR2GRAY))

    # FPS limit: Adjust to reduce CPU/GPU load
    elapsed_time = time.time() - start_time
    wait_time = max(1, int(1000 / fps - elapsed_time * 1000))  # Limit FPS processing
    if cv2.waitKey(wait_time) & 0xFF == ord('q'):
        break  # Press 'q' to exit

# Cleanup
cap.release()
#out.release()
cv2.destroyAllWindows()


    # Save the frame with contours
    #out.write(cv2.cvtColor(frame_with_contours, cv2.COLOR_BGR2GRAY))

    # FPS limit: Adjust to reduce CPU/GPU load
elapsed_time = time.time() - start_time
wait_time = max(1, int(1000 / fps - elapsed_time * 1000))  # Limit FPS processing
if cv2.waitKey(wait_time) & 0xFF == ord('q'):
    exit  # Press 'q' to exit

# Cleanup
cap.release()
#out.release()
cv2.destroyAllWindows()

