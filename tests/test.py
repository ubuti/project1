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
    os.makedirs("/home/kit/project1/cameraimg/test/", exist_ok=True)
    test_file = f"/home/kit/project1/cameraimg/test/test.txt"
        
    with open(test_file, 'w') as f:
        f.write("USB write test")
    #os.remove(test_file)
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
    savepath = "/home/kit/project1/cameraimg/test/test.jpg"
    cv2.imwrite(savepath, frame)
    print("Image write to usb OK ")
    #os.remove(savepath)
except Exception as e:
    print(f"USB write error: {e}")
finally:
    f.close()
    cam.stop()
    cam.close()
    print("End of test")
