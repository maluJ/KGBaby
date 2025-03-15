from picamera2 import Picamera2
from flask import Flask, Response
import cv2
import numpy as np
import time
import threading

app = Flask(__name__)

# Initialize camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (800, 600)})
picam2.configure(config)
picam2.start()

# Global variables
frame = None
frame_lock = threading.Lock()

def capture_frames():
    global frame
    while True:
        current_frame = picam2.capture_array()
        # Convert to BGR format for OpenCV
        current_frame = cv2.cvtColor(current_frame, cv2.COLOR_RGBA2BGR)
        with frame_lock:
            frame = current_frame
        time.sleep(0.05)  # ~20 FPS

@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>Raspberry Pi Camera Stream</title>
    </head>
    <body>
        <h1>Raspberry Pi Camera Stream</h1>
        <img src="/stream" width="800" height="600" />
    </body>
    </html>
    """

@app.route('/stream')
def stream():
    def generate_frames():
        global frame
        while True:
            with frame_lock:
                if frame is not None:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.05)

    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Start the frame capture thread
    thread = threading.Thread(target=capture_frames)
    thread.daemon = True
    thread.start()
    
    # Start the Flask server
    print("Starting server at http://0.0.0.0:8000")
    app.run(host='0.0.0.0', port=8000, debug=False)