#draw shapes on image, and highlight region of interest

import cv2
import numpy as np


#draws circle with x,y center and r radius
def circle(img):
    center= (200,75)
    radius= 45
    color=(0,0,255)
    masked_img=cv2.circle(img,center,radius,color,2)
    return masked_img
#draws rectangle with x1,y1 corner and x2,y2 corner
def rectangle(img):
    pt1=(180,480)#input("canto superior direito(x,y):").strip().lower()
    pt2=(490,550)#input("canto inferior esquerdo(x,y):").strip().lower()
    color= (0,255,0)
    #color_code = input("Blue, Red or Green?(B,G,R)").strip().lower()
    #if color_code == "b":
        #color=(255,0,0)
    #if color_code == "g":
        #color=(0,255,0)
    #if color_code == "r":
        #color=(0,0,255)

    masked_img=cv2.rectangle(img,pt1,pt2,color,2)
    return masked_img
#polygons
def roi(img):
    height = img.shape[0]  # Get the height (number of rows) of the image 0 == height 1 == width
    polygons = np.array([[(180, 550), (180, 480), (490, 480), (490, 550)]])  # Define a polygon (region of interest)
    mask = np.zeros_like(img)  # Create a black mask of the same size as the image
    cv2.fillPoly(mask, polygons, (255,0,0))  # Fill the polygon region in the mask with given color, white for original (255,255,255)
    masked_img = cv2.bitwise_and(img, mask)  # Apply the mask to the image (keeping only the region of interest)
    return masked_img  # Return the masked image


img_og = cv2.imread("/home/cobrascott/Documents/Python/Images/img.jpg")
img_mod=img_og.copy()
final=roi(img_mod)
img_mod=img_og.copy()
rec=rectangle(img_mod)
img_mod=img_og.copy()
circ=circle(img_mod)

cv2.imshow("image original",img_og)
cv2.imshow("image rectangled",rec)
cv2.imshow("image circled",circ)
cv2.imshow("image modified",final)
cv2.waitKey(0)
