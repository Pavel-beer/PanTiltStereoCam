#!/usr/bin/env python3
from flask import Flask, render_template, Response
import camera_pi
import os

app = Flask(__name__)

# Глобальная переменная для камеры
camera = None

def get_camera():
    global camera
    if camera is None:
        # Используем первую USB камеру (индекс 0)
        camera = camera_pi.Camera(src=0)
    return camera

@app.route('/')
def index():
    return render_template('index.html')

def generate_frames():
    cam = get_camera()
    while True:
        frame = cam.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.teardown_appcontext
def cleanup(exception=None):
    global camera
    if camera:
        camera.stop()
        camera = None
        print("Камера остановлена")

if __name__ == '__main__':
    # Запускаем сервер, доступный из локальной сети
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
