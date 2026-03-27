#!/usr/bin/env python3
"""
Простой веб-сервер для передачи видео с USB-камеры
"""

import cv2
from flask import Flask, Response, render_template_string
import time
import threading

app = Flask(__name__)

# HTML шаблон
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>USB Camera Stream</title>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            background: #1a1a2e;
            color: #eee;
            margin: 0;
            padding: 20px;
        }
        h1 { color: #00adb5; }
        .video-container {
            margin: 20px auto;
            background: #0f3460;
            padding: 20px;
            border-radius: 15px;
            display: inline-block;
        }
        img {
            border: 3px solid #00adb5;
            border-radius: 8px;
            max-width: 100%;
        }
        .info { margin-top: 20px; color: #888; }
        .ip { background: #0f3460; padding: 5px 10px; border-radius: 5px; font-family: monospace; }
        button {
            background: #00adb5;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover { background: #008b93; }
    </style>
</head>
<body>
    <h1>📹 USB Camera Stream</h1>
    <div class="video-container">
        <img src="{{ url_for('video_feed') }}" width="800">
    </div>
    <div class="info">
        <p>🌐 Доступ: <span class="ip">{{ ip_address }}</span>:5000</p>
        <button onclick="location.reload()">🔄 Обновить</button>
    </div>
</body>
</html>
'''

# Глобальные переменные
frame = None
lock = threading.Lock()
running = True
camera = None

def init_camera():
    """Инициализация камеры в отдельном потоке"""
    global camera, frame, running
    
    print("📷 Подключение к камере...")
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("❌ Ошибка: не удалось открыть камеру")
        return False
    
    # Установка разрешения
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Проверка
    w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"✅ Камера готова: {w}x{h}")
    
    return True

def capture_thread():
    """Поток для непрерывного захвата кадров"""
    global frame, running, camera
    
    while running:
        if camera and camera.isOpened():
            ret, img = camera.read()
            if ret:
                with lock:
                    frame = img.copy()
        time.sleep(0.03)  # ~30 fps

def get_ip():
    """Получение IP-адреса"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "192.168.1.53"

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, ip_address=get_ip())

@app.route('/video_feed')
def video_feed():
    def generate():
        global frame
        while True:
            with lock:
                if frame is not None:
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.teardown_appcontext
def cleanup(exception=None):
    global running, camera
    running = False
    if camera:
        camera.release()
    print("📷 Камера освобождена")

if __name__ == '__main__':
    print("=" * 60)
    print("🎥 USB Camera Web Server")
    print("=" * 60)
    
    # Инициализация камеры
    if init_camera():
        # Запуск потока захвата
        thread = threading.Thread(target=capture_thread)
        thread.daemon = True
        thread.start()
        print("✅ Поток захвата запущен")
    else:
        print("⚠️ Камера не работает, проверьте подключение")
    
    ip = get_ip()
    print(f"🌐 http://localhost:5000")
    print(f"🌐 http://{ip}:5000")
    print("=" * 60)
    print("Нажмите CTRL+C для остановки")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
