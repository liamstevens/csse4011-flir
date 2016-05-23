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
    

