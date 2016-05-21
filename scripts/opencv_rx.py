#!/usr/bin/python
import sys, os
import socket, select

from timeit import default_timer as timer

import cv2
import numpy as np

# frames = 0
# start = 0
# if (start == 0): 
#     start = timer    
#     end = timer()
#     time = (end - start)

combined_img = np.zeros((480,640,4), np.uint8)

try:

    epoll = select.epoll()

    nodejs = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    nodejs.connect("/run/shm/cv2node")
    
    if os.path.exists( "/run/shm/pi2cv" ):
        os.remove( "/run/shm/pi2cv" )
    
    picam = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    picam.bind("/run/shm/pi2cv")
    epoll.register(picam.fileno(), select.EPOLLIN)

    if os.path.exists( "/run/shm/flir2cv" ):
        os.remove( "/run/shm/flir2cv" )

    flir = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    flir.bind("/run/shm/flir2cv")
    epoll.register(flir.fileno(), select.EPOLLIN)

    nodejs.send("HELLO WORLD")

    while True:

        events = epoll.poll()

        for fileno, event in events:

            if (picam.fileno() == fileno):
                jpg = picam.recv(262144)
                nparr = np.fromstring(jpg, np.uint8)
                pi_cam_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                # cv2.imshow( "PiCam", pi_cam_img );

                combined_img[:,:,0:3] = pi_cam_img

            if (flir.fileno() == fileno):
                ir = flir.recv(262144)
                nparr = np.fromstring(ir, np.uint8)
                flir_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                # cv2.imshow( "FLIR", flir_img );

                combined_img[0:60,0:80,3] = flir_img

            combined_img[0:60,0:80,0] = combined_img[0:60,0:80,3]
            combined_img[0:60,0:80,1] = combined_img[0:60,0:80,3]
            combined_img[0:60,0:80,2] = combined_img[0:60,0:80,3]
            cv2.imshow( "combined_img", combined_img ); 

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print "Exception: " + str(e)

finally:
    print "Exiting"