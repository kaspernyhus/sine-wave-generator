# Sine Wave Generator
Generate a .wav file containing one or more channels of sine waves or a stream.

## Setup
Using uv
```
uv sync
```

### Arguments
```
uv run sine-wave-generator --help
```

### Example
Generate a 10 second wave file with 2 channels, 442Hz in left 1000Hz in right, volume=0.5
```
uv run sine-wave-generator -w -c 2 -f 442 1000 -v 0.5 -d 10
```

A stream with glitches
```
uv run sine-wave-generator -g --dropout
```
