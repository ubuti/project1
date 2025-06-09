# Testing imports
try:
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
    print("Import's working OK")
except Exception as e:
    print(f"Import error: {e}")

# Test write access
try:
    
    with open("../storagepath", 'r') as t:
        path = t.read()
    path = path.replace("\n", "")
    path_testdir = os.path.join(path, "test")
    os.makedirs(path_testdir, exist_ok=True)
    test_file = os.path.join(path_testdir, "test.txt")
    print("Creating file")
    with open(test_file, 'w') as f:
        f.write("USB write test")
    print("USB write permissions OK")
except Exception as e:
    print(f"USB write error: {e}")

# Test image captioring
try:
    cam = picamera2.Picamera2()
    config = cam.create_preview_configuration()
    cam.configure(config)
    cam.start()
    frame = cam.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
    savepath = os.path.join(path_testdir, "test.jpg")
    cv2.imwrite(savepath, frame)
    print("Image write to usb OK ")
except Exception as e:
    print(f"USB write error: {e}")
finally:
    f.close()
    t.close()
    cam.stop()
    cam.close()
    print("End of test")
