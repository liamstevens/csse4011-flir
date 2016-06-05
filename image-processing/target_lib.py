import numpy as np
import cv2
#import "flir_process_lib.py"
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
        self.previous_roi = None
        self.ID = ID
        self.timer = 5
        self.rate = 0
        
        
    #Update the region of interest stored    
    def update_roi(self, lum, region=None):
        if region == None:
            #At the point there are two options. We can reuse the previous ROI (attribute in place for this)
            #Alternately we can attempt to extrapolate the position. This will likely produce worse results,
            #So for now we will just use the previous value
            self.roi = self.previous_roi
            self.timer = self.timer-1#We don't have a valid ROI so decrement the timer. Once it reaches zero,
                                     #it should be removed from the list of objects.

        else:
            self.previous_roi = self.roi
            self.roi = region
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
        #Now we truncate for the lower frequencies at 0.666Hz
        final_freq = [f for f in pos_freq if f > 0.666]
        spectrum = spectrum[len(pos_freq)-len(final_freq):len(pos_freq)-1]
        abs_spec = np.absolute(spectrum)
        max_val = np.amax(abs_spec)
        max_index = np.where(abs_spec==max_val)[0][0]
        maxfreq = final_freq[max_index]
        return int(maxfreq*60) #Return a floored (integer) representation of the frequency in BPM
