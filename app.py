import os
import ssl
import time
import warnings
import datetime
import threading
from queue import Queue, Empty
from pathlib import Path

import cv2
import picamera2
from flask import Flask, Response
from flask_httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Suppress Flask-Limiter warning
warnings.filterwarnings("ignore", message="Using the in-memory storage for tracking rate limits")

# Initialize app and auth
app = Flask(__name__)
auth = HTTPBasicAuth()

# Load credentials
load_dotenv('./credentials/logcred.env')
USERNAME = os.environ.get('CAMERA_USERNAME')
PASSWORD = os.environ.get('CAMERA_PASSWORD')

if not USERNAME or not PASSWORD:
    raise ValueError("CAMERA_USERNAME and CAMERA_PASSWORD must be set in environment")

# Limiter setup
limiter = Limiter(app=app, key_func=get_remote_address)

# Global variables
picam2 = None
frame_queue = Queue(maxsize=10)  # Limit queue size to prevent memory buildup
save_queue = Queue(maxsize=50)   # Queue for saving frames
shutdown_event = threading.Event()

# Configuration
SAVE_PATH = Path("/home/kit/project1/cameraimg")
JPEG_QUALITY = 60
FRAME_RATE = 10  # FPS
SAVE_EVERY_N_FRAMES = 10

# Ensure save directory exists
SAVE_PATH.mkdir(parents=True, exist_ok=True)

def initialize_camera():
    """Initialize camera with error handling"""
    global picam2
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            picam2 = picamera2.Picamera2()
            config = picam2.create_preview_configuration(
                main={"size": (640, 480)}  # Reduce resolution for better performance
            )
            picam2.configure(config)
            picam2.start()
            print("Camera initialized successfully")
            return True
        except Exception as e:
            print(f"Camera initialization attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return False
    return False

def stop_camera():
    """Safely stop camera"""
    global picam2
    try:
        if picam2:
            picam2.stop()
            picam2.close()
            print("Camera stopped safely")
    except Exception as e:
        print(f"Error stopping camera: {e}")

def save_frame_worker():
    """Background thread worker for saving frames"""
    while not shutdown_event.is_set():
        try:
            frame_data = save_queue.get(timeout=1)
            if frame_data is None:  # Poison pill
                break
                
            frame, timestamp = frame_data
            filename = f"captured_{timestamp}.jpg"
            filepath = SAVE_PATH / filename
            
            # Use higher quality for saved images
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
            success = cv2.imwrite(str(filepath), frame, encode_param)
            
            if success:
                print(f"Saved frame: {filename}")
            else:
                print(f"Failed to save frame: {filename}")
                
        except Empty:
            continue
        except Exception as e:
            print(f"Error in save worker: {e}")

def capture_frames():
    """Capture frames from camera and put them in queue"""
    frame_counter = 0
    
    while not shutdown_event.is_set():
        try:
            if not picam2:
                time.sleep(0.1)
                continue
                
            # Capture frame
            frame = picam2.capture_array()
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
            
            # Save every Nth frame (non-blocking)
            if frame_counter % SAVE_EVERY_N_FRAMES == 0:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
                try:
                    save_queue.put_nowait((frame_bgr.copy(), timestamp))
                except:
                    pass  # Queue full, skip this save
            
            # Encode for streaming (lower quality)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY]
            ret, buffer = cv2.imencode('.jpg', frame_bgr, encode_param)
            
            if ret:
                frame_bytes = buffer.tobytes()
                
                # Put in queue (non-blocking)
                try:
                    frame_queue.put_nowait(frame_bytes)
                except:
                    # Queue full, remove oldest frame and add new one
                    try:
                        frame_queue.get_nowait()
                        frame_queue.put_nowait(frame_bytes)
                    except:
                        pass
            
            frame_counter += 1
            time.sleep(1.0 / FRAME_RATE)  # Control frame rate
            
        except Exception as e:
            print(f"Error capturing frame: {e}")
            time.sleep(0.5)  # Brief pause on error

def generate_frames():
    """Generate frames for streaming from queue"""
    while not shutdown_event.is_set():
        try:
            # Get frame from queue with timeout
            frame_bytes = frame_queue.get(timeout=1)
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                   
        except Empty:
            # No frame available, yield empty frame or continue
            continue
        except Exception as e:
            print(f"Error generating frame: {e}")
            break

# Password verification
PASSWORD_HASH = generate_password_hash(str(PASSWORD))

@auth.verify_password
def verify_password(username, password):
    return username == USERNAME and check_password_hash(PASSWORD_HASH, password)

@app.route('/')
@limiter.limit("30 per minute")  # Increased limit for better user experience
@auth.login_required
def video():
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return {'status': 'ok', 'camera': picam2 is not None}

def setup_ssl_context():
    """Configure SSL context with security best practices"""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    
    # Disable insecure protocols
    context.options |= ssl.OP_NO_SSLv2
    context.options |= ssl.OP_NO_SSLv3
    context.options |= ssl.OP_NO_TLSv1
    context.options |= ssl.OP_NO_TLSv1_1
    
    # Set secure ciphers
    context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256')
    
    # Load certificates
    cert_path = Path('./credentials/server.crt')
    key_path = Path('./credentials/server.key')
    
    if not cert_path.exists() or not key_path.exists():
        raise FileNotFoundError("SSL certificate or key file not found")
        
    context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
    return context

def cleanup():
    """Cleanup function"""
    print("Shutting down...")
    shutdown_event.set()
    
    # Stop save queue
    save_queue.put(None)  # Poison pill
    
    # Stop camera
    stop_camera()

if __name__ == '__main__':
    # Start background threads
    save_thread = threading.Thread(target=save_frame_worker, daemon=True)
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    
    try:
        # Initialize camera
        if not initialize_camera():
            print("Failed to initialize camera. Exiting.")
            exit(1)
        
        # Start threads
        save_thread.start()
        capture_thread.start()
        
        # Setup SSL
        ssl_context = setup_ssl_context()
        
        print("Starting Flask app on https://0.0.0.0:8000")
        app.run(
            host='0.0.0.0', 
            port=8000, 
            ssl_context=ssl_context,
            threaded=True,
            debug=False  # Disable debug in production
        )
        
    except KeyboardInterrupt:
        print("Received interrupt signal")
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        cleanup()
