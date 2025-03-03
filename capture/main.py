import socket
import sys
import os
import time
import numpy
import threading
import cv2
import picamera
import picamera.array
import time
import thread

from PIL import Image, ImageOps, ImageEnhance, ImageFont, ImageDraw
from multiprocessing import Process, Queue

def make_linear_ramp():
    # putpalette expects [r,g,b,r,g,b,...]
    ramp = [
    0,0,0,
    0,0,16,
    0,0,33,
    0,0,42,
    0,0,49,
    0,0,56,
    0,0,63,
    0,0,70,
    0,0,77,
    0,0,83,
    1,0,87,
    2,0,91,
    3,0,95,
    4,0,99,
    5,0,103,
    7,0,106,
    9,0,110,
    11,0,115,
    12,0,116,
    13,0,118,
    16,0,120,
    19,0,122,
    22,0,124,
    25,0,127,
    28,0,129,
    31,0,131,
    34,0,133,
    38,0,135,
    42,0,137,
    45,0,138,
    48,0,140,
    52,0,141,
    55,0,143,
    58,0,144,
    61,0,146,
    63,0,147,
    65,0,148,
    68,0,149,
    71,0,149,
    74,0,150,
    76,0,150,
    79,0,151,
    82,0,151,
    85,0,152,
    88,0,152,
    92,0,153,
    94,0,154,
    97,0,155,
    101,0,155,
    104,0,155,
    107,0,155,
    110,0,156,
    112,0,156,
    114,0,156,
    117,0,157,
    121,0,157,
    124,0,157,
    126,0,157,
    129,0,157,
    132,0,157,
    135,0,157,
    137,0,157,
    140,0,156,
    143,0,156,
    146,0,155,
    149,0,155,
    152,0,155,
    154,0,155,
    157,0,155,
    159,0,155,
    161,0,155,
    164,0,154,
    166,0,154,
    168,0,153,
    170,0,153,
    172,0,152,
    174,0,152,
    175,1,151,
    177,1,151,
    178,1,150,
    180,1,149,
    182,2,149,
    183,3,149,
    185,4,148,
    186,4,147,
    188,5,147,
    189,5,146,
    190,5,146,
    191,6,145,
    192,7,144,
    193,9,143,
    194,10,142,
    195,11,141,
    197,12,139,
    198,13,138,
    200,15,136,
    201,17,134,
    202,18,133,
    203,20,131,
    204,21,129,
    206,23,126,
    207,24,123,
    208,26,121,
    208,27,118,
    209,28,116,
    210,30,113,
    211,32,111,
    212,34,108,
    213,36,104,
    214,38,101,
    216,40,98,
    217,42,95,
    218,44,91,
    219,46,87,
    220,47,81,
    221,49,76,
    222,51,70,
    223,53,65,
    223,54,59,
    224,56,54,
    224,57,48,
    225,59,42,
    226,61,37,
    227,63,31,
    228,65,28,
    228,67,25,
    229,69,23,
    230,71,21,
    231,72,19,
    231,74,17,
    232,76,15,
    233,77,13,
    234,78,11,
    234,80,10,
    235,82,9,
    235,84,8,
    236,86,8,
    236,87,7,
    236,89,7,
    237,91,6,
    237,92,5,
    238,94,4,
    238,95,4,
    239,97,3,
    239,99,3,
    240,100,3,
    240,102,3,
    241,103,2,
    241,104,2,
    241,106,1,
    241,107,1,
    242,109,1,
    242,111,1,
    243,113,1,
    243,114,0,
    243,115,0,
    244,117,0,
    244,119,0,
    244,121,0,
    244,124,0,
    245,126,0,
    245,128,0,
    246,129,0,
    246,131,0,
    247,133,0,
    247,134,0,
    248,136,0,
    248,137,0,
    248,139,0,
    248,140,0,
    249,142,0,
    249,143,0,
    249,144,0,
    249,146,0,
    249,148,0,
    250,150,0,
    250,153,0,
    251,155,0,
    251,157,0,
    252,159,0,
    252,161,0,
    253,163,0,
    253,166,0,
    253,168,0,
    253,170,0,
    253,172,0,
    253,174,0,
    254,176,0,
    254,177,0,
    254,178,0,
    254,181,0,
    254,183,0,
    254,185,0,
    254,186,0,
    254,188,0,
    254,190,0,
    254,191,0,
    254,193,0,
    254,195,0,
    254,197,0,
    254,199,0,
    254,200,0,
    254,202,1,
    254,203,1,
    254,205,2,
    254,206,3,
    254,207,4,
    254,209,6,
    254,211,8,
    254,213,10,
    254,215,11,
    254,216,12,
    254,218,14,
    255,219,16,
    255,220,20,
    255,221,24,
    255,222,28,
    255,224,32,
    255,225,36,
    255,227,39,
    255,228,44,
    255,229,50,
    255,230,56,
    255,231,62,
    255,233,67,
    255,234,73,
    255,236,79,
    255,237,85,
    255,238,92,
    255,238,98,
    255,239,105,
    255,240,111,
    255,241,119,
    255,241,127,
    255,242,135,
    255,243,142,
    255,244,149,
    255,244,156,
    255,245,164,
    255,245,171,
    255,246,178,
    255,247,184,
    255,247,190,
    255,248,195,
    255,248,201,
    255,249,206,
    255,250,212,
    255,251,218,
    255,252,224,
    255,253,229,
    255,253,235,
    255,254,240,
    255,254,244,
    255,255,249,
    255,255,252,
    255,255,255]

    return ramp


