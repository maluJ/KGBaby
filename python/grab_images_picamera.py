from picamera2 import Picamera2
import time

# Initialize the camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (800, 600)})
picam2.configure(config)
picam2.start()

# Allow time for the camera to initialize
time.sleep(2)

try:
    while True:
        # Capture an image
        frame = picam2.capture_array()
        
        # Do your processing here
        # For example, analyze the image, extract features, etc.
        print(f"Captured frame with shape: {frame.shape}")
        
        # Control capture speed
        time.sleep(0.1)  # 10 frames per second
        
except KeyboardInterrupt:
    print("Capture stopped by user")
finally:
    picam2.stop()