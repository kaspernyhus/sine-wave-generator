import pyaudio
import numpy as np
import threading
import signal
import sys
import time

class SineWaveGenerator:
    def __init__(self, sample_rate=48000, frequency=440, amplitude=0.5, chunk_size=1024, glitch=False):
        self.sample_rate = sample_rate
        self.frequency = frequency
        self.amplitude = amplitude
        self.chunk_size = chunk_size
        self.stream = None
        self.exit_event = threading.Event()
        self.audio_thread = threading.Thread(target=self._play_audio)
        self.audio_thread.daemon = True
        self.glitch_active = glitch
        self.glitch_timer = 0

    def _generate_chunk(self):
        """Generate a chunk of sine wave samples."""
        t = (np.arange(self.chunk_size) + self.chunk_index * self.chunk_size) / self.sample_rate
        sine_wave_chunk = self.amplitude * np.sin(2 * np.pi * self.frequency * t).astype(np.float32)
        self.chunk_index += 1
        if self.glitch_active:
            if self.glitch_timer <= 0:
                self.glitch_timer = self.sample_rate / self.chunk_size
                sine_wave_chunk = np.zeros_like(sine_wave_chunk)
            else:
                self.glitch_timer -= 1
        return sine_wave_chunk

    def _play_audio(self):
        p = pyaudio.PyAudio()

        # Open an audio stream
        self.stream = p.open(format=pyaudio.paFloat32,
                             channels=1,
                             rate=self.sample_rate,
                             output=True,
                             frames_per_buffer=self.chunk_size)

        self.chunk_index = 0  # Used to keep track of sample position in the sine wave

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

    def start(self):
        print("Starting audio thread...")
        self.audio_thread.start()

    def stop(self):
        print("Stopping audio thread...")
        self.exit_event.set()
        self.audio_thread.join()

    def set_amplitude(self, amplitude: float):
        self.amplitude = amplitude

    def set_frequency(self, frequency: int):
        self.frequency = frequency


if __name__ == "__main__":

    def signal_handler(sig, frame):
        print("\nCtrl+C pressed, shutting down...")
        generator.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    generator = SineWaveGenerator(sample_rate=48000, frequency=440, chunk_size=1024)
    generator.start()

    while not generator.exit_event.is_set():
        time.sleep(0.1)
