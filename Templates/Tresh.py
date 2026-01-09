#primitive BnW
import cv2
import time

# Open video file or webcam (use 0 for webcam)
cap = cv2.VideoCapture(0) 

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
#out = cv2.VideoWriter('output.avi', fourcc, 20.0, (resized_width, resized_height), False)

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

    # Apply adaptive thresholding (CPU-only)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)

    # Show the output
    cv2.imshow("Thresholded Video (CUDA Grayscale)", thresh)

    # Save the thresholded frame
    #out.write(thresh)

    # FPS limit: Adjust to reduce CPU/GPU load
    elapsed_time = time.time() - start_time
    wait_time = max(1, int(1000 / fps - elapsed_time * 1000))  # Limit FPS processing
    if cv2.waitKey(wait_time) & 0xFF == ord('q'):
        break  # Press 'q' to exit

# Cleanup
cap.release()
#out.release()
cv2.destroyAllWindows()
