import os
import cv2
import ssl
import time
import datetime
import picamera2
from OpenSSL import SSL
from dotenv import load_dotenv
from flask import Flask, Response
from flask_limiter import Limiter
from flask_httpauth import HTTPBasicAuth
from flask_login import LoginManager, UserMixin
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash


# Initialize app and auth
app = Flask(__name__)
auth = HTTPBasicAuth()

# log in credentials 
load_dotenv('./credentials/logcred.env')

# Replace these with your own username and password
USERNAME = os.environ.get('CAMERA_USERNAME')
PASSWORD = os.environ.get('CAMERA_PASSWORD')

# Limiter setup to prevent overuse
limiter = Limiter(app=app, key_func=get_remote_address)

# initialize camera
picam2 = picamera2.Picamera2()
config = cam.create_preview_configuration()
cam.configure(config)
cam.start()

# Exit function
def stop_cam(cam):
    cam.stop()
    cam.close()
return None

# Function to generate frames from the camera
def generate_frames():
    frame_counter = 0  # To count frames
    while True:
        try:
            # Capture a frame from the camera
            frame = picam2.capture_array()

            # Convert the frame from RGBA to BGR (OpenCV default)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

            # Save every 10th frame to the USB drive
            if frame_counter % 10 == 0:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                savepath = f"/home/kit/project1/cameraimg/captured_{timestamp}.jpg"
                cv2.imwrite(savepath, frame)

            frame_counter += 1
        except:
            print("Error during image generation...")
            break
            
        try:
            # Encode the frame as JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
            ret, buffer = cv2.imencode('.jpg', frame, encode_param)

            # Convert the frame buffer to bytes
            frame = buffer.tobytes()

            # Yield the frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            # Sleep to control the frame rate
            time.sleep(0.1)
        except:
            print("Error during streaming...")
            break
# used to manage connection attempts
PASSWORD_HASH = generate_password_hash(str(PASSWORD))

# Function to verify the username and password
@auth.verify_password
def verify_password(username, password):
    if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
        return True
    return False

# Route to serve the video stream with authentication
@app.route('/')
@limiter.limit("10 per minute")
@auth.login_required
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Start the camera and app when the script is run
if __name__ == '__main__':
    try:
        picam2.start()
        # Specify your SSL certificate and key files
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1
        context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384')
        context.load_cert_chain(certfile='./credentials/server.crt', keyfile='./credentials/server.key')
        # Start Flask app with SSL (HTTPS)
        app.run(host='0.0.0.0', port=8000, ssl_context=context)
    except:
        print("An error occured .. shutting down ..")
    finally:
        stop_cam(cam)
