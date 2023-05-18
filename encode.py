# importe as bibliotecas
from suaBibSignal import *
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from suaBibSignal import *
from funcoes_LPF import *
from scipy.io.wavfile import read
from os.path import isfile
import itertools

A = 1
S = signalMeu()

DEFAULT_AUDIO_FILE = "hog-rider.wav"


def prepareAudioForTransmission(audio: np.array, sampleRate: int):
    return LPF(list(itertools.chain(*audio)), 4000, sampleRate)


def main():
    print("-----INIT-----")
    cont = True
    while cont:
        audioFile: str = ""

        print("Waiting for user input")

        while True:
            audioFile: str = input("Enter the file path: ") + ".wav"

            print(audioFile)

            if not isfile(audioFile):
                print("Invalid path, try again")
            else:
                break

        audio = read(audioFile)

        sampleRate = audio[0]

        filteredAudio = prepareAudioForTransmission(audio[1], sampleRate)

        t = 1/sampleRate

        t_array = np.arange(0, len(filteredAudio)/sampleRate, t)

        normalized = np.linalg.norm(filteredAudio)

        portadora = np.sin(2*14000*np.pi*t_array)

        modulada = portadora * filteredAudio

        sd.play(modulada, sampleRate)


if __name__ == "__main__":
    main()