def cameraProcess(q):
    camera = picamera.PiCamera()
    camera.resolution = (160, 120)
    camera.framerate = 10

    while(1):
            
        time.sleep(0.1)
            
        with picamera.array.PiRGBArray(camera, size=(160, 120)) as stream:
            camera.capture(stream, format='bgr')
            q.put(stream.array)


def leptonProcess(q):
    try:
            HOST = 'localhost'
            PORT = 8888
            HeatMap = make_linear_ramp() 
            
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Start the streaming from the FLIR lepton by sending some data to the socket
            s.sendto('X', (HOST, PORT))
    except socket.error:
        print 'Failed to create socket'
        sys.exit()
        
    while (1):
        try :
            data, server = s.recvfrom(19200)
        
            # Put the received data into a numpy array, reshape to image dimensions
            image_data = numpy.fromstring(data, numpy.uint32)
            image_data_reshaped = numpy.reshape(image_data, (60, 80))

            # Resize and colourise the image
            image = Image.fromarray(numpy.uint8(image_data_reshaped))
            image.putpalette(HeatMap)
            image = image.convert('RGB')
            image = image.rotate(180).resize((80*2, 60*2))

            open_cv_image = numpy.array(image)
            q.put(open_cv_image)
            time.sleep(0.01)
                
        except socket.error, msg:
            print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sys.exit()


def cvProcess(camQ, lepQ, outQ):
    camImage = None
    lepImage = None

    while(1):

        if not camQ.empty():
            #print("Cam Image")
            camImage = camQ.get()
            #outQ.put(camImage)
            #cv2.imwrite('cam_img.png', camImage)

        if not lepQ.empty():
            #print("Lepton Image")
            lepImage = lepQ.get()
            outQ.put(lepImage)
            #cv2.imwrite('lep_img.png', lepImage)

        time.sleep(0.05)


def outProcess(outQ):
    server_address = '/run/shm/cv2node'
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.connect(server_address)
    print 'Ready...'

    while(1):

        if not outQ.empty():
            image = outQ.get()
            r, buf = cv2.imencode(".jpg", image)
            sock.send(buf)
            
        time.sleep(0.05)

cameraImageQueue = Queue(20)
leptonImageQueue = Queue(20)
outImageQueue = Queue(20)

camProcess = Process(target=cameraProcess, args=(cameraImageQueue,))
camProcess.start()

lepProcess = Process(target=leptonProcess, args=(leptonImageQueue,))
lepProcess.start()

outProcess = Process(target=outProcess, args=(outImageQueue,))
outProcess.start()

imgProcProccess = Process(target=cvProcess, args=(cameraImageQueue, leptonImageQueue, outImageQueue,))
imgProcProccess.start()
 
# Main Loop
while(1) :
    time.sleep(1)
