#!/usr/bin/python
import sys, os
import socket

import cv2
import numpy as np

cap = cv2.VideoCapture(0)

if (cap.isOpened() == False):
    print "Failed to Open OPEN"
    sys.exit()

try:

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1*1024*1024)
    sock.connect("/run/shm/pi2cv")
    
    while True:

        ret, img = cap.read()
        jpg = cv2.imencode('.jpeg', img)[1].tostring()

        sock.send(jpg)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print "Exception: " + str(e)

finally:
    print "Exiting"

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

