#Crop out unnecessary parts of an image 
import cv2
import numpy as np

img= cv2.imread('/home/cobrascott/Documents/Python/Images/img.jpg')
#[yi:yf,xi:xf]
roi=img[30:630,170:495]

cv2.imshow("roi",roi)
cv2.imshow("Original",img)
cv2.waitKey(0)
