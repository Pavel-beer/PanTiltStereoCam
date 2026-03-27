#!/usr/bin/env python3
"""
Простой веб-сервер для потоковой передачи видео с USB-камеры
"""

import cv2
from flask import Flask, Response, render_template_string
import time
import threading

app = Flask(__name__)

# HTML шаблон с правильным отображением видео
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>USB Camera Stream</title>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=/video_only">
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
        <img src="{{ url_for('video_feed') }}?t={{ timestamp }}" width="800" style="transform: scaleX(-1);">
    </div>
    <div class="info">
        <p>🌐 Доступ: <span class="ip">{{ ip_address }}</span>:5000</p>
        <button onclick="location.reload()">🔄 Обновить</button>
    </div>
    <script>
        // Принудительное обновление изображения
        var img = document.querySelector('img');
        setInterval(function() {
            img.src = "{{ url_for('video_feed') }}?t=" + new Date().getTime();
        }, 50);
    </script>
</body>
</html>
'''

# Глобальные переменные
frame = None
lock = threading.Lock()
running = True
camera = None
fps = 30

def init_camera():
    """Инициализация камеры"""
    global camera
    
    print("📷 Подключение к камере...")
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("❌ Ошибка: не удалось открыть камеру")
        return False
    
    # Установка разрешения
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)
    
    # Проверка
    w = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = camera.get(cv2.CAP_PROP_FPS)
    print(f"✅ Камера готова: {w}x{h}, FPS: {actual_fps}")
    
    return True

def capture_thread():
    """Поток для непрерывного захвата кадров"""
    global frame, running, camera
    
    while running:
        if camera and camera.isOpened():
            ret, img = camera.read()
            if ret:
                with lock:
                    # Можно добавить горизонтальное отражение для зеркального отображения
                    # img = cv2.flip(img, 1)
                    frame = img.copy()
            else:
                print("⚠️ Ошибка захвата кадра")
        time.sleep(0.01)  # Высокая частота захвата

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
    """Главная страница"""
    import time
    return render_template_string(HTML_TEMPLATE, 
                                 ip_address=get_ip(),
                                 timestamp=int(time.time()))

@app.route('/video_only')
def video_only():
    """Страница только с видео"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Stream</title>
        <style>
            body { margin: 0; background: black; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
            img { max-width: 100%; max-height: 100vh; }
        </style>
    </head>
    <body>
        <img src="/video_feed" style="transform: scaleX(-1);">
    </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    """Видеопоток MJPEG"""
    def generate():
        global frame
        last_frame = None
        while True:
            current_frame = None
            with lock:
                if frame is not None:
                    current_frame = frame.copy()
            
            if current_frame is not None:
                # Проверяем, изменился ли кадр
                if last_frame is None or not (current_frame == last_frame).all():
                    ret, jpeg = cv2.imencode('.jpg', current_frame, 
                                           [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if ret:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'Cache-Control: no-cache, no-store, must-revalidate\r\n'
                               b'Pragma: no-cache\r\n'
                               b'Expires: 0\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                        last_frame = current_frame.copy()
            
            # Задержка для контроля FPS
            time.sleep(1.0 / fps)
    
    return Response(generate(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame',
                   headers={
                       'Cache-Control': 'no-cache, no-store, must-revalidate',
                       'Pragma': 'no-cache',
                       'Expires': '0'
                   })

@app.route('/status')
def status():
    """Проверка статуса"""
    with lock:
        has_frame = frame is not None
    return {'camera_working': has_frame, 'fps': fps}

@app.teardown_appcontext
def cleanup(exception=None):
    """Очистка при завершении"""
    global running, camera
    running = False
    if camera:
        camera.release()
    print("📷 Камера освобождена")

if __name__ == '__main__':
    print("=" * 60)
    print("🎥 USB Camera Web Server - LIVE STREAM")
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
    print("🌐 http://{ip}:5000/video_only - полноэкранный режим")
    print("=" * 60)
    print("Нажмите CTRL+C для остановки")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
