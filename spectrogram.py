import numpy as np
from scipy.io import wavfile
from scipy import fft
import matplotlib.pyplot as plt

rate, data = wavfile.read('./signals/2024-04-15T16:06:28Z001.wav')
N = 1024

# Frequencies:
#f = np.log(fft.fftshift(fft.fftfreq(N, d=1/rate))[N//2+1:N])
f = fft.fftshift(fft.fftfreq(N, d=1/rate))[N//2:N]

# array([    0. ,   187.5,   375. , ..., 23625. , 23812.5])
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
R = (S - np.min(S))/(np.max(S)-np.min(S))
print("max(R) =",np.max(R))
print("min(R) =",np.min(R))


# Spectrogram rendering:
plt.imshow(R.T, origin='lower')
plt.savefig('foo.png')
