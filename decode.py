# Importe todas as bibliotecas
from suaBibSignal import *
import peakutils
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import time
import itertools

# Configs and constants
KEYS = {"1": [697, 1209], "2": [697, 1336], "3": [697, 1477], "A": [697, 1633], "4": [770, 1209], "5": [770, 1336], "6": [770, 1477], "B": [
    770, 1633], "7": [852, 1209], "8": [852, 1336], "9": [852, 1477], "C": [852, 1633], "X": [941, 1209], "0": [941, 1336], "#": [941, 1477], "D": [941, 1633]}
SAMPLE_RATE = 48000
DURATION = 5
T = 1/SAMPLE_RATE
T_ARRAY = np.arange(0, DURATION, T)
S = signalMeu()
sd.default.samplerate = SAMPLE_RATE
sd.default.channels = 1


def main():

    # Record audio
    audio = sd.rec(int(DURATION * SAMPLE_RATE), SAMPLE_RATE, channels=1)
    sd.wait()
    print("Audio sample recorded")

    # flatten audio list
    audioFlat = list(itertools.chain(*audio))

    print("Plotando audio no tempo")
    plt.plot(T_ARRAY, audio)
    plt.title("audio no t")
    plt.xlabel("t")
    plt.ylabel("Amplitude")
    plt.show()

    print("Plotando FFT")
    S.plotFFT(audioFlat, SAMPLE_RATE)
    plt.xlim(500, 1800)
    plt.show()

    #Calculate FFT
    xf, yf = S.calcFFT(audioFlat, SAMPLE_RATE)

    #Get Frequency peaks
    index = peakutils.indexes(yf, thres=0.1, min_dist=50)
    filtered_f = set(
        map(int, [x for x in xf[index] if x <= 2000 and x >= 500]))
    print("Frequencias detectadas: {}" .format(filtered_f))
    
    # Decide which key was pressed
    for key, values in KEYS.items():
        match_count = 0

        for value in values:
            if filtered_f.intersection(range(value-10, value+10)):
                match_count += 1

        #Matched Key
        if match_count == len(values):
            print(f"A Key pressionada é: {key}")
            return

    #Can't detect
    print("Não foi possivel detectar uma key, tente novamenete")
    return

if __name__ == "__main__":
    main()