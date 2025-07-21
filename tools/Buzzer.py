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
        if Config.PWM_FLAG: # PWM Buzzer
            self.buzzer = GPIO.PWM(buzzer_pin, frequency)
        else:
            self.buzzer = Pin(buzzer_pin, GPIO.OUT)
            self.buzzer.output(GPIO.HIGH)

        # Test the PWM buzzer
        if Config.PWM_FLAG: # PWM Buzzer
            self.on()
            time.sleep(0.1)
            self.stop()

    def on(self):
        # Start PWM: pwm.start(duty_cycle)
        # 50% duty cycle is a good choice for a simple square wave tone.
        if Config.PWM_FLAG: # PWM Buzzer
            self.buzzer.start(50)
        else:
            self.buzzer.output(GPIO.LOW)

    def stop(self):
        if Config.PWM_FLAG: # PWM Buzzer
            self.buzzer.stop()
        else:
            self.buzzer.output(GPIO.HIGH)


def GetBuzzer(*args):
    return Buzzer(Config.BUZZER_PIN, Config.PURETONE_HZ)
