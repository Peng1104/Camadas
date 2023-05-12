# importe as bibliotecas
from suaBibSignal import *
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from suaBibSignal import *
from pydub import AudioSegment, effects
from pydub.playback import play
from pydub.scipy_effects import low_pass_filter
from scipy.io.wavfile import read 

KEYS = {"1": [697, 1209], "2": [697, 1336], "3": [697, 1477], "A": [697, 1633], "4": [770, 1209], "5": [770, 1336], "6": [770, 1477], "B": [
    770, 1633], "7": [852, 1209], "8": [852, 1336], "9": [852, 1477], "C": [852, 1633], "X": [941, 1209], "0": [941, 1336], "#": [941, 1477], "D": [941, 1633]}

A = 1
SAMPLE_RATE = 48000
DURATION = 5
S = signalMeu()

T = 1/SAMPLE_RATE
T_ARRAY = np.arange(0, DURATION, T)

AUDIO_FILE = "hog-rider.wav"
AUDIO = AudioSegment.from_wav(AUDIO_FILE)

def prepareAudioForTransmission(audio:AudioSegment):
    filtered = audio.low_pass_filter(4000, order=1)
    play(filtered)
    
    _, audioData = read(AUDIO_FILE)
    channel1 = audioData[:,0]

    fourier = np.fft.fft(channel1)
    plt.figure(1, figsize=(8,6))
    plt.plot(fourier, color='#ff7f00')
    plt.xlabel('k')
    plt.ylabel('Amplitude')


    #S.plotFFT(filtered, SAMPLE_RATE)
    #plt.xlim(0, 20000)
    #plt.show()

    pass

def main():
    print("-----INIT-----")
    cont = True
    while cont:
        k:str = ""
        
        print("Waiting for user input")
        while k not in KEYS.keys():
            k:str = input("Enter a key: ")
            if k not in KEYS.keys():
                print("Invalid key")
        
        print("Gerando Tons base")
        sin1 = A * np.sin(2*np.pi*KEYS[k][0]*T_ARRAY)
        sin2 = A * np.sin(2*np.pi*KEYS[k][1]*T_ARRAY)
        sin = sin1 + sin2

        print("Executando as senoides (emitindo o som)")
        sd.play(sin, SAMPLE_RATE)
        sd.wait()

        print("Plotando FFT")
        S.plotFFT(sin, SAMPLE_RATE)
        plt.xlim(500, 1800)
        plt.show()

        print("Plotando senoide no tempo")
        plt.plot(T_ARRAY, sin)
        plt.title("sinal no t")
        plt.xlabel("t")
        plt.ylabel("Amplitude")
        plt.xlim(0, 0.02)
        plt.show()

        print("Generate new tone? (y/n)")
        inp:str = input()
        if inp == "n":
            cont = False
            print("-----END-----")
            return


if __name__ == "__main__":
    #main()
    prepareAudioForTransmission(AUDIO)
