#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Стереокамера с управлением поворотной платформой (Pan/Tilt)
"""

import time
from flask import Flask, render_template, Response

from camera_pi import StereoCamera
import angleServoCtrl as servo

app = Flask(__name__)

# Инициализация сервоприводов (PAN=GPIO17, TILT=GPIO27)
servo.init_servos(pan_pin=17, tilt_pin=27)

# Инициализация стереокамеры
camera = StereoCamera(left_src=0, right_src=2, width=640, height=480)

@app.route('/')
def index():
    return render_template('index.html',
                         panAngle=servo.get_pan_angle(),
                         tiltAngle=servo.get_tilt_angle())

def generate_frames(mode='combined'):
    while True:
        if mode == 'left':
            frame = camera.get_left_frame()
        elif mode == 'right':
            frame = camera.get_right_frame()
        else:
            frame = camera.get_combined_frame()
        
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.05)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames('combined'),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/left')
def video_feed_left():
    return Response(generate_frames('left'),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/right')
def video_feed_right():
    return Response(generate_frames('right'),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/pan/<int:angle>')
def pan_control(angle):
    angle = max(0, min(180, angle))
    servo.set_pan_angle(angle, smooth=True)
    return render_template('index.html',
                         panAngle=servo.get_pan_angle(),
                         tiltAngle=servo.get_tilt_angle())

@app.route('/tilt/<int:angle>')
def tilt_control(angle):
    angle = max(0, min(180, angle))
    servo.set_tilt_angle(angle, smooth=True)
    return render_template('index.html',
                         panAngle=servo.get_pan_angle(),
                         tiltAngle=servo.get_tilt_angle())

@app.route('/reset')
def reset():
    servo.set_pan_angle(90, smooth=True)
    servo.set_tilt_angle(90, smooth=True)
    return render_template('index.html', panAngle=90, tiltAngle=90)

@app.teardown_appcontext
def cleanup(exception=None):
    global camera
    if camera:
        camera.stop()
    servo.cleanup()

if __name__ == '__main__':
    print("=" * 60)
    print("🎥 СТЕРЕОКАМЕРА С УПРАВЛЕНИЕМ PAN/TILT")
    print("📹 Левая камера: /dev/video0")
    print("📹 Правая камера: /dev/video2")
    print("🎮 PAN: GPIO17, TILT: GPIO27")
    print("🌐 http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)