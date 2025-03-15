import pyaudio
import threading
import queue
import numpy as np
import time
from collections import deque
from datetime import datetime

# Audio parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100  # Sample rate for audio recording
CHUNK = 512  # Chunk size for reading audio
THRESHOLD = 2000  # Volume threshold for detecting a scream

# Time and Success parameters
OBSERVATION_TIME = 2  # Time in seconds over which to observe (window size)
SUCCESS_RATE = 50  # Percentage of successful detections required within the window to trigger
LOG_FILE = "screams_log.txt"  # File to log ISO timestamps when scream is detected

# Queue for audio data
audio_queue = queue.Queue()

# Ring buffer to store scream detection results (0 or 1)
BUFFER_SIZE = int(RATE * OBSERVATION_TIME / CHUNK)
ring_buffer = deque(maxlen=BUFFER_SIZE)  # Stores success values (1 or 0)

# State variables
scream_detected = False  # Flag to track if a valid scream has been detected

def detect_scream(audio_data):
    """Checks if the volume exceeds the threshold."""
    samples = np.frombuffer(audio_data, dtype=np.int16)
    volume = np.abs(samples).mean()  # Calculate average volume
    return volume > THRESHOLD

def calculate_success_rate():
    """Calculate the success rate of scream detections within the window."""
    successes = sum(ring_buffer)  # Count the number of successful detections (1s)
    total = len(ring_buffer)  # Total number of observations in the buffer
    return (successes / total) * 100 # Return percentage

def log_scream_event():
    """Log the timestamp of the scream detection event."""
    timestamp = datetime.now().isoformat()  # Get the current timestamp in ISO format
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"Scream detected at {timestamp}\n")  # Write to log file
    print(f"Scream event logged at {timestamp}")

def audio_recording():
    """Runs in a separate thread and continuously records audio."""
    global scream_detected
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)

    print("Scream detection started...")

    try:
        while recording:
            data = stream.read(CHUNK)
            audio_queue.put(data)  # Store data in queue

            # Detect scream and store result in ring buffer (1 for scream detected, 0 for no scream)
            scream_detected_result = detect_scream(data)
            ring_buffer.append(1 if scream_detected_result else 0)

            current_success_rate = 0
            # Calculate the current success rate if the buffer is full
            if (len(ring_buffer) == BUFFER_SIZE):
                current_success_rate = calculate_success_rate()

            # Check if the success rate exceeds the threshold to trigger the scream detection
            if current_success_rate >= SUCCESS_RATE:
                print(f"Scream detected! (Success rate: {current_success_rate:.2f}%)")
                log_scream_event()  # Log the scream event
                # Reset the buffer after logging
                ring_buffer.clear()
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Recording stopped.")

# Start recording in a separate thread
recording = True
audio_thread = threading.Thread(target=audio_recording, daemon=True)
audio_thread.start()
print("Scream detection started.")

try:
    while True:
        pass  # Main thread can perform other tasks here
except KeyboardInterrupt:
    recording = False  # Stop recording
    audio_thread.join()
    print("Program terminated.")
