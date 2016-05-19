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

try:

    epoll = select.epoll()
    

    if os.path.exists( "/run/shm/pi2cv" ):
        os.remove( "/run/shm/pi2cv" )

    if os.path.exists( "/run/shm/flir2cv" ):
        os.remove( "/run/shm/flir2cv" )


    picam = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    picam.bind("/run/shm/pi2cv")
    epoll.register(picam.fileno(), select.EPOLLIN)

    flir = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    flir.bind("/run/shm/flir2cv")
    epoll.register(flir.fileno(), select.EPOLLIN)

    # alpha = 0.5
    # beta = ( 1.0 - alpha )
    # pi_cam_img = np.empty(0)
    # flir_img = np.empty(0)
    # dst = np.empty(0)
    
    while True:

        events = epoll.poll()

        for fileno, event in events:

            if (picam.fileno() == fileno):
                jpg = picam.recv(262144)
                nparr = np.fromstring(jpg, np.uint8)
                pi_cam_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                cv2.imshow( "PiCam", pi_cam_img );

            if (flir.fileno() == fileno):
                ir = flir.recv(262144)
                nparr = np.fromstring(ir, np.uint8)
                flir_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                cv2.imshow( "FLIR", flir_img );

        # if (pi_cam_img.size != 0 and flir_img.size != 0):
        #     cv2.addWeighted( flir_img, alpha, pi_cam_img, beta, 0.0, pi_cam_img);
        #     cv2.imshow( "Linear Blend", pi_cam_img );

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print "Exception: " + str(e)

finally:
    print "Exiting"