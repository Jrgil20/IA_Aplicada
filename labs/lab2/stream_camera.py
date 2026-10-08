#!/usr/bin/env python3
"""
Local Webcam HTTP MJPEG Streamer for DGX Spark.
Serves the webcam video feed at http://<LOCAL_IP>:8080/video
matching what app.py on the Spark expects.
"""

import argparse
import sys
from flask import Flask, Response, render_template_string

try:
    import cv2
except ImportError:
    sys.exit("Error: opencv-python is not installed yet.")

app = Flask(__name__)
camera = None


def get_camera(camera_idx: int = 0):
    global camera
    if camera is None or not camera.isOpened():
        camera = cv2.VideoCapture(camera_idx)
    return camera


def generate_frames(camera_idx: int = 0):
    cap = get_camera(camera_idx)
    while True:
        success, frame = cap.read()
        if not success:
            continue
        # Encode as JPEG
        ret, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


@app.route("/video")
def video_feed():
    camera_idx = app.config.get("CAMERA_INDEX", 0)
    return Response(
        generate_frames(camera_idx),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/")
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head><title>Webcam MJPEG Streamer</title></head>
    <body style="font-family:sans-serif; text-align:center; padding:20px; background:#111; color:#eee;">
        <h2>Webcam Local Stream Activo (DGX Spark)</h2>
        <p>Endpoint consumido por app.py en la Spark: <code>/video</code></p>
        <img src="/video" width="640" style="border:2px solid #555; border-radius:8px;" />
    </body>
    </html>
    """)


def main():
    parser = argparse.ArgumentParser(
        description="Local Webcam MJPEG Streamer for DGX Spark"
    )
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface (default: 0.0.0.0)")
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default: 0)")
    args = parser.parse_args()

    app.config["CAMERA_INDEX"] = args.camera
    print(f"\n[Webcam Streamer]: Iniciando servicio en http://{args.host}:{args.port}/video")
    print("Presiona Ctrl+C para detener.\n")
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
