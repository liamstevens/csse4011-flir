import cv2, sys
import numpy as np
from scipy.signal import savgol_filter




#Function to draw lines around objects of at least llim intensity
def threshold_contour(image, ulim, llim):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, gray = cv2.threshold(gray, llim, ulim, cv2.THRESH_BINARY)
    contImage, contours, hier = cv2.findContours(gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 
    cv2.drawContours(image, contours, -1, (0, 255, 0), 2)
    cv2.imshow('frame', image)

#Computes the difference in brightness between a sequence of frames.
'''
    Arguments:
    @im_list: A list of images to analyse. Should have already been parsed by OpenCV (ie., they are numpy ndarrays)
    @area_list: A list of ROIs, represented in tuples. Structed as (x, y, dx, dy). im_list[i] corresponds to area_list[i]. 
                This is simply the rectangular area in which we are interested in.
    @return A list of average luminances (one for each frame). For a large number of frames (minimum 30),
            we can calculate a heartrate.
'''
def series_analyse(im_list, area_list):
    out = []
    for e in im_list:
        a = area_list[im_list.index(e)] #Pretty dodgy. Could almost certainly do this more efficiently but it will do for now.
        mask = mask_image(e, a)
        val = mean_luminance(mask)
        out.append(val)
    return out

'''
    Find the dominant frequency, typically this translates to the heartbeat.
    There is likely a lot of low frequency response, which needs to be ignored.
    Arguments:
    @arr: An array of luminances, typically numpy float64 values.
    @Ts: Sample time, in seconds - inverse of sample rate.
    @return: Dominant frequency (BPM). May not be lower than 40BPM. Rounded to integer.
'''
def find_frequency(arr, Ts):
    spectrum = np.fft.fft(arr)
    frequencies =  np.fft.fftfreq(len(arr), Ts)
    #Discard negative frequencies, and associated peaks - not interested.
    ############HERE BE ARBITRATION, SUBJECT TO CHANGE##################
    #There are a few large, low frequency components to the FLIR data (DC is *HUGE*).
    #This can be either due to the FLIR recently starting up, or (hopefully infrequent) 
    #ambient temperature changes that it equalises. These *WILL* mess up our spectral 
    #analysis, so we are going to discard anything that is close to, or below 
    #40BPM (0.6666Hz), as this is pushing it for resting heart rate.
    #####################ARBITRARY SPEEL OVER.#########################
    pos_freq =  [f for f in frequencies if f > 0]
    #This uses a bit of trickery from the way that np.fft.fftfreq constructs its
    #array of frequencies. All positive frequencies are added to the array, then the
    #negative frequencies. This means we can avoid having to process the negative
    #frequencies at all, save for one.
    #Now we truncate for the lower frequencies at 0.666Hz
    final_freq = [f for f in pos_freq if f > 0.7]
    spectrum = spectrum[(len(pos_freq)-len(final_freq)):len(pos_freq)-1]
    abs_spec = np.absolute(spectrum)
    max_val = np.amax(abs_spec)
    max_index = np.where(abs_spec==max_val)
    maxfreq = final_freq[max_index[0][0]]#-1?
    return int(maxfreq*60) #Return a floored (integer) representation of the frequency in BPM

'''
    Used once a face is found to find the neck.
    Arguments:
    @image: The entire image. Multiple faces is fine, as there should be only one face processed per function call.
    @roi: The Region of Interest describing the location of the face.
    @return: The neck corresponding to the detected face.
'''
def find_neck(image, roi):
    neckdim = ((roi[0]+((roi[2]-roi[0])/4)),roi[3],(roi[2]-((roi[2]-roi[0])/4)), (roi[3]+((roi[3]-roi[1])/2))
    #This is very opaque but I think is the best way to do it. The region of the neck is half the height 
    #and width, and is centred on the middle of the face's ROI. This means the "corners" of the new ROI
    #are at 1/4, 3/4x, and y, 3y/2. 
    out_img = mask_image(image, neckdim)
    return out_img
'''
    Arguments:
    @image: A numpy ndarray representation of an image.
    @area A region to capture from the image. Structured (x, y, dx, dy)
    @return A masked (ie., cropped) version of the image.
'''
def mask_image(image, area):
    return image[area[0]:area[2], area[1]:area[3]]

'''
    Arguments:
    @image: A numpy ndarray representation of an image. When being fed to this,
    typically should be cropped for a region of interest.
    @return: The average luminance of the region.
'''
def mean_luminance(image):
    image_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YCR_CB) 
    image_y = cv2.split(image_yuv)[0]
    val = cv2.mean(image_y)[0]
    return val
            
#To be used with gray colour maps (no transformation to gray, to save computation - essentially only feed this FLIR data)
#im1 and im2 to be numpy arrays
def img_bright_diff(im1, im2):
    kernel = np.ones((2,2), np.uint8)
    #cv2.closing may be useful here (img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel) (kernel to be specified)
    #this fills "holes" in the image (typically caused by noise but may be due to clothing, etc for FLIR)
    im1 = cv2.morphologyEx(im1, cv2.MORPH_CLOSE, kernel)
    im2 = cv2.morphology(im2, cv2.MORPH_CLOSE, kernel)
    res = np.subtract(im1, im2)
    return res
    
#Format agnostic, as long as openCV has accepted them as images, im1 and im2 are fine to be used.
#im1 = FLIR image, im2 = webcam/raspicam
#TODO - This requires a translation and a crop - the FLIR has a smaller FoV than the picam, and will be physically located elsewhere - this means that 
#       a straight scale will not be accurate
def overlay(im1, im2):
#Compare dimensions and apply scaling as required
    im2h, im2w = im2.shape[:1]
    scaled = cv2.resize(im1, (im2h, im2w), interpolation = cv2.INTER_CUBIC)
#Overlay one image over the other (in this case
    ret = cv2.addWeighted(scaled, 0.3, im2, 0.7, 0)
    return ret


def face_cascade(cascade, image, gflag=True):
    if not gflag:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    return cascade.detectMultiScale(gray, scaleFactor = 1.5, minNeighbors = 5, minSize = (30, 30), flags = cv2.CASCADE_SCALE_IMAGE)


def detections_draw(image, detections):
    for (x, y, w, h) in detections:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)


#TEST MAIN LOOP FOR DEVELOPMENT
def main():
    regions = []
    images = []
    raw = []
    vals = []
    cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')

    image_path = sys.argv[1]
    #Read in the test images
    for i in range(1, 100):
        raw.append(cv2.imread(image_path.strip()+"{}.jpg".format(i)))
    #raw.append(cv2.imread(image_path))
    #iterate over test images and get output
    for i in raw:
        #Do facial recognition on each image and return an array of images + regions of interest
        vals.append(mean_luminance(i))
        #num = face_cascade(cascade, i, False)
        #if len(num) > 0:
        #    regions.append(num)
        #    images.append(i)
    #print "No. images: {0:2d}".format(len(images))
    base = min(vals)
    vals[:] = [e - base for e in vals]
    fft_vals = np.fft.fft(vals)
    print "Frequency: {}".format(find_frequency(vals, 0.125))
if __name__ == "__main__":
    sys.exit(main())
    

