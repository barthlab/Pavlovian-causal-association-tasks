#!/bin/env python3

"""
PWM tone generator
"""

import RPi.GPIO as GPIO
import Config as Config
import time
from utils.PinManager import Pin


class Buzzer:
    def __init__(self, buzzer_pin: int, frequency: int):
        GPIO.setup(buzzer_pin, GPIO.OUT)
        if buzzer_pin != 33:
            self.buzzer = Pin(buzzer_pin, GPIO.OUT)
            self.buzzer.output(GPIO.LOW)
            self.pwm_flag = False
        else:
            self.buzzer = GPIO.PWM(buzzer_pin, frequency)
            self.pwm_flag = True
        self.on()
        time.sleep(0.1)
        self.stop()

    def on(self):
        # Start PWM: pwm.start(duty_cycle)
        # 50% duty cycle is a good choice for a simple square wave tone.
        if self.pwm_flag:
            self.buzzer.start(50)
        else:
            self.buzzer.output(GPIO.HIGH)

    def stop(self):
        if self.pwm_flag:
            self.buzzer.stop()
        else:
            self.buzzer.output(GPIO.LOW)


def GetBuzzer(*args):
    return Buzzer(Config.BUZZER_PIN, Config.PURETONE_HZ)
