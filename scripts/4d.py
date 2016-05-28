#!/usr/bin/python
import sys, os
import socket, select

from timeit import default_timer as timer

import cv2
import numpy as np

combined_img = np.zeros((480,640,4), np.uint8)

try:

    jpg = picam.recv(262144)
    nparr = np.fromstring(jpg, np.uint8)
    pi_cam_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Store PiCam Image in BGR channels of the combined image
    combined_img[:,:,0:3] = pi_cam_img

    ir = flir.recv(262144)
    nparr = np.fromstring(ir, np.uint8)
    flir_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

    # Store the flir image in the A channel of the combined image
    combined_img[0:60,0:80,3] = flir_img

    # Copy the FLIR data into the BGR channels    
    combined_img[0:60,0:80,0] = combined_img[0:60,0:80,3]
    combined_img[0:60,0:80,1] = combined_img[0:60,0:80,3]
    combined_img[0:60,0:80,2] = combined_img[0:60,0:80,3]
    cv2.imshow( "combined_img", combined_img ); 

except Exception as e:
    print "Exception: " + str(e)

finally:
    print "Exiting"