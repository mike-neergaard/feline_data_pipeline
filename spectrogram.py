import numpy as np
from scipy.io import wavfile
from scipy import fft
#import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline

class Spectrogram:
    """ A class to read wav files and calculate spectrograms. """
    def __init__(self, fname = None, fft_size = 1024, default_rate = 48000):
        self.default_rate = 48000
        self.fft_size = fft_size
        if fname is not None:
            self.wav_to_spectrogram(fname)

    def wav_to_spectrogram(self, 
            filename: str, 
            stretch_percent: int = 10) -> list:
        """ Read a wav file and calculate spectrogram and interpolations
        Args:
            filename (str): wav file to open

        Returns:
            None
        """
        rate, data = wavfile.read(filename)
    
        N = self.fft_size
    
        # Frequencies:
        # f = fft.fftshift(fft.fftfreq(N, d=1/rate))[N//2:N]
    
        self.spectrogram = self.calc_spectrogram(data)
        self.interps = self.fill_interps(N/rate, self.spectrogram, rate, \
                self.default_rate, \
                [1 + i/100 for i in range(stretch_percent+1)])

    def calc_spectrogram(self, data, lower=0, upper=1):
        """ Calculate spectrogram 
        args:
            data
            lower
            upper
        # map to range [-1, 1]
        # Returning this will create correlation calculation
        #return (S*2 - np.min(S) - np.max(S))/(np.max(S)-np.min(S))
    
        # map to range [0,1]
        # Returning this will create a calculation for the presence of signal,
        # but not the absence.  It is not, in that sense, a true correlation
        return:
        """
        

        N = self.fft_size
        # Spectrogram estimation:
        S = []
        for k in range(0, data.shape[0]+1, N):
            x = fft.fftshift(fft.fft(data[k:k+N], n=N))[N//2:N]
            # Technically, power might use a different log and have a different
            # constant in front.  These are all constants, which will be 
            # normalized away anyway.  
            power = np.log(np.real(x*np.conj(x)))
            S.append(power)
        S = np.array(S)

        S_min = np.min(S)
        S_max = np.max(S)
        # Avoid a divide by zero error
        if S_min == S_max: return S - S_min + lower

        # Map to range [lower, upper]
        return  (S - S_min) * ((upper-lower) / (S_max - S_min)) + lower


    def fill_interps(self, 
        interval: float, 
        R: np.ndarray, 
        rate: int,
        default_rate: int,
        factors: list) -> list:
        """ Strech signal as to time 
            args:
                R: The spectrogram
                rate: The sampling rate
            returns:
                interps
                
        """

        # Derive the timestamps
        x = [interval*i for i in range(R.shape[0])]

        interps = []
        bsplines = []
        for i in range(R.shape[1]):
            y = R.T[i] 
            bsplines.append(make_interp_spline(x, y, k=3))

        # Need to normalize for different sampling rates.
        # How many samples would the array have if sampled at the default rate?
        sample_len = R.shape[0]*default_rate / rate

        for j in range(len(factors)):
            factor = factors[j]
            interp_list = []
            for i in range(R.shape[1]):
                xx = [interval * i / factor \
                        for i in range(round(sample_len*factor))]
                yy = bsplines[i](xx)
                interp_list.append(yy)
            interp_array = np.array(interp_list).T
            interps.append(interp_array)
    
        return interps

