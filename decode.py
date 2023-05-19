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
from scipy.io.wavfile import read

# Configs and constants
SAMPLE_RATE = 44100
DURATION = 5.5
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

    print("Use wav? (y/n)")
    inp: str = input()
    if inp == "n":
        audio = recordAudio()

        t_array = np.arange(0, len(audio[1][:,0])/SAMPLE_RATE, T)
    else:
        while True:
            audioFile: str = input("Enter the file path: ") + ".wav"

            if not isfile(audioFile):
                print("Invalid path, try again")
            else:
                break

        audio = read(audioFile)

        sampleRate = audio[0]
        
        t_array = np.arange(0, len(audio[1])/sampleRate, 1/sampleRate)

    portadora = np.sin(2*14000*np.pi*t_array)

    modulada = portadora * audio[1]

    filteredAudio = LPF(modulada, 4000, sampleRate)

    print("Plotando FFT")
    S.plotFFT(filteredAudio, sampleRate)
    plt.xlim(0, 20000)
    plt.show()

    sd.play(filteredAudio, sampleRate)
    sd.wait()


if __name__ == "__main__":
    main()
