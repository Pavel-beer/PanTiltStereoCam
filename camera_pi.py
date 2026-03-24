#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для работы со стереокамерой (две USB-камеры)
"""

import cv2
import threading
import time
import numpy as np

class StereoCamera:
    def __init__(self, left_src=0, right_src=2, width=640, height=480):
        self.left_src = left_src
        self.right_src = right_src
        self.width = width
        self.height = height
        self.running = True
        
        self.cap_left = cv2.VideoCapture(self.left_src)
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
    
    def get_frame(self, mode='combined'):
        with self.lock:
            frame = None
            if mode == 'left':
                frame = self.frame_left
            elif mode == 'right':
                frame = self.frame_right
            else:
                frame = self.frame_combined
            
            if frame is not None:
                ret, jpeg = cv2.imencode('.jpg', frame)
                if ret:
                    return jpeg.tobytes()
        
        empty = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        ret, jpeg = cv2.imencode('.jpg', empty)
        return jpeg.tobytes()
    
    def get_left_frame(self):
        return self.get_frame('left')
    
    def get_right_frame(self):
        return self.get_frame('right')
    
    def get_combined_frame(self):
        return self.get_frame('combined')
    
    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        if self.cap_left:
            self.cap_left.release()
        if self.cap_right:
            self.cap_right.release()

Camera = StereoCamera