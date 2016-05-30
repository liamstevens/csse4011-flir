#!/usr/bin/python
import sys, os
import socket
from time import sleep

import cv2
import numpy as np

try:

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.connect("/run/shm/flir2cv")

    with open('test_images/test_ir.pgm', 'r') as flir_file:

        flir_str = flir_file.read()

        nparr = np.fromstring(flir_str, np.uint8)
        flir = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    
        while True:

            sock.send(flir)

            sleep(0.125)

except Exception as e:
    print "Exception: " + str(e)

finally:
    print "Exiting"


