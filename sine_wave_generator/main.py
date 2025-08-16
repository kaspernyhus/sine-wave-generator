import sys
import signal
import argparse
from sine_wave_generator import SineWaveGenerator, GlitchType


def main():
    def signal_handler(sig, frame):
        print("\nCtrl+C pressed, shutting down...")
        generator.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    ap = argparse.ArgumentParser(
        description="Generate sine waves as audio streams or WAV files with optional glitch effects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                             # Play 440Hz sine wave
  %(prog)s -f 1000 -v 0.5              # Play 1kHz at 50%% volume
  %(prog)s -f 440 880 -c 2             # Play stereo (440Hz left, 880Hz right)
  %(prog)s -w -d 5                     # Save 5 second WAV file
  %(prog)s --dropout 50                # Play with dropout glitches (50 samples)
  %(prog)s --skip --random-interval    # Play with randomized skip glitches
        """,
    )

    # Audio Generation Settings
    audio_group = ap.add_argument_group("Audio Generation Settings")
    audio_group.add_argument(
        "-f",
        "--frequencies",
        type=float,
        nargs="+",
        default=[440.0],
        metavar="HZ",
        help="Sine wave frequencies in Hz (default: %(default)s Hz)",
    )
    audio_group.add_argument(
        "-v",
        "--volume",
        default=0.8,
        type=float,
        metavar="LEVEL",
        help="Audio volume level 0.0-1.0 (default: %(default)s)",
    )
    audio_group.add_argument(
        "-r",
        "--sample_rate",
        default=48000,
        type=int,
        metavar="HZ",
        help="Audio sample rate in Hz (default: %(default)s Hz)",
    )

    # Audio Format Settings
    format_group = ap.add_argument_group("Audio Format Settings")
    format_group.add_argument(
        "-c",
        "--channels",
        default=1,
        type=int,
        metavar="N",
        help="Number of audio channels (default: %(default)s)",
    )
    format_group.add_argument(
        "-b",
        "--bitdepth",
        default=32,
        type=int,
        choices=[16, 24, 32],
        metavar="BITS",
        help="Audio bit depth: 16, 24, or 32 bits (default: %(default)s)",
    )

    # Output Settings
    output_group = ap.add_argument_group("Output Settings")
    output_group.add_argument("-w", "--wav", action="store_true", help="Save to WAV file instead of playing audio")
    output_group.add_argument(
        "-d",
        "--duration",
        default=10,
        type=int,
        metavar="SEC",
        help="Duration in seconds for WAV output (default: %(default)s sec)",
    )

    glitch_group = ap.add_argument_group("Glitch Effects (experimental audio artifacts)")
    glitch_group.add_argument(
        "-g",
        "--glitch",
        action="store_true",
        help="Enable glitch effects (defaults to dropout if no specific type given)",
    )
    glitch_group.add_argument(
        "--dropout",
        nargs="?",
        type=int,
        const=100,
        metavar="SAMPLES",
        help="Insert silence dropouts every ~1 second (default: %(const)s samples)",
    )
    glitch_group.add_argument(
        "--skip",
        nargs="?",
        type=int,
        const=10,
        metavar="SAMPLES",
        help="Skip audio samples every ~1 second (default: %(const)s samples)",
    )
    glitch_group.add_argument(
        "--fullscale",
        nargs="?",
        type=int,
        const=5,
        metavar="SAMPLES",
        help="Insert full-scale clicks every ~1 second (default: %(const)s samples)",
    )
    glitch_group.add_argument(
        "--random-interval",
        action="store_true",
        help="Randomize glitch intervals for more realistic artifacts",
    )
    glitch_group.add_argument(
        "--interval-range",
        nargs=2,
        type=float,
        default=[0.5, 2.0],
        metavar=("MIN", "MAX"),
        help="Range for random glitch intervals in seconds (default: %(default)s)",
    )
    args = vars(ap.parse_args())

    fs = args["sample_rate"]
    freq = args["frequencies"]
    volume = args["volume"]
    channels = args["channels"]
    bitdepth = args["bitdepth"]
    glitch_on = args["glitch"]
    duration = args["duration"]
    file = args["wav"]
    random_interval = args["random_interval"]
    interval_range = tuple(args["interval_range"])

    glitch_type = GlitchType.NONE
    glitch_size = 0

    if args["dropout"] is not None:
        glitch_on = True
        glitch_type = GlitchType.DROPOUT
        glitch_size = args["dropout"]
    elif args["skip"] is not None:
        glitch_on = True
        glitch_type = GlitchType.SKIP
        glitch_size = args["skip"]
    elif args["fullscale"] is not None:
        glitch_on = True
        glitch_type = GlitchType.FULLSCALE
        glitch_size = args["fullscale"]
    elif glitch_on:
        glitch_type = GlitchType.DROPOUT
        glitch_size = 100

    try:
        generator = SineWaveGenerator(
            sample_rate=fs,
            frequencies=freq,
            channels=channels,
            bitdepth=bitdepth,
            amplitude=volume,
            chunk_size=1024,
            glitch_type=glitch_type,
            glitch_size=glitch_size,
            random_glitch_interval=random_interval,
            glitch_interval_range=interval_range,
        )
    except ValueError as e:
        print(f"\033[91mError: {e}\033[0m")
        sys.exit(1)
    except Exception as e:
        print(f"\033[91mUnexpected error initializing generator: {e}\033[0m")
        sys.exit(1)

    if file:
        print("Saving sine wave(s) to WAV file(s)")
    else:
        print("Playing sine wave(s) at frequencies:", freq, "Hz")
        print("\033[94mPress Ctrl+C to stop\033[0m\n")
    if glitch_on:
        print("\033[91mNOTE: Glitches enabled\033[0m")
        if glitch_type == GlitchType.DROPOUT:
            print(f"\033[93mGlitch type: DROPOUT, size: {glitch_size} samples\033[0m")
        elif glitch_type == GlitchType.SKIP:
            print(f"\033[93mGlitch type: SKIP, size: {glitch_size} samples\033[0m")
        elif glitch_type == GlitchType.FULLSCALE:
            print(f"\033[93mGlitch type: FULLSCALE, size: {glitch_size} samples\033[0m")

        if random_interval:
            print(f"\033[94mRandom intervals: {interval_range[0]:.1f}s - {interval_range[1]:.1f}s\033[0m")
        else:
            print("\033[94mFixed interval: 1.0s\033[0m")
        print()

    try:
        if file:
            glitch = "_glitchy" if glitch_on else ""
            filename = f"sine_wave_{int(freq[0])}{glitch}.wav"
            generator.save_to_wav(duration, filename)
            print(f"Saved to {filename}")
        else:
            generator.start(blocking=True)
    except KeyboardInterrupt:
        print("\n\033[93mInterrupted by user\033[0m")
    except Exception as e:
        print(f"\033[91mError during audio operation: {e}\033[0m")
        sys.exit(1)
    finally:
        generator.stop()


if __name__ == "__main__":
    main()
