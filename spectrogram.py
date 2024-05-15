import numpy as np
from scipy.io import wavfile
from scipy import fft
#import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import os
from glob import glob
import time
import json

default_rate = 48000
stretch_percent = 10

def stretch(interval: float, 
        R: np.ndarray, 
        rate: int,
        factors: list) -> list:
    """ Strech signal as to time and stretch (shift?) signal in frequency"""

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

def compute_spectrogram(data, N):
    # Spectrogram estimation:
    S = []
    for k in range(0, data.shape[0]+1, N):
        x = fft.fftshift(fft.fft(data[k:k+N], n=N))[N//2:N]
        # Technically, power might use a different log and have a different
        # constant in front.  These are all constants, which will be normalized
        # away anyway.  
        power = np.log(np.real(x*np.conj(x)))
        S.append(power)
    S = np.array(S)
    # map to range [-1, 1]
    # Returning this will create correlation calculation
    #return (S*2 - np.min(S) - np.max(S))/(np.max(S)-np.min(S))

    # map to range [0,1]
    # Returning this will create a calculation for the presence of signal,
    # but not the absence.  It is not, in that sense, a true correlation
    return (S - np.min(S))/(np.max(S)-np.min(S))

def calc_max_correlation(a, b):
    short_len = min(a.shape[0], b.shape[0])
    long_len = max(a.shape[0], b.shape[0])
    s = a if a.shape[0] == short_len else b
    l = b if b.shape[0] == long_len else a
    max_cor = -999999999

    for i in range(long_len - short_len + 1):
        cor = sum([np.dot(s[j],l[j+i]) \
                for j in range(short_len) ])
        max_cor = cor if cor > max_cor else max_cor
        if max_cor > 512*short_len:
            print("max_cor", max_cor)
            print("i", i)
            print("s", s)
            print("l", l)
            exit(33)
    
    # Return the average correlation, else long samples will match "better"
    return max_cor / short_len


def load_wav(filename: str) -> list:
    rate, data = wavfile.read(filename)

    N = 1024

    # Frequencies:
    # f = fft.fftshift(fft.fftfreq(N, d=1/rate))[N//2:N]

    r = compute_spectrogram(data, N)
    return stretch(N/rate, r, rate, \
            [1 + i/100 for i in range(stretch_percent+1)])

def calc_dist(interps_1, interps_2):
    max_score = -999999999
    for i in range(stretch_percent + 1):
        # We will simultaneously treat the stretching of both samples 
        # by i%
        score = calc_max_correlation(interps_1[0], interps_2[i])
        max_score = score if score > max_score else max_score
        score = calc_max_correlation(interps_1[i], interps_2[0])
        max_score = score if score > max_score else max_score

    return max_score

def run():
    
    # e.g. 2024-03-23T03:45:31Z001.wav
    complete_files = glob(os.path.join("signals", 
        "2[0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-9][0-9]Z[0-9][0-9][0-9]*.wav"))

    begin_load = time.time()
    print("Loading all files")
    interps = { f: load_wav(f) for f in complete_files}

    begin_calc = time.time()
    print("Loading complete in", begin_calc - begin_load, "seconds")

    print("Calculating all distances")
    total_files = len(complete_files)
    i = 0
    """
    distances = {f1: {f2: calc_dist(interps1, interps2)} \ 
        for f1, interps1 in interps.items() \
        for f2, interps2 in interps.items()}
        """
    distances = {}
    loop_end = time.time()
    for f1, interps1 in interps.items():
        loop_begin = loop_end
        distances[f1] = {}
        i += 1
        print("\rProcessing file",i,"of",total_files, end="")
        for f2, interps2 in interps.items():
            distances[f1][f2] = calc_dist(interps1, interps2)

        # Checkpoint calculation
        with open("distances.json", "w") as outfile:
            json.dump(distances, outfile)
        loop_end = time.time()
        print("... complete in", loop_end - loop_begin, "seconds")

    print("Distance calculation complete in", \
            begin_load - time.time(), "seconds")
    print(distances)
# Spectrogram rendering:
#plt.imshow(r_1.T, origin='lower')
#plt.show()
#plt.savefig('foo.png')

if __name__ == "__main__":
    run()
