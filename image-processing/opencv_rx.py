#!/usr/bin/python -u

import sys, os
import socket, select

import calendar, time

import cv2
import numpy as np

import face_test as ft

from PIL import Image

# 
# pi_cam_img = np.zeros((480,640,3), np.uint8)
# flir_img = np.zeros((60,80,1), np.uint8)

epoll = select.epoll()
cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

socket_buf_size = 1*1024*1024

# GLOBAL CONFIGURABLES
save_file_enable = False
multiple_faces = True
colorize = True
output_view = 1

def main():
    
    picam_ready = 0
    flir_ready = 0

    jpg = []
    pgm = []

    cv2.setNumThreads(3)

    try:

        node_tx = uds_connect("/run/shm/cv2node")

        node_rx = uds_bind("/run/shm/node2cv")

        picam_rx = uds_bind("/run/shm/pi2cv")

        flir_rx = uds_bind("/run/shm/flir2cv")

        while True:

            events = epoll.poll()

            for fileno, event in events:

                if (picam_rx.fileno() == fileno):
                    jpg = picam_rx.recv(socket_buf_size)
                    picam_ready = 1

                if (flir_rx.fileno() == fileno):
                    pgm = flir_rx.recv(socket_buf_size)
                    flir_ready = 1

                if (node_rx.fileno() == fileno):
                    cmd = node_rx.recv(socket_buf_size)
                    handle_cmd(cmd)

            if (picam_ready != 1 or flir_ready != 1):
                continue

            nparr = np.fromstring(jpg, np.uint8)
            pi_cam_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            nparr = np.fromstring(pgm, np.uint8)
            flir_img = np.reshape(nparr, (60, 80))

            combined_img, detections = do_processing(pi_cam_img, flir_img)
            out_img = do_output(combined_img, detections)

            node_tx.send(out_img)

            picam_ready = 0
            flir_ready = 0

    except Exception as e:
        print "Exception: " + str(e)

    finally:
        print "Exiting"

def handle_cmd(cmd):

    global output_view
    global colorize
    global multiple_faces

    print "Got Command: " + cmd

    if (cmd[0] != '!'):
        print "Invalid Format"
        return

    if (cmd[1] == 'V'):
        output_view = int(cmd[2])
        print "Output view is now: " + str(output_view)

    elif (cmd[1] == 'C'):
        colorize = int(cmd[2])
        print "Colorize flir is now: " + str(colorize)

    elif (cmd[1] == 'M'):
        multiple_faces = int(cmd[2])
        print "Multiple faces is now: " + str(multiple_faces)


def uds_bind(path):

    global epoll
    global socket_buf_size

    if os.path.exists( path ):
        os.remove( path )

    sock = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    sock.bind(path)
    sock.setblocking(0)
    epoll.register(sock.fileno(), select.EPOLLIN)

    return sock

def uds_connect(path):

    global socket_buf_size

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,socket_buf_size)
    sock.connect(path)
    return sock


def do_processing(image1, image2):

    # TODO: Crop image1 to smaller size to match 

    combined_img = np.zeros((image1.shape[0],image1.shape[1],4), np.uint8)

    # cv2.mixChannels( [image1, image2], [combined_img], [0,0, 1,1, 2,2, 3,3] )
    combined_img[:,:,0:3] = image1
    combined_img[0:60,0:80,3] = image2

    detections = ft.face_cascade(cascade, combined_img, False)

    if (multiple_faces == False and len(detections) > 1 ):
        detections = detections[0]

    return (combined_img, detections)

jpg_quality = 95
frame = -1
directory = "out_data/"+time.strftime("%Y%m%d-%H%M%S")
def do_output(image, detections):

    global jpg_quality
    global frame

    result_image = np.zeros((image.shape[0],image.shape[1],3), np.uint8)

    rgb_component = np.zeros((image.shape[0],image.shape[1],3), np.uint8)
    ir_component = np.zeros((image.shape[0],image.shape[1],3), np.uint8)

    cv2.mixChannels( [image], [rgb_component, ir_component], [0,0, 1,1, 2,2, 3,3, 3,4, 3,5] )

    frame = frame + 1

    if (save_file_enable == True):

        if (frame == 0):
            os.makedirs(directory+"/cam/")
            os.makedirs(directory+"/flir/")

        # Write image1 to file
        cv2.imwrite(directory+"/cam/"+str(frame)+".jpg", rgb_component)
        # Write image2 to file
        cv2.imwrite(directory+"/flir/"+str(frame)+".pgm", ir_component)


    if (colorize == 1):
        ir_component = cv2.LUT(ir_component, LUT)


    # Do transformation on incoming image
    if (output_view == 2):
        result_image = rgb_component

    elif (output_view == 1):
        result_image = ir_component

    elif (output_view == 0):
        # No Video, leave result image as all black
        pass
    else:
        result_image = cv2.addWeighted(rgb_component, 0.3, ir_component, 0.7,  0)

    if (output_view != 0):
        ft.detections_draw(result_image, detections)

    out_img = cv2.imencode('.jpeg', result_image,  [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality])[1].tostring()

    if (len(out_img) > 58000):
        if (jpg_quality > 0):
            jpg_quality = jpg_quality - 1
    else:
        if (jpg_quality < 95):
            jpg_quality = jpg_quality + 1

    return out_img

