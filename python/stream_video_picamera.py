from picamera2 import Picamera2
from flask import Flask, Response
import cv2
import numpy as np
import time
import threading
from collections import deque 

app = Flask(__name__)

# Initialize camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (800, 600)})
picam2.configure(config)
picam2.start()

# Global variables
frame = None
frame_lock = threading.Lock()

last_frame = None

movement_start_time = None
pixel_change_sum = 0

FRAME_RATE = 20.0 # Hz
BUFFER_TIME_WINDOW = 1.0 # sec
BUFFER_SIZE = int(BUFFER_TIME_WINDOW * FRAME_RATE)
pixel_change_buffer = deque(maxlen=BUFFER_SIZE)

def process_frame(frame):
    global last_frame
    if last_frame is None:
        last_frame = frame
        return

    frame_diff = cv2.absdiff(last_frame, frame)

    # Mask out a polygon
    pixel_locations = [(100, 100), (600, 150), (550, 500), (100, 500)]  # Rectangle
    points = np.array([pixel_locations], dtype=np.int32)
    cv2.fillPoly(frame_diff, points, 0)

    thresh = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)

    thresh = cv2.threshold(thresh, 30, 255, cv2.THRESH_BINARY)[1]

    # thresh = cv2.dilate(thresh, None, iterations=2)

    # contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # print(f"Got {len(contours)} contours.")
    
    # # Check for significant movement
    # significant_movement = False
    # MIN_CONTOUR_AREA = 500
    # for contour in contours:
    #     if cv2.contourArea(contour) > MIN_CONTOUR_AREA:
    #         significant_movement = True
    #         # Draw rectangle around movement (optional)
    #         x, y, w, h = cv2.boundingRect(contour)
    #         cv2.rectangle(frame_diff, (x, y), (x+w, y+h), (0, 255, 0), 2)
    #         break

    # Count changed pixels
    changed_pixels = cv2.countNonZero(thresh)

    global pixel_change_buffer
    pixel_change_buffer.append(changed_pixels)

    total_pixel_change = sum(pixel_change_buffer)

    PIXEL_CHANGE_THRESHOLD = 10000  # Minimum number of changed pixels per frame
    HIT_RATIO_TO_TRIGGER = 0.5
    ACCUM_PIXEL_THRESHOLD = PIXEL_CHANGE_THRESHOLD * HIT_RATIO_TO_TRIGGER * BUFFER_SIZE
    movement_detected = False
    if total_pixel_change > ACCUM_PIXEL_THRESHOLD:
        movement_detected = True
        pixel_change_buffer.clear()
    
    # Display status
    status = f"Movement: {movement_detected} (Pixels: {total_pixel_change} of {ACCUM_PIXEL_THRESHOLD}) "
    cv2.putText(frame_diff, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                1, (0, 0, 255) if movement_detected else (255, 0, 0), 2)
    cv2.polylines(frame_diff, points, isClosed=True, color=(0, 255, 0), thickness=2)

    last_frame = frame

    return frame_diff

def capture_frames():
    global frame
    while True:
        current_frame = picam2.capture_array()
        # Convert to BGR format for OpenCV
        current_frame = cv2.cvtColor(current_frame, cv2.COLOR_RGBA2BGR)

        print("processing frame.")
        display_frame = process_frame(current_frame)

        with frame_lock:
            frame = display_frame
        
        time.sleep(1.0/FRAME_RATE)  # ~20 FPS

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