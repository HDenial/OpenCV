#detect and highlight green objects in webcam feed

import cv2
import numpy as np


#webcam start
cap = cv2.VideoCapture(0)


#video Properties
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

while True:
    #captures frame by frame
    ret,frame=cap.read()

    if not ret:
        print("ERROR: video could not be captured!")
        break

    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV) #define color space
    lower_green= np.array([40,50,50]) #define lower limit of green color in HSV
    upper_green= np.array([80,255,255]) #define upper limit of green color in HSV

    mask= cv2.inRange(hsv,lower_green,upper_green)

    contours,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        area=cv2.contourArea(contour)
        print (area)
        if area > 500: #filter out small contours
            x,y,w,h=cv2.boundingRect(contour) #Get bounding rectangles for each contour

            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,0),2)#Draw a black rectangle around any green region detected

            cv2.putText(frame,"Verde",(x,y-10),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,0),5)

    cv2.imshow("cam",frame)
    cv2.imshow("mask",mask)
    if cv2.waitKey(10) & 0xFF==ord("q"):
        break
    
cap.release()
cv2.destroyAllWindows()