def colorize_flir(flir_img):

    return 

LUT = [0,0,0,16,0,0,33,0,0,42,0,0,49,0,0,56,0,0,63,0,0,70,0,0,77,0,0,83,0,0,87,0,1,91,0,2,95,0,3,99,0,4,103,0,5,106,0,7,110,0,9,115,0,11,116,0,12,118,0,13,120,0,16,122,0,19,124,0,22,127,0,25,129,0,28,131,0,31,133,0,34,135,0,38,137,0,42,138,0,45,140,0,48,141,0,52,143,0,55,144,0,58,146,0,61,147,0,63,148,0,65,149,0,68,149,0,71,150,0,74,150,0,76,151,0,79,151,0,82,152,0,85,152,0,88,153,0,92,154,0,94,155,0,97,155,0,101,155,0,104,155,0,107,156,0,110,156,0,112,156,0,114,157,0,117,157,0,121,157,0,124,157,0,126,157,0,129,157,0,132,157,0,135,157,0,137,156,0,140,156,0,143,155,0,146,155,0,149,155,0,152,155,0,154,155,0,157,155,0,159,155,0,161,154,0,164,154,0,166,153,0,168,153,0,170,152,0,172,152,0,174,151,1,175,151,1,177,150,1,178,149,1,180,149,2,182,149,3,183,148,4,185,147,4,186,147,5,188,146,5,189,146,5,190,145,6,191,144,7,192,143,9,193,142,10,194,141,11,195,139,12,197,138,13,198,136,15,200,134,17,201,133,18,202,131,20,203,129,21,204,126,23,206,123,24,207,121,26,208,118,27,208,116,28,209,113,30,210,111,32,211,108,34,212,104,36,213,101,38,214,98,40,216,95,42,217,91,44,218,87,46,219,81,47,220,76,49,221,70,51,222,65,53,223,59,54,223,54,56,224,48,57,224,42,59,225,37,61,226,31,63,227,28,65,228,25,67,228,23,69,229,21,71,230,19,72,231,17,74,231,15,76,232,13,77,233,11,78,234,10,80,234,9,82,235,8,84,235,8,86,236,7,87,236,7,89,236,6,91,237,5,92,237,4,94,238,4,95,238,3,97,239,3,99,239,3,100,240,3,102,240,2,103,241,2,104,241,1,106,241,1,107,241,1,109,242,1,111,242,1,113,243,0,114,243,0,115,243,0,117,244,0,119,244,0,121,244,0,124,244,0,126,245,0,128,245,0,129,246,0,131,246,0,133,247,0,134,247,0,136,248,0,137,248,0,139,248,0,140,248,0,142,249,0,143,249,0,144,249,0,146,249,0,148,249,0,150,250,0,153,250,0,155,251,0,157,251,0,159,252,0,161,252,0,163,253,0,166,253,0,168,253,0,170,253,0,172,253,0,174,253,0,176,254,0,177,254,0,178,254,0,181,254,0,183,254,0,185,254,0,186,254,0,188,254,0,190,254,0,191,254,0,193,254,0,195,254,0,197,254,0,199,254,0,200,254,1,202,254,1,203,254,2,205,254,3,206,254,4,207,254,6,209,254,8,211,254,10,213,254,11,215,254,12,216,254,14,218,254,16,219,255,20,220,255,24,221,255,28,222,255,32,224,255,36,225,255,39,227,255,44,228,255,50,229,255,56,230,255,62,231,255,67,233,255,73,234,255,79,236,255,85,237,255,92,238,255,98,238,255,105,239,255,111,240,255,119,241,255,127,241,255,135,242,255,142,243,255,149,244,255,156,244,255,164,245,255,171,245,255,178,246,255,184,247,255,190,247,255,195,248,255,201,248,255,206,249,255,212,250,255,218,251,255,224,252,255,229,253,255,235,253,255,240,254,255,244,254,255,249,255,255,252,255,255,255,255,255]
LUT = np.array(LUT, np.uint8)
LUT = np.reshape(LUT, (256, 1, 3))

if __name__ == "__main__":

    sys.exit(main())


# Increase Buffer sizes?
# https://www.raspberrypi.org/forums/viewtopic.php?f=81&t=106052
