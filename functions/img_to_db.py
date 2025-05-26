import psycopg2
import cv2
import numpy as np


def store_img2(img):
    pass

def store_img(img):
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(dbname="camimages_db", user="pi_user", password="password", host="localhost")
        cur = conn.cursor()

        # Convert OpenCV image (numpy array) to binary
        _, buffer = cv2.imencode(".jpg", img)  # Encode as JPEG
        binary_image = buffer.tobytes()  # Convert to bytes

        # Insert into PostgreSQL
        cur.execute("INSERT INTO images (image_data) VALUES (%s);", (binary_image,))
        conn.commit()

        print("Image stored in database successfully.")

    except Exception as e:
        print(f"Error storing image: {e}")

    finally:
        # Close connection
        cur.close()
        conn.close()
