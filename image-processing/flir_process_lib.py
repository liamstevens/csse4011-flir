import cv2, sys
import numpy as np
#import scipy.signal as sci
from scipy.signal import savgol_filter
#import scikit-learn as skl
#import matplotlib.pyplot as mpl
#TODO inspect contents of contours for use in clustering

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
        '''
        area = np.zeros(area_list[2]-area_list[0], area_list[3]-area_list[1])
        for i in range(area_list[0], area_list[2]):
            for j in range(area_list[1], area_list[3]):
                area[i-area_list[0], j-area_list[1]] = e[i,j]
        #Assigning variables could optimize this - just not sure if it is faster to do it this way or not due to the way that
        #numpy handles 2D arrays and their contiguity in memory.

        if(imlist.index(e) > 0):
            #compare previous image in ROI's luminance - commented out for now as unsure if this is wise - may be floored due to low difference
            #res = np.subtract(e, im_list[im_list.index(e)-1]) 

            #NOTE - This difference may need to be scaled in order for it to be significant. Gain required may actually be quite high.
            #means = cv2.mean(res)
            #This is to match with human perception of brightness, this is prone to change depending on performance
            #val = (means[2]*0.27) + (means[1]*0.67) + (means[0]*0.06)
            #Append to end of output list
            val = mean_luminance(e)
            out.append(val)
            '''

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
    pos_freq =  [f in frequencies if f > 0]
    #This uses a bit of trickery from the way that np.fft.fftfreq constructs its
    #array of frequencies. All positive frequencies are added to the array, then the
    #negative frequencies. This means we can avoid having to process the negative
    #frequencies at all, save for one.

    spectrum = spectrum[:len(pos_freq)-1]#truncate the spectrum appropriately
    #Now we truncate for the lower frequencies at 0.666Hz
    final_freq = [f in pos_freq if f > 0.666]
    spectrum = spectrum[(len(pos_freq)-len(final_freq)-1:]
    abs_spec = np.absolute(spectrum)
    max_val = np.amax(abs_spec)
    maxfreq = final_freq[np.where(abs_spec==max_val)]
    return int(maxfreq*60) #Return a floored (integer) representation of the frequency in BPM


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
        # print "({0}, {1}, {2}, {3})".format(x, y, w, h)
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
    '''for i in range(0, 20):
        raw.append[cv2.imread("latest{0:3d}.jpg".format(i))]
        '''
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
    print "unfiltered"
    print vals
    fft_vals = np.fft.fft(vals)
    print "FFT coefficients"
    print fft_vals
    print "Frequencies?"
    print np.fft.fftfreq(fft_vals.size, 0.125)
    vals = savgol_filter(vals, 21, 5, deriv=1)
    print "Derivatives"
    print vals
    #mpl.plot([vals])
    #mpl.ylabel("Variance in mean luminance of images")
    #mpl.show()
    '''
    while(True):
        #pull webcam image and draw contours around lighter parts of the image
        #In actual application it may be worth doing grayscale conversions in mainloop to avoid extra computation time
        cap = cv2.VideoCapture(0)
        ret, image = cap.read()
        threshold_contour(image, 255, 127)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break;

    cap.release()
    cv2.destroyAllWindows()
    '''
if __name__ == "__main__":
    sys.exit(main())
    

