#!/usr/bin/python -u
import sys, os
import socket
from time import sleep

import cv2
import numpy as np

try:

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1*1024*1024)
    #print "SND Size: " + str(sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))
    sock.connect("/run/shm/pi2cv")

    with open('test_images/test_wc.jpg', 'r') as jpg_file:

        jpg = jpg_file.read()

        while True:

            sock.send(jpg)
            sleep(0.05)

except Exception as e:
    print "Exception: " + str(e)

finally:
    print "Exiting"


