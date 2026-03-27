import cv2
import threading
import time

class Camera:
    def __init__(self, src=0, width=640, height=480):
        self.src = src
        self.width = width
        self.height = height
        # Открываем камеру (для USB камеры это обычно /dev/video0)
        self.cap = cv2.VideoCapture(self.src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        self.frame = None
        self.ret = False
        self.lock = threading.Lock()
        self.running = True
        
        # Запускаем фоновый поток для обновления кадров
        self.thread = threading.Thread(target=self.update)
        self.thread.daemon = True
        self.thread.start()
    
    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            with self.lock:
                self.ret = ret
                if ret:
                    self.frame = frame.copy()
            time.sleep(0.03)  # Небольшая пауза для снижения нагрузки
    
    def get_frame(self):
        with self.lock:
            if self.ret and self.frame is not None:
                ret, jpeg = cv2.imencode('.jpg', self.frame)
                if ret:
                    return jpeg.tobytes()
        return None
    
    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()
        if self.cap:
            self.cap.release()
