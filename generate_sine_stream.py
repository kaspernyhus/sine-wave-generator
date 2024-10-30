import sys
import time
import signal
import argparse
from sine_wave_generator import SineWaveGenerator


def main():
    def signal_handler(sig, frame):
        print("\nCtrl+C pressed. Shutting down...")
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
        "--frequency",
        default=440,
        required=False,
        type=int,
        help="Sine frequency",
    )
    ap.add_argument(
        "-v",
        "--volume",
        default=0.8,
        type=float,
        required=False,
        help="Volume"
    )
    ap.add_argument(
        "-g",
        "--glitch",
        action="store_true",
        help="Produce a glitch roughly every second"
    )
    args = vars(ap.parse_args())

    fs = args["sample_rate"]
    freq = args["frequency"]
    volume = args["volume"]
    glitch_on = args["glitch"]

    generator = SineWaveGenerator(sample_rate=fs, frequency=freq, amplitude=volume, chunk_size=1024, glitch=glitch_on)
    generator.start()

    while not generator.exit_event.is_set():
        time.sleep(0.1)


if __name__ == "__main__":
    main()
