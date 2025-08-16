# Sine Wave Generator
Generate sine waves as audio streams or WAV files with optional glitch injection.

## Setup
Using uv
```
uv sync
```

## Basic Usage

### Arguments
```
uv run sine-wave-generator --help
```

### Examples

Generate a basic 440Hz sine wave (live audio):
```
uv run sine-wave-generator
```

Generate a 10 second stereo WAV file (442Hz left, 1000Hz right, 50% volume):
```
uv run sine-wave-generator -w -c 2 -f 442 1000 -v 0.5 -d 10
```

## Glitch Effects

The sine wave generator includes glitch effects to simulate various audio artifacts.

### Glitch Types

**Dropout** (`--dropout [samples]`): Inserts periods of silence (digital dropouts)
```
uv run sine-wave-generator --dropout        # Default: 100 samples
uv run sine-wave-generator --dropout 10     # 10 samples of silence for every glitch
```

**Skip** (`--skip [samples]`): Skips audio samples, creating discontinuities
```
uv run sine-wave-generator --skip           # Default: 10 samples
uv run sine-wave-generator --skip 1         # Skip 1 samples
```

**Fullscale** (`--fullscale [samples]`): Inserts full-scale (1.0/-1.0) sample digital clips/clicks
```
uv run sine-wave-generator --fullscale      # Default: 5 samples
uv run sine-wave-generator --fullscale 2    # 2 full-scale samples
```

### Glitch Timing

**Fixed Intervals** (default): Glitches occur every ~1 second
```
uv run sine-wave-generator --dropout        # Fixed 1.0s intervals
```

**Random Intervals**: Glitches occur at randomized intervals for more realistic artifacts
```
uv run sine-wave-generator --skip --random-interval                    # Random 0.5-2.0s intervals
uv run sine-wave-generator --dropout --random-interval --interval-range 0.2 1.5  # Custom range
```
