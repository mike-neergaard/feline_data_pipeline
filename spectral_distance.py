import numpy as np
#import matplotlib.pyplot as plt
import os
from glob import glob
import time
import json
import math
from spectrogram import Spectrogram

class spectral_distance:
    @classmethod
    def calc_max_correlation(cls, a, b):
        short_len = min(a.shape[0], b.shape[0])
        long_len = max(a.shape[0], b.shape[0])
        s = a if a.shape[0] == short_len else b
        l = b if b.shape[0] == long_len else a
        s_norm = math.sqrt( sum([np.dot(s[j],s[j]) \
                    for j in range(short_len) ]))
        max_cor = -999999999
    
        for i in range(long_len - short_len + 1):
            l_norm = math.sqrt( sum([np.dot(l[j+i],l[j+i]) \
                    for j in range(short_len) ]) )
            cor = sum([np.dot(s[j],l[j+i]) \
                    for j in range(short_len) ])/ (s_norm * l_norm)
            max_cor = cor if cor > max_cor else max_cor
            if max_cor > 1:
                print("max_cor", max_cor)
                print("i", i)
                print("s", s)
                print("l", l)
                exit(33)
    
        # Return the average correlation, else long samples will match "better"
        return max_cor / short_len


    @classmethod
    def calc_dist(cls, interps_1, interps_2, stretch_percent: int = 10):
        max_score = -999999999
        for i in range(stretch_percent + 1):
            # We will simultaneously treat the stretching of both samples 
            # by i%
            score = spectral_distance.calc_max_correlation(interps_1[0], interps_2[i])
            max_score = score if score > max_score else max_score
            score = spectral_distance.calc_max_correlation(interps_1[i], interps_2[0])
            max_score = score if score > max_score else max_score

        return max_score 

def run():
    
    # e.g. 2024-03-23T03:45:31Z001.wav
    complete_files = glob(os.path.join("signals", "2[0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-9][0-9]Z[0-9][0-9][0-9]*.wav"))

    begin_load = time.time()
    print("Loading all files")
    #interps = { f.replace("signals/",""): wav_spectrogram(f) for f in complete_files}
    interps = { f: Spectrogram(f).interps for f in complete_files}

    begin_calc = time.time()
    print("Loading complete in", begin_calc - begin_load, "seconds")

    print("Calculating all distances")
    total_files = len(complete_files)
    i = 0
    """
    distances = {f1: {f2: spectral_distance.calc_dist(interp1, interp2)} \ 
        for f1, interp1 in interps.items() \
        for f2, interp2 in interps.items()}
        """
    distances = {}
    loop_end = time.time()

    for f1, interp1 in interps.items():
        loop_begin = loop_end
        distances[f1] = {}
        i += 1
        print("\rProcessing file",i,"of",total_files, end="")
        for f2, interp2 in interps.items():
            if f1 == f2:
                distances[f1][f2] = 1
            else:
                distances[f1][f2] = spectral_distance.calc_dist(interp1, interp2)

        # Checkpoint calculation
        with open("distances.json", "w") as outfile:
            json.dump(distances, outfile, indent=2)
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
