import random
import threading
from enum import Enum

import numpy as np
import pyaudio
from scipy.io import wavfile


class GlitchType(Enum):
    NONE = 0
    DROPOUT = 1
    SKIP = 2
    FULLSCALE = 3


class SineWaveGenerator:
    """Audio sine wave generator with optional glitch effects.

    Supports real-time audio playback and WAV file generation with configurable
    glitch effects like dropouts, sample skipping, and full-scale clicks.
    """

    DEFAULT_SAMPLE_RATE = 48000
    DEFAULT_CHUNK_SIZE = 1024
    MIN_SAMPLE_RATE = 8000
    MAX_SAMPLE_RATE = 192000
    MAX_CHUNK_SIZE = 8192
    GLITCH_INTERVAL_SECONDS = 1.0
    THREAD_STOP_TIMEOUT = 5.0

    def __init__(
        self,
        sample_rate=DEFAULT_SAMPLE_RATE,
        frequencies=None,
        channels=1,
        amplitude=0.5,
        bitdepth=32,
        chunk_size=DEFAULT_CHUNK_SIZE,
        glitch_type=GlitchType.NONE,
        glitch_size=10,
        blocking=True,
        random_glitch_interval=False,
        glitch_interval_range=(0.5, 2.0),
    ):
        if sample_rate <= 0:
            raise ValueError(f"Sample rate must be positive, got {sample_rate}")
        if not (self.MIN_SAMPLE_RATE <= sample_rate <= self.MAX_SAMPLE_RATE):
            raise ValueError(
                f"Sample rate {sample_rate} Hz is outside typical range ({self.MIN_SAMPLE_RATE}Hz-{self.MAX_SAMPLE_RATE}Hz)"
            )

        if frequencies is None:
            frequencies = [440.0]

        for freq in frequencies:
            if freq <= 0:
                raise ValueError(f"All frequencies must be positive, got {freq}")
            if freq > sample_rate / 2:
                raise ValueError(f"Frequency {freq} Hz exceeds Nyquist limit ({sample_rate / 2} Hz)")

        if not (0.0 <= amplitude <= 1.0):
            raise ValueError(f"Amplitude must be between 0.0 and 1.0, got {amplitude}")

        if channels <= 0:
            raise ValueError(f"Channels must be positive, got {channels}")

        if bitdepth not in [16, 24, 32]:
            raise ValueError(f"Bit depth must be 16, 24, or 32, got {bitdepth}")

        if chunk_size <= 0 or chunk_size > self.MAX_CHUNK_SIZE:
            raise ValueError(f"Chunk size must be positive and <= {self.MAX_CHUNK_SIZE}, got {chunk_size}")

        # Validate glitch interval range
        if glitch_interval_range[0] <= 0 or glitch_interval_range[1] <= 0:
            raise ValueError("Glitch interval range values must be positive")
        if glitch_interval_range[0] > glitch_interval_range[1]:
            raise ValueError("Glitch interval range minimum must be <= maximum")

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
        self.audio_thread = None
        self._pyaudio_instance = None

        self.glitch_type = glitch_type
        self.glitch_size = glitch_size
        self.glitch_timer = 0

        # Glitch interval randomization settings
        self.random_glitch_interval = random_glitch_interval
        self.glitch_interval_range = glitch_interval_range

        # Calculate base glitch interval and set next glitch time
        self.base_glitch_interval_chunks = int(self.GLITCH_INTERVAL_SECONDS * sample_rate / chunk_size)
        self._set_next_glitch_interval()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __del__(self):
        try:
            self.stop()
        except AttributeError:
            pass

    def _set_next_glitch_interval(self):
        """Set the number of chunks until the next glitch occurs."""
        if self.random_glitch_interval:
            # Random interval between min and max range
            random_seconds = random.uniform(self.glitch_interval_range[0], self.glitch_interval_range[1])
            self.next_glitch_chunks = int(random_seconds * self.sample_rate / self.chunk_size)
        else:
            # Use fixed interval
            self.next_glitch_chunks = self.base_glitch_interval_chunks

    def _get_pyaudio_format(self):
        """Convert bit depth to PyAudio format constant."""
        format_map = {16: pyaudio.paInt16, 24: pyaudio.paInt24, 32: pyaudio.paFloat32}
        return format_map.get(self.bitdepth, pyaudio.paFloat32)

    def _generate_sines(self, num_samples):
        """Generate sine wave samples for all frequencies while maintaining phase continuity."""
        delta_theta = (2 * np.pi * np.array(self.frequencies)) / self.sample_rate  # Δθ = 2πf / fs
        theta_matrix = self.thetas[:, None] + np.arange(num_samples) * delta_theta[:, None]
        sine_waves = (self.amplitude * np.sin(theta_matrix)).astype(np.float32)
        self.thetas = (self.thetas + num_samples * delta_theta) % (2 * np.pi)
        return np.column_stack(sine_waves).flatten()

    def _generate_chunk(self):
        """Generate a chunk of sine wave samples with optional glitch effects."""
        interleaved_chunk = self._generate_sines(self.chunk_size)

        if self.glitch_timer >= self.next_glitch_chunks:
            self.glitch_timer = 0
            self._set_next_glitch_interval()
            if self.glitch_type == GlitchType.DROPOUT:
                interleaved_chunk[: self.channels * self.glitch_size] = 0.0

            elif self.glitch_type == GlitchType.SKIP:
                samples_to_skip = self.channels * self.glitch_size
                interleaved_chunk[:-samples_to_skip] = interleaved_chunk[samples_to_skip:]
                new_samples = self._generate_sines(self.glitch_size)
                interleaved_chunk[-len(new_samples) :] = new_samples

            elif self.glitch_type == GlitchType.FULLSCALE:
                fs_sample = -1.0 if interleaved_chunk[0] >= 0.0 else 1.0
                interleaved_chunk[: self.channels * self.glitch_size] = fs_sample
        else:
            self.glitch_timer += 1
        return interleaved_chunk

    def _play_audio(self):
        """Main audio playback loop running in separate thread."""
        self._pyaudio_instance = pyaudio.PyAudio()

        try:
            # Open an audio stream
            self.stream = self._pyaudio_instance.open(
                format=self._get_pyaudio_format(),
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
                # Clean up stream resources
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
                    self.stream = None
        finally:
            # Clean up PyAudio instance
            if self._pyaudio_instance:
                self._pyaudio_instance.terminate()
                self._pyaudio_instance = None

    def start(self, blocking=None):
        """
        Start audio playback in a separate thread.

        Raises:
            RuntimeError: If audio thread is already running.
        """
        if self.audio_thread is not None and self.audio_thread.is_alive():
            raise RuntimeError("Audio thread is already running")

        if blocking is not None:
            self.blocking = blocking

        self.exit_event.clear()  # Reset the event
        self.audio_thread = threading.Thread(target=self._play_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()

        if self.blocking:
            self.audio_thread.join()

    def stop(self):
        """Stop audio playback and clean up resources."""
        if self.audio_thread is None:
            return

        self.exit_event.set()
        if self.audio_thread.is_alive():
            self.audio_thread.join(timeout=self.THREAD_STOP_TIMEOUT)  # Add timeout to prevent hanging
            if self.audio_thread.is_alive():
                print("Warning: Audio thread did not stop gracefully")
        self.audio_thread = None

    def set_amplitude(self, amplitude: float):
        """Set the audio amplitude/volume."""
        if not (0.0 <= amplitude <= 1.0):
            raise ValueError(f"Amplitude must be between 0.0 and 1.0, got {amplitude}")
        self.amplitude = amplitude

    def set_frequencies(self, frequencies: list[float]):
        """Set the sine wave frequencies.

        Args:
            frequencies (list[float]): List of frequencies in Hz
        """
        for freq in frequencies:
            if freq <= 0:
                raise ValueError(f"All frequencies must be positive, got {freq}")
            if freq > self.sample_rate / 2:
                raise ValueError(f"Frequency {freq} Hz exceeds Nyquist limit ({self.sample_rate / 2} Hz)")
        self.frequencies = frequencies
        self.thetas = np.zeros(len(self.frequencies))  # Reset phase tracking

    def save_to_wav(self, duration: int, filename: str):
        """
        Generate and save a sine wave to a WAV file.

        Raises:
            ValueError: If duration is not positive
        """
        if duration <= 0:
            raise ValueError(f"Duration must be positive, got {duration}")
        num_samples = int(self.sample_rate * duration)

        # More efficient: generate all samples at once for clean audio
        if self.glitch_type == GlitchType.NONE:
            samples = self._generate_clean_samples(num_samples)
        else:
            samples = self._generate_samples_with_glitches(num_samples)

        # Reshape and save
        samples = samples.reshape(-1, self.channels)
        wavfile.write(filename, self.sample_rate, samples)

    def _generate_clean_samples(self, num_samples):
        """Generate clean sine wave samples efficiently without glitches."""
        delta_theta = (2 * np.pi * np.array(self.frequencies)) / self.sample_rate
        theta_matrix = self.thetas[:, None] + np.arange(num_samples) * delta_theta[:, None]
        sine_waves = (self.amplitude * np.sin(theta_matrix)).astype(np.float32)
        # Update phase tracking for next call
        self.thetas = (self.thetas + num_samples * delta_theta) % (2 * np.pi)
        return np.column_stack(sine_waves).flatten()

    def _generate_samples_with_glitches(self, num_samples):
        """Generate samples with glitches using optimized chunked approach."""
        num_chunks = num_samples // self.chunk_size
        remaining_samples = num_samples % self.chunk_size

        # Pre-allocate array for better performance
        total_samples_needed = num_samples * self.channels
        all_samples = np.empty(total_samples_needed, dtype=np.float32)

        # Generate chunks
        offset = 0
        for _ in range(num_chunks):
            chunk = self._generate_chunk()
            chunk_size = len(chunk)
            all_samples[offset : offset + chunk_size] = chunk
            offset += chunk_size

        # Handle remaining samples
        if remaining_samples > 0:
            original_chunk_size = self.chunk_size
            self.chunk_size = remaining_samples
            try:
                chunk = self._generate_chunk()
                chunk_size = len(chunk)
                all_samples[offset : offset + chunk_size] = chunk
            finally:
                self.chunk_size = original_chunk_size

        return all_samples
