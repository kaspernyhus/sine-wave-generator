import sys
import signal
import argparse
from sinewavegenerator.sine_wave_generator import SineWaveGenerator, GlitchType


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
    ap.add_argument("-g", "--glitch", action="store_true", help="Enable glitches roughly every second")
    ap.add_argument(
        "--dropout",
        nargs="?",
        type=int,
        required=False,
        help="Insert silence (dropouts). Number of samples to silence (default: 100)",
    )
    ap.add_argument(
        "--skip",
        nargs="?",
        type=int,
        required=False,
        help="Skip samples (default: 10)",
    )
    ap.add_argument(
        "--fullscale",
        nargs="?",
        type=int,
        required=False,
        help="Insert full scale samples to produce a click (default: 5)",
    )
    ap.add_argument("-w", "--wav", action="store_true", help="Save to wav file")
    ap.add_argument("-d", "--duration", default=10, type=int, required=False, help="Duration [ms]")
    args = vars(ap.parse_args())

    fs = args["sample_rate"]
    freq = args["frequencies"]
    volume = args["volume"]
    channels = args["channels"]
    bitdepth = args["bitdepth"]
    glitch_on = args["glitch"]
    duration = args["duration"]
    file = args["wav"]

    glitch_type = GlitchType.NONE
    glitch_size = 0

    if glitch_on:
        print("NOTE: Glitches enabled")
        if "--dropout" in sys.argv:
            print("... producing dropouts\n")
            glitch_type = GlitchType.DROPOUT
            glitch_size = 100 if not args["dropout"] else args["dropout"]
        elif "--skip" in sys.argv:
            print("... skipping samples\n")
            glitch_type = GlitchType.SKIP
            glitch_size = 10 if not args["skip"] else args["skip"]
        elif "--fullscale" in sys.argv:
            print("... inserting full scale samples\n")
            glitch_type = GlitchType.FULLSCALE
            glitch_size = 5 if not args["fullscale"] else args["fullscale"]

    generator = SineWaveGenerator(
        sample_rate=fs,
        frequencies=freq,
        channels=channels,
        bitdepth=bitdepth,
        amplitude=volume,
        chunk_size=1024,
        glitch_type=glitch_type,
        glitch_size=glitch_size,
    )

    if not file:
        generator.start(blocking=True)
    else:
        print("Saving to sine_wave.wav", "Duration:", duration, "s")
        generator.save_to_wav(duration, "sine_wave.wav")


if __name__ == "__main__":
    main()
