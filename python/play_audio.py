import pyaudio
import wave
import argparse
import sys
import time

def list_audio_devices():
    """List all available audio output devices"""
    p = pyaudio.PyAudio()
    
    print("\nAvailable audio output devices:")
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info['maxOutputChannels'] > 0:  # Only show output devices
            print(f"Device {i}: {dev_info['name']}")
    
    p.terminate()

def play_wav(file_path, device_index=None):
    """
    Play a WAV file through the specified audio device
    
    Args:
        file_path (str): Path to the WAV file
        device_index (int, optional): Index of the audio device to use
    """
    try:
        # Open the WAV file
        wf = wave.open(file_path, 'rb')
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return
    except wave.Error:
        print(f"Error: '{file_path}' is not a valid WAV file.")
        return
    
    # Get WAV file properties
    channels = wf.getnchannels()
    sample_width = wf.getsampwidth()
    frame_rate = wf.getframerate()
    
    # Print audio file information
    print(f"\nAudio file: {file_path}")
    print(f"Channels: {channels}")
    print(f"Sample width: {sample_width} bytes")
    print(f"Frame rate: {frame_rate} Hz")
    print(f"Total frames: {wf.getnframes()}")
    duration = wf.getnframes() / float(frame_rate)
    print(f"Duration: {duration:.2f} seconds")
    
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    # If no device specified, ask user to select one
    if device_index is None:
        list_audio_devices()
        device_index = int(input("\nEnter the device index for your USB speaker: "))
    
    # Get format from sample width
    format_map = {
        1: pyaudio.paInt8,
        2: pyaudio.paInt16,
        3: pyaudio.paInt24,
        4: pyaudio.paInt32
    }
    audio_format = format_map.get(sample_width, pyaudio.paInt16)
    
    # Get device info to confirm selection
    try:
        device_info = p.get_device_info_by_index(device_index)
        print(f"\nPlaying through: {device_info['name']}")
        print(f"    Default sample rate: {int(device_info['defaultSampleRate'])} Hz")
        print(f"    Max output channels: {device_info['maxOutputChannels']}")
    except:
        print("Invalid device index. Using default output device.")
        device_index = p.get_default_output_device_info()['index']
        device_info = p.get_device_info_by_index(device_index)
        print(f"Default device: {device_info['name']}")

    # Create and open the output stream
    chunk_size = 1024
    stream = p.open(
        format=audio_format,
        channels=channels,
        rate=frame_rate,
        output=True,
        output_device_index=device_index,
        frames_per_buffer=chunk_size
    )
    
    # Play the audio file
    print("\nPlaying audio... Press Ctrl+C to stop.")
    print("0%", end="")
    
    try:
        data = wf.readframes(chunk_size)
        frames_played = 0
        total_frames = wf.getnframes()
        
        while data:
            stream.write(data)
            data = wf.readframes(chunk_size)
            frames_played += chunk_size
            
            # Update progress bar
            progress = min(100, int(frames_played * 100 / total_frames))
            sys.stdout.write(f"\r{progress}% {'█' * (progress // 5)}{' ' * (20 - progress // 5)}")
            sys.stdout.flush()
            
    except KeyboardInterrupt:
        print("\nPlayback stopped by user.")
    except Exception as e:
        print(f"\nError during playback: {e}")
    finally:
        # Clean up
        stream.stop_stream()
        stream.close()
        wf.close()
        p.terminate()
        print("\nPlayback complete.")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Play WAV audio file through USB speaker")
    parser.add_argument("file", nargs="?", help="Path to WAV file to play")
    parser.add_argument("-d", "--device", type=int, help="Audio device index")
    parser.add_argument("-l", "--list", action="store_true", help="List available audio devices")
    
    args = parser.parse_args()
    
    # If list option is specified, just list devices and exit
    if args.list:
        list_audio_devices()
        sys.exit(0)
    
    # Check if file is provided
    if not args.file:
        parser.print_help()
        sys.exit(1)
    
    # Play the specified audio file
    play_wav(args.file, args.device)