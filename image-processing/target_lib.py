import numpy as np
import cv2
#import "flir_process_lib.py"

def sort_targets(targets):
    return sorted(targets, key=lambda x: (-x.timer, x.roi[0]))

def validate_targets(targets, rois):

    found = []
    remaining = rois

    # Iterate through all targets (check for for valid rois, put them in)
    for item in targets:
        for roi in remaining:
            roi_not_found = True
            
            # Pop from list if roi is valid
            if item.validate_roi(roi):
                found.add(remaining.pop(roi))
                roi_not_found = False
                break

        # If no valid rois found, just add empty element
        if roi_not_found:
            found.add(None)

    return found, remaining

'''
A class to represent tracked targets.
    @history: A list of luminance values.
    @timestamp: A correstponding list of timestamps.
    @roi: A tuple indicating the region of interest for this target.
    @ID: A unique identifier for the target.
    @timer: A timeout indicator for when the target cannot be tracked.
'''
class target:

    def __init__(self, area, ID):
        self.history = deque([])
        self.timestamp = deque([])
        self.roi = area
        self.delta = (self.roi[3]-self.roi[0])/2
        self.previous_roi = None
        self.ID = ID
        self.timer = 5
        self.rate = 0
        
    '''
        Find whether the new ROI is valid. This is pretty primitive, just checks if
        the ROI is reasonable (not a large change in position). Delta is tunable
        (set to half width of ROI currently)
        Arguments:
        @roi: The new ROI to validate.
        @delta: A tunable value, to specify the maximum change that is permissible.
    '''
    def validate_roi(self, roi):
        for i in range(0,3):
            if abs(self.roi[i]-roi[i]) > self.delta:
                return false
        return true
        
    '''
        Update the region of interest stored.
        Arguments:
        @lum: a luminance value to append to history.
        @region: A new ROI for the object, if it has shifted. Optional.
        If no value is provided, defaults to previous value.
    '''    
    def update_roi(self, lum, region=None):
        if region == None or not validate_roi(region):
            #At the point there are two options. We can reuse the previous ROI (attribute in place for this)
            #Alternately we can attempt to extrapolate the position. This will likely produce worse results,
            #So for now we will just use the previous value
            self.roi = self.previous_roi
            self.timer = self.timer-1#We don't have a valid ROI so decrement the timer. Once it reaches zero,
                                     #it should be removed from the list of objects.

        else:
            self.previous_roi = self.roi
            self.roi = region
            self.delta = (self.roi[3]-self.roi[0])/2
            self.timer = 5# reset the timer
        if len(self.history) < 100:
            self.history.append(lum)
        else:
            #At least 100 samples. We can do some analysis reliably.
            self.history.pop()#Discard oldest term
            self.history.append(lum)
       
    '''
        Find the dominant frequency, typically this translates to the heartbeat.
        There is likely a lot of low frequency response, which needs to be ignored.
        Arguments:
        @arr: An array of luminances, typically numpy float64 values.
        @Ts: Sample time, in seconds - inverse of sample rate.
        @return: Dominant frequency (BPM). May not be lower than 40BPM. Rounded to integer.
    '''
    def find_frequency(self):
        spectrum = np.fft.fft(self.history)
        Ts = numpy.average(numpy.diff(self.timestamp))
        frequencies =  np.fft.fftfreq(len(history), Ts)
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

        spectrum = spectrum[:]#truncate the spectrum appropriately
        #Now we truncate for the lower frequencies at 0.7Hz
        final_freq = [f for f in pos_freq if f > 0.7]
        spectrum = spectrum[len(pos_freq)-len(final_freq)+1:len(pos_freq)-1]#no +1 previously
        final_freq = final_freq[len(final_freq)-len(spectrum):] #does not exist previously - forces matching of spectrum and frequency array lengths
        abs_spec = np.absolute(spectrum)
        max_val = np.amax(abs_spec)
        max_index = np.where(abs_spec==max_val)[0][0]
        maxfreq = final_freq[max_index]
        self.rate = int(maxfreq*60)
        #return int(maxfreq*60) #Return a floored (integer) representation of the frequency in BPM
