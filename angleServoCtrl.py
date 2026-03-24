#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Управление сервоприводами MG90S через GPIO
"""

import sys
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

class ServoController:
    def __init__(self, pin, initial_angle=90):
        self.pin = pin
        self.angle = initial_angle
        
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 50)
        self.pwm.start(0)
        self.set_angle(initial_angle)
    
    def _angle_to_duty(self, angle):
        angle = max(0, min(180, angle))
        return 2.5 + (angle / 180.0) * 10.0
    
    def set_angle(self, angle, smooth=True, step_delay=0.01):
        angle = max(0, min(180, angle))
        
        if smooth and self.angle != angle:
            step = 1 if angle > self.angle else -1
            for a in range(int(self.angle), int(angle), step):
                self.pwm.ChangeDutyCycle(self._angle_to_duty(a))
                time.sleep(step_delay)
        
        self.pwm.ChangeDutyCycle(self._angle_to_duty(angle))
        time.sleep(0.1)
        self.pwm.ChangeDutyCycle(0)
        self.angle = angle
        return angle
    
    def get_angle(self):
        return self.angle
    
    def stop(self):
        if self.pwm:
            self.pwm.stop()
        GPIO.cleanup(self.pin)

pan_servo = None
tilt_servo = None

def init_servos(pan_pin=17, tilt_pin=27):
    global pan_servo, tilt_servo
    pan_servo = ServoController(pan_pin, 90)
    tilt_servo = ServoController(tilt_pin, 90)
    return pan_servo, tilt_servo

def set_pan_angle(angle, smooth=True):
    global pan_servo
    if pan_servo:
        return pan_servo.set_angle(angle, smooth)
    return None

def set_tilt_angle(angle, smooth=True):
    global tilt_servo
    if tilt_servo:
        return tilt_servo.set_angle(angle, smooth)
    return None

def get_pan_angle():
    global pan_servo
    return pan_servo.get_angle() if pan_servo else 90

def get_tilt_angle():
    global tilt_servo
    return tilt_servo.get_angle() if tilt_servo else 90

def cleanup():
    global pan_servo, tilt_servo
    if pan_servo:
        pan_servo.stop()
    if tilt_servo:
        tilt_servo.stop()
    GPIO.cleanup()