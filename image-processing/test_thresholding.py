#import required modules
from __future__ import print_function
import cv2
import numpy as np
#import argparse

#==========Arbitrary image load based on absolute filepath===========#
#====================================================================#
#ap = argparse.ArgumentParser()
#ap.add_argument("-i", "--image", help = "Absolute filepath to image")
#args = vars(ap.parse())

#image = cv2.imread(args["image"])
#====================================================================#


#=====================Define capture device==========================#
cap = cv2.VideoCapture(0)
while(True):
    ret, frame = cap.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #ret, gray = cv2.threshold(gray, 127, 255,cv2.THRESH_BINARY)
    gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,11,2)


    cv2.imshow('frame', gray)

    if cv2.waitKey(1) & 0xFF == ord('q'):
                break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()


#====================Define colour boundaries========================#
#====================================================================#


#====================================================================#



