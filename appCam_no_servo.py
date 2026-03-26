#!/usr/bin/env python3
from flask import Flask, render_template, Response
import cv2
import threading
import time
import numpy as np

app = Flask(__name__)

class StereoCamera:
    def __init__(self, left_src=0, right_src=2, width=640, height=480):
        self.left_src = left_src
        self.right_src = right_src
        self.width = width
        self.height = height
        self.running = True
        
        print(f"📷 Открываю левую камеру (src={left_src})...")
        self.cap_left = cv2.VideoCapture(self.left_src)
        print(f"📷 Открываю правую камеру (src={right_src})...")
        self.cap_right = cv2.VideoCapture(self.right_src)
        
        self.cap_left.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap_left.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap_right.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap_right.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        self.frame_left = None
        self.frame_right = None
        self.frame_combined = None
        self.lock = threading.Lock()
        
        self.thread = threading.Thread(target=self._update_frames)
        self.thread.daemon = True
        self.thread.start()
    
    def _update_frames(self):
        while self.running:
            ret_left, frame_left = self.cap_left.read()
            ret_right, frame_right = self.cap_right.read()
            
            with self.lock:
                if ret_left:
                    self.frame_left = frame_left.copy()
                if ret_right:
                    self.frame_right = frame_right.copy()
                
                if self.frame_left is not None and self.frame_right is not None:
                    h1, w1 = self.frame_left.shape[:2]
                    h2, w2 = self.frame_right.shape[:2]
                    if h1 != h2:
                        min_h = min(h1, h2)
                        self.frame_left = self.frame_left[:min_h, :]
                        self.frame_right = self.frame_right[:min_h, :]
                    self.frame_combined = cv2.hconcat([self.frame_left, self.frame_right])
            
            time.sleep(0.03)
    
    def get_left_frame(self):
        with self.lock:
            if self.frame_left is not None:
                ret, jpeg = cv2.imencode('.jpg', self.frame_left)
                if ret:
                    return jpeg.tobytes()
        return None
    
    def get_right_frame(self):
        with self.lock:
            if self.frame_right is not None:
                ret, jpeg = cv2.imencode('.jpg', self.frame_right)
                if ret:
                    return jpeg.tobytes()
        return None
    
    def get_combined_frame(self):
        with self.lock:
            if self.frame_combined is not None:
                ret, jpeg = cv2.imencode('.jpg', self.frame_combined)
                if ret:
                    return jpeg.tobytes()
        return None
    
    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap_left:
            self.cap_left.release()
        if self.cap_right:
            self.cap_right.release()

# Инициализация стереокамеры
# Сначала пробуем левая=0, правая=2
camera = StereoCamera(left_src=0, right_src=2, width=640, height=480)

@app.route('/')
def index():
    return render_template('index_simple.html')

@app.route('/video_feed/left')
def video_feed_left():
    def generate():
        while True:
            frame = camera.get_left_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/right')
def video_feed_right():
    def generate():
        while True:
            frame = camera.get_right_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed/combined')
def video_feed_combined():
    def generate():
        while True:
            frame = camera.get_combined_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.teardown_appcontext
def cleanup(exception=None):
    global camera
    if camera:
        camera.stop()

if __name__ == '__main__':
    print("=" * 60)
    print("🎥 СТЕРЕОКАМЕРА (без сервоприводов)")
    print("📹 Левая камера: /dev/video0")
    print("📹 Правая камера: /dev/video2")
    print("🌐 Откройте в браузере: http://localhost:5000")
    print("🌐 С другого компьютера: http://192.168.1.53:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)