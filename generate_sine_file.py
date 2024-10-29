import argparse
import math
import numpy as np
from time import sleep
from scipy.io import wavfile


def main():
    ap = argparse.ArgumentParser(description="Sine generator")
    ap.add_argument(
        "-r",
        "--sample_rate",
        default=48000,
        required=False,
        type=int,
        help="Sample Rate",
    )
    ap.add_argument(
        "-c",
        "--channels",
        default=2,
        type=int,
        required=False,
        help="Number of channels",
    )
    ap.add_argument(
        "-b",
        "--bitdepth",
        default=16,
        type=int,
        required=False,
        help="Audio bitdepth (16/24/32bit)",
    )
    ap.add_argument(
        "-f",
        "--frequencies",
        nargs="+",
        default=["440", "552"],
        required=False,
        help="Sine frequencies",
    )
    ap.add_argument(
        "-v", "--volume", default=0.8, type=float, required=False, help="Volume"
    )
    ap.add_argument(
        "-d", "--duration", default=10, type=int, required=False, help="Duration [ms]"
    )
    ap.add_argument(
        "-m",
        "--mode",
        type=str,
        default="file",
        required=False,
        help="Mode: 'file' or 'stream'",
    )
    args = vars(ap.parse_args())

    fs = args["sample_rate"]
    f = [int(freq) for freq in args["frequencies"]]
    volume = args["volume"]
    channels = args["channels"]
    dur_ms = args["duration"]
    num_samples = int(fs * dur_ms / 1000)

    # Bit depth
    bit_depth = int(args["bitdepth"])
    scale = int((pow(2, bit_depth) / 2) - 1)
    print(scale)
    if bit_depth > 16:
        data_type = np.int32
    else:
        data_type = np.int16

    samples = np.zeros((num_samples, channels), dtype=data_type)

    if args["mode"] == "file":
        print("Sample rate: ", fs)
        print("Bits:        ", bit_depth)
        print("Channels:    ", channels)
        print("Frequencies: ", f)
        print("Volume:      ", volume)
        print(f"Duration:     {dur_ms}ms")

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
