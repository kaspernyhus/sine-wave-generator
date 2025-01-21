import threading

import numpy as np
import pyaudio
from scipy.io import wavfile
import scipy.io.wavfile as wavfile


class SineWaveGenerator:
    def __init__(
        self,
        sample_rate=48000,
        frequencies=[440.0],
        channels=1,
        amplitude=0.5,
        bitdepth=32,
        chunk_size=1024,
        glitch=False,
        glitch_size=4,
        glitch_zeros=False,
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
        self.chunk_index = 0
        self.stream = None
        self.exit_event = threading.Event()
        self.blocking = blocking
        self.audio_thread = threading.Thread(target=self._play_audio)
        self.audio_thread.daemon = True
        self.glitch_active = glitch
        self.glitch_size = glitch_size
        self.glitch_zeros = glitch_zeros
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

    def _generate_chunk(self):
        """Generate a chunk of sine wave samples for multiple channels with different frequencies, interleaved.
        Introduces a glitch effect at a periodic interval.
        """
        if len(self.frequencies) != self.channels:
            self.frequencies = self.frequencies * self.channels

        t = (np.arange(self.chunk_size) + self.chunk_index * self.chunk_size) / self.sample_rate
        sine_waves = [(self.amplitude * np.sin(2 * np.pi * freq * t)).astype(np.float32) for freq in self.frequencies]
        interleaved_chunk = np.column_stack(sine_waves).flatten()

        if self.glitch_active:
            if self.glitch_timer <= 0:
                self.glitch_timer = self.sample_rate / self.chunk_size
                if self.glitch_zeros:
                    interleaved_chunk = np.zeros(self.channels * self.glitch_size, dtype=np.float32)
                else:
                    for i in range(self.channels * self.glitch_size):
                        if interleaved_chunk[i] < 0.0:
                            interleaved_chunk[i] = 1.0
                        else:
                            interleaved_chunk[i] = -1.0
            else:
                self.glitch_timer -= 1

        self.chunk_index += 1
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
