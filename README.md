# SineWaveGenerator

Generate a .wav file containing one or more channels of sine waves.

### Create Virtual Environment
```
python -m venv venv/
```

### Install dependencies
```
pip install -r requirements.txt
```

### Arguments

```
python generate_sine.py --help
```
```
usage: generate_sine.py [-h] [-r SAMPLE_RATE] [-c CHANNELS] [-f FREQUENCIES [FREQUENCIES ...]] [-v VOLUME] [-d DURATION] [-m MODE]

Sine generator

options:
  -h, --help            show this help message and exit
  -r SAMPLE_RATE, --sample_rate SAMPLE_RATE
                        Sample Rate
  -c CHANNELS, --channels CHANNELS
                        Number of channels
  -f FREQUENCIES [FREQUENCIES ...], --frequencies FREQUENCIES [FREQUENCIES ...]
                        Sine frequencies
  -v VOLUME, --volume VOLUME
                        Volume
  -d DURATION, --duration DURATION
                        Duration [ms]
  -m MODE, --mode MODE  Mode: 'wav' = wav file, 'bin' = binary file or 'stream'
```

#### Example
```
python generate_sine.py -c 2 -f 442 1000 -v 0.5 -d 1000 -m wav
```
