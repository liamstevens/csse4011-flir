import cv2, sys
import numpy as np

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

        area = np.zeros(area_list[2]-area_list[0], area_list[3]-area_list[1])
        for i in range(area_list[0], area_list[2]):
            for j in range(area_list[1], area_list[3]):
                area[i-area_list[0], j-area_list[1]] = e[i,j]
        #Assigning variables could optimize this - just not sure if it is faster to do it this way or not due to the way that
        #numpy handles 2D arrays and their contiguity in memory.

        if(e > 0):
            #compare previous image in ROI's luminance - commented out for now as unsure if this is wise - may be floored due to low difference
            #res = np.subtract(e, im_list[im_list.index(e)-1]) 

            #NOTE - This difference may need to be scaled in order for it to be significant. Gain required may actually be quite high.
            #Take RGB mean
            means = cv2.mean(res)
            #luminance can be computed from RGB value (if using colorised FLIR image this is fine)
            #luminance is weighted sum of R, G and B values 
            #L = 0.27R + 0.67G + 0.06B
            #This is to match with human perception of brightness, this is prone to change depending on performance
            val = (means[2]*0.27) + (means[1]*0.67) + (means[0]*0.06)
            #Append to end of output list
            out.append(val)

    return out
            
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
def overlay(im1, im2):
#Compare dimensions and apply scaling as required
    im2h, im2w = im2.shape[:1]
    scaled = cv2.resize(im1, (im2h, im2w), interpolation = cv2.INTER_CUBIC)
#Overlay one image over the other (in this case
    ret = cv2.addWeighted(scaled, 0.3, im2, 0.7, 0)
    return ret


#TEST MAIN LOOP FOR DEVELOPMENT
def main():
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
    
if __name__ == "__main__":
    sys.exit(main())
    

