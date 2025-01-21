import sys
import signal
import argparse
from sinewavegenerator.sine_wave_generator import SineWaveGenerator


def main():
    def signal_handler(sig, frame):
        print("\nCtrl+C pressed, shutting down...")
        generator.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

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
        "-f",
        "--frequencies",
        type=float,
        nargs="+",
        default=[440.0],
        help="Sine frequency/frequencies",
    )
    ap.add_argument(
        "-c",
        "--channels",
        default=1,
        type=int,
        required=False,
        help="Number of channels",
    )
    ap.add_argument(
        "-b",
        "--bitdepth",
        default=32,
        type=int,
        required=False,
        help="Audio bitdepth (16/24/32bit)",
    )
    ap.add_argument("-v", "--volume", default=0.8, type=float, required=False, help="Volume")
    ap.add_argument("-g", "--glitch", action="store_true", help="Inserts a glitch roughly every second")
    ap.add_argument("--glitch_size", default=10, type=int, help="Number of samples per channel to glitch")
    ap.add_argument(
        "--dropouts",
        action="store_true",
        help="Insert silence (dropouts). 'glitch_size' sets number of samples to silence",
    )
    ap.add_argument("-w", "--wav", action="store_true", help="Save to wav file")
    ap.add_argument("-d", "--duration", default=10, type=int, required=False, help="Duration [ms]")
    args = vars(ap.parse_args())

    fs = args["sample_rate"]
    freq = args["frequencies"]
    volume = args["volume"]
    channels = args["channels"]
    bitdepth = args["bitdepth"]
    glitch_on = args["glitch"] or args["dropouts"]
    duration = args["duration"]
    file = args["wav"]

    generator = SineWaveGenerator(
        sample_rate=fs,
        frequencies=freq,
        channels=channels,
        bitdepth=bitdepth,
        amplitude=volume,
        chunk_size=1024,
        glitch=glitch_on,
        glitch_size=args["glitch_size"],
        glitch_zeros=args["dropouts"],
    )

    if not file:
        generator.start(blocking=True)
    else:
        print("Saving to sine_wave.wav", "Duration:", duration, "s")
        generator.save_to_wav(duration, "sine_wave.wav")


if __name__ == "__main__":
    main()
