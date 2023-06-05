import argparse
import math
import numpy as np
from scipy.io import wavfile


def main():
    ap = argparse.ArgumentParser(description='Sine generator')
    ap.add_argument("-r", "--sample_rate", default=48000, required=False, type=int,
    help="Sample Rate")
    ap.add_argument("-c", "--channels", default=2, type=int, required=False,
    help="Number of channels")
    ap.add_argument("-f", "--frequencies", default=[440, 552], type=list, required=False,
    help="Sine frequencies")
    ap.add_argument("-v", "--volume", default=0.8, type=float, required=False,
    help="Volume")
    ap.add_argument("-d", "--duration", default=10, type=int, required=False,
    help="Duration [ms]")
    args = vars(ap.parse_args())

    fs = args['sample_rate']
    f = list(args['frequencies'])
    volume = args['volume']
    channels = args['channels']
    scale = 32767
    dur_ms = args['duration']

    print("Sample rate: ", fs)
    print("Channels:    ", channels)
    print("Frequencies: ", f)
    print("Volume:      ", volume)
    print("Duration:    ", dur_ms)

    num_samples = int(fs*dur_ms/1000)

    samples = np.zeros((num_samples, channels), dtype=np.int16)

    for channel in range(channels):
        theta = 0.0
        amp = volume * scale
        step = f[channel] * 2 * math.pi / fs
        for sample in range(num_samples):
            samples[sample][channel] = amp * math.sin(theta)
            theta += step

    # Generate Wav file
    wavfile.write("sine.wav", fs, samples)

    print("done")


if __name__ == "__main__":
    main()
