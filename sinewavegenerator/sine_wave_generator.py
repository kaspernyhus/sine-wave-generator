import threading
from enum import Enum

import numpy as np
import pyaudio
from scipy.io import wavfile
import scipy.io.wavfile as wavfile


class GlitchType(Enum):
    NONE = 0
    DROPOUT = 1
    SKIP = 2
    FULLSCALE = 3


class SineWaveGenerator:
    def __init__(
        self,
        sample_rate=48000,
        frequencies=[440.0],
        channels=1,
        amplitude=0.5,
        bitdepth=32,
        chunk_size=1024,
        glitch_type=GlitchType.NONE,
        glitch_size=10,
        blocking=True,
    ):
        self.sample_rate = sample_rate
        self.frequencies = frequencies
        self.amplitude = amplitude
        self.channels = channels
        if len(self.frequencies) != self.channels:
            self.channels = len(self.frequencies)
        self.bitdepth = bitdepth
        self.chunk_size = chunk_size
        self.thetas = np.zeros(len(self.frequencies))

        self.stream = None
        self.exit_event = threading.Event()
        self.blocking = blocking
        self.audio_thread = threading.Thread(target=self._play_audio)
        self.audio_thread.daemon = True

        self.glitch = glitch_type
        self.glitch_size = glitch_size
        self.glitch_timer = 0

    def _get_bitdepth(self):
        if self.bitdepth == 16:
            return pyaudio.paInt16
        elif self.bitdepth == 24:
            return pyaudio.paInt24
        elif self.bitdepth == 32:
            return pyaudio.paFloat32
        else:
            return pyaudio.paFloat32

    def _generate_sines(self, num_samples):
        """Generate sine wave samples for all frequencies while maintaining phase continuity."""
        delta_theta = (2 * np.pi * np.array(self.frequencies)) / self.sample_rate  # Δθ = 2πf / fs
        theta_matrix = self.thetas[:, None] + np.arange(num_samples) * delta_theta[:, None]
        sine_waves = (self.amplitude * np.sin(theta_matrix)).astype(np.float32)
        self.thetas = (self.thetas + num_samples * delta_theta) % (2 * np.pi)
        return np.column_stack(sine_waves).flatten()

    def _generate_chunk(self):
        """Generate a chunk of sine wave samples, introducing glitches when necessary."""
        interleaved_chunk = self._generate_sines(self.chunk_size)

        if self.glitch_timer > self.sample_rate / self.chunk_size:
            self.glitch_timer = 0
            if self.glitch == GlitchType.DROPOUT:
                interleaved_chunk[: self.channels * self.glitch_size] = 0.0

            elif self.glitch == GlitchType.SKIP:
                interleaved_chunk = interleaved_chunk[self.channels * self.glitch_size :]
                new_samples = self._generate_sines(self.glitch_size)
                interleaved_chunk = np.concatenate((interleaved_chunk, new_samples))

            elif self.glitch == GlitchType.FULLSCALE:
                fs_sample = -1.0 if interleaved_chunk[0] >= 0.0 else 1.0
                interleaved_chunk[: self.channels * self.glitch_size] = fs_sample
        else:
            self.glitch_timer += 1
        return interleaved_chunk

    def _play_audio(self):
        p = pyaudio.PyAudio()

        # Open an audio stream
        self.stream = p.open(
            format=self._get_bitdepth(),
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.chunk_size,
        )

        self.chunk_index = 0

        try:
            while not self.exit_event.is_set():
                sine_wave_chunk = self._generate_chunk()
                self.stream.write(sine_wave_chunk.tobytes())
        finally:
            # Clean up resources
            self.stream.stop_stream()
            self.stream.close()
            p.terminate()
            print("Audio stream closed and resources cleaned up.")

    def start(self, blocking=None):
        print("Starting audio thread...")
        if blocking is not None:
            self.blocking = blocking
        self.audio_thread.start()
        if self.blocking:
            self.audio_thread.join()

    def stop(self):
        print("Stopping audio thread...")
        self.exit_event.set()
        self.audio_thread.join()

    def set_amplitude(self, amplitude: float):
        self.amplitude = amplitude

    def set_frequencies(self, frequencies: list[float]):
        self.frequencies = frequencies

    def save_to_wav(self, duration: int, filename: str):
        """Generate and save a sine wave to a WAV file for the given duration."""
        num_samples = int(self.sample_rate * duration)
        num_chunks = num_samples // self.chunk_size  # How many full chunks to generate
        remaining_samples = num_samples % self.chunk_size  # Remaining samples
        all_samples = []
        for _ in range(num_chunks):
            chunk = self._generate_chunk()
            all_samples.append(chunk)
        if remaining_samples > 0:
            self.chunk_size = remaining_samples  # Temporarily set chunk size
            chunk = self._generate_chunk()
            all_samples.append(chunk)
        samples = np.concatenate(all_samples).reshape(-1, self.channels)
        wavfile.write(filename, self.sample_rate, samples)
