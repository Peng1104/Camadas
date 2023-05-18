# Importe todas as bibliotecas
from suaBibSignal import *
from os.path import isfile
from pydub import AudioSegment, effects
from pydub.playback import play
import peakutils
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
import itertools
from funcoes_LPF import *

# Configs and constants
SAMPLE_RATE = 44100
DURATION = 2.7
T = 1/SAMPLE_RATE
T_ARRAY = np.arange(0, DURATION, T)
S = signalMeu()
sd.default.samplerate = SAMPLE_RATE
sd.default.channels = 1
MARGIN_OF_ERROR = 2
AUDIO_FILE = "output.wav"


def recordAudio():

    while True:
        input("Pressione uma tecla para iniciar a gravação...")

        # Record audio
        audio = sd.rec(int(DURATION * SAMPLE_RATE), SAMPLE_RATE, channels=1)
        sd.wait()
        print("Audio sample recorded")

        # flatten audio list
        audioFlat = list(itertools.chain(*audio))

        if input("Audio salvo, Gravar novamente?") != "s":
            break
    return audio


def main():
    audio = recordAudio()

    t_array = np.arange(0, len(audio)/SAMPLE_RATE, T)

    portadora = np.sin(2*14000*np.pi*t_array)

    modulada = portadora * audio

    filteredAudio = LPF(modulada, 4000, SAMPLE_RATE)

    print("Plotando audio no tempo")
    plt.plot(T_ARRAY, filteredAudio)
    plt.title("audio no t")
    plt.xlabel("t")
    plt.ylabel("Amplitude")
    plt.show()

    print("Plotando FFT")
    S.plotFFT(filteredAudio, SAMPLE_RATE)
    plt.xlim(0, 20000)
    plt.show()

    # Calculate FFT
    xf, yf = S.calcFFT(filteredAudio, SAMPLE_RATE)

    # Get Frequency peaks
    index = peakutils.indexes(yf, thres=0.1, min_dist=50)
    filtered_f = set(map(int, xf[index]))
    print("Frequencias detectadas: {}" .format(filtered_f))


if __name__ == "__main__":
    main()
