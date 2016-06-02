#!/usr/bin/python

import socket

# from random import randint
from time import sleep

import numpy as np

if __name__ == "__main__":

    width = 80
    height = 60
    max_val = 0
    freq = 10

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.connect("/run/shm/flir2cv")

    try:
        while True:

            data = np.random.randint(256, size=width*height).astype('uint8')
            sock.send(data)

            sleep(1.0/freq)

    except:
        print "Exiting"
