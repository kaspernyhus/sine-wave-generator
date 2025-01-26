# SineWaveGenerator
Generate a .wav file containing one or more channels of sine waves or a stream.

## Setup
Using poetry
```
poetry install
```

### Arguments
```
poetry run sine --help
```

### Example
Generate a 10 second wave file with 2 channels, 442Hz in left 1000Hz in right, volume=0.5
```
poetry run sine -w -c 2 -f 442 1000 -v 0.5 -d 10
```

A stream with glitches
```
poetry run sine -g --dropout
```
