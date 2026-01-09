#Find coordinates and BGR color code of pixel in an image or video
import cv2
import numpy as np

while True:
    ans=input("Quer medir uma imagem ou video?(i/v) (q) para sair:").strip().lower()
    if ans == "i":
        # Load an actual image
        img_name= input("Qual o nome da imagem a ser medida?(sem extensão):").strip()
        img_ext= [".jpg",".jpeg",".png"]
        img_file =f"/home/cobrascott/Documents/Python/Images/{img_name}" #Address to your image folder
        img_path=None

        for ext in img_ext:
            try:
                with open(img_file + ext, "rb") as f:  # Check if file exists
                    img_path = img_file + ext
                    break  # Stop when the first valid image is found
            except FileNotFoundError:
                continue  # Try the next extension

        img = cv2.imread(img_path)  

        if img is None:
            print("Error: Image not found!")
            exit()

        # Add extra space at the bottom for text
        extra_space = 50  # Height for text display
        img_with_space = np.vstack([img, np.full((extra_space, img.shape[1], 3), 255, dtype=np.uint8)])

        def mouse_event(event, x, y, flags, param,):
            if event == cv2.EVENT_MOUSEMOVE:  # Update position dynamically as you move the mouse
                img_display = img_with_space.copy()
                if 0 <= y <= img.shape[0] and 0 <= x <= img.shape[1]: #make sure the pixel is within the image
                    b,g,r = img[y,x] #request bgr color code from numpy array

                cv2.rectangle(img_display, (0, img.shape[0]), (img.shape[1], img.shape[0] + extra_space), (255, 255, 255), -1)  # Clear text area
                cv2.putText(img_display, f"X: {x}, Y: {y}, BGR: ({b}, {g}, {r})", (10, img.shape[0] + 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                cv2.imshow("Image", img_display)

        cv2.imshow("Image", img_with_space)
        cv2.setMouseCallback("Image", mouse_event)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        break
    if ans == "v":
        cap =cv2.VideoCapture(0) #Use 0 for webcam or replace with video file path
        if not cap.isOpened():
            print("Erro: Video não detectado!")
            exit()
        def mouse_event(event,x,y, flags, param):
            global mouse_x, mouse_y
            if event == cv2.EVENT_MOUSEMOVE:
                mouse_x, mouse_y = x, y
        
        mouse_x , mouse_y = 0, 0
        cv2.namedWindow("Video")
        cv2.setMouseCallback("Video", mouse_event)
        while True:
            ret, frame =cap.read()
            if not ret: #if no frame is captured, ....
                break 
            b, g, r = frame[mouse_y, mouse_x] 
            cv2.putText(frame, f"X:{mouse_x}, Y:{mouse_y}, BGR: ({b}, {g}, {r})", (10,30),
                        cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)
            cv2.imshow("Video", frame)
            if cv2.waitKey(1) & 0xFF== ord("q"):
                break
        cap.release()
        cv2.destroyAllWindows
        break
    if ans == "q":
        break
    else:
        print("Resposta inválida! Responda apenas i para imagem ou v para video")
    