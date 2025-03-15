import pyaudio
import wave
import time
import argparse
import sys

def record_audio(output_file="recording.wav", duration=5, sample_rate=44100, channels=1, chunk=512):
    """
    Record audio from the default input device (webcam microphone)
    
    Args:
        output_file (str): Output WAV file path
        duration (int): Recording duration in seconds
        sample_rate (int): Audio sample rate
        channels (int): Number of audio channels (1=mono, 2=stereo)
        chunk (int): Frames per buffer
    """
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # Get information about available devices
    print("\nAvailable audio input devices:")
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:  # Only show input devices
            print(f"Device {i}: {dev_info['name']}")
    
    # Ask user to select device
    device_index = int(input("\nEnter the device index for your webcam microphone: "))
    
    # Get device info to confirm selection
    device_info = p.get_device_info_by_index(device_index)
    print(f"\nSelected device: {device_info['name']}")
    
    print("\n========== Device Information ==========")
    print(f"Device: {device_info['name']}")
    print(f"Index: {device_index}")
    print(f"Default Sample Rate: {int(device_info['defaultSampleRate'])} Hz")
    print(f"Max Input Channels: {device_info['maxInputChannels']}")
    
    # Open audio stream
    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=sample_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=chunk
    )

    stream.start_stream()
    
    print(f"\nRecording {duration} seconds of audio...")
    frames = []
    
    # Record audio in chunks
    for i in range(0, int(sample_rate / chunk * duration)):
        try:
            data = stream.read(chunk)
        except OSError as error:
            print("OSError Exception. Probably buffer overflow, please adapt the chunk size. terminating program.")
            sys.exit()
        frames.append(data)
        # Display progress
        if i % 10 == 0:
            print(f"Recording: {i*chunk/sample_rate:.1f}/{duration} seconds", end="\r")
    
    print("\nFinished recording!")
    
    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save to WAV file
    print(f"Saving to {output_file}...")
    wf = wave.open(output_file, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    print(f"Audio saved to {output_file}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Record audio from webcam microphone")
    parser.add_argument("-o", "--output", default="recording.wav", help="Output WAV file path")
    parser.add_argument("-d", "--duration", type=int, default=5, help="Recording duration in seconds")
    parser.add_argument("-r", "--rate", type=int, default=44100, help="Sample rate")
    parser.add_argument("-c", "--channels", type=int, default=1, help="Number of channels (1=mono, 2=stereo)")
    
    args = parser.parse_args()
    
    record_audio(
        output_file=args.output,
        duration=args.duration,
        sample_rate=args.rate,
        channels=args.channels
    )