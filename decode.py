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
MARGIN_OF_ERROR = 2
AUDIO_FILE = "output.wav"


def recordNewFile():
    input("Pressione uma tecla para iniciar a gravação...")

    # Record audio
    audio = AudioSegment(
        sd.rec(int(DURATION * SAMPLE_RATE), SAMPLE_RATE, channels=1))
    sd.wait()

    print("Gravação finalizada")

    AudioSegment.export(audio, AUDIO_FILE, format="wav")

    if input("Audio salvo, Gravar novamente?") == "s":
        recordNewFile()

    return audio


def main():
    audio = []

    if input("Ultilizar mp3? (s/n)") == "s":
        audio = AudioSegment.from_mp3("hog-rider.mp3")
    elif isfile(AUDIO_FILE):
        if input("Deseja ultilizar o arquivo de audio salvo? (s/n)") == "s":
            audio = AudioSegment.from_wav(AUDIO_FILE)
        else:
            audio = recordNewFile()
    else:
        audio = recordNewFile()

    normalized = effects.normalize(audio)

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

    # Calculate FFT
    xf, yf = S.calcFFT(audioFlat, SAMPLE_RATE)

    # Get Frequency peaks
    index = peakutils.indexes(yf, thres=0.1, min_dist=50)
    filtered_f = set(map(int, xf[index]))
    print("Frequencias detectadas: {}" .format(filtered_f))

    teclas = []

    # Check for each key
    for tecla, frequencias in KEYS.items():
        # Match counter
        match_count = 0

        # Check if the frequency is present in the filtered frequencies, with a margin of error
        for frequencia in frequencias:
            if filtered_f.intersection(range(frequencia-MARGIN_OF_ERROR, frequencia+MARGIN_OF_ERROR)):
                match_count += 1

        # If all frequencies match
        if match_count == len(frequencias):
            teclas.append(tecla)

    if len(teclas) == 1:
        print(f"A Tecla pressionada é: {teclas[0]}")
    else:
        print(
            f"Não foi possivel detectar qual tecla foi pressionada, tente novamenete {teclas}")


if __name__ == "__main__":
    main()
