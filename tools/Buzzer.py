#!/bin/env python3

"""
Encoder test script for raspberry pi
"""

import time
import RPi.GPIO as GPIO
import os
import sys
import os.path as path
from Config import *
from utils.PinManager import Pin
from copy import copy, deepcopy


class Buzzer:
    def __init__(self, buzzer_pin: int, frequency: int):
        GPIO.setup(buzzer_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(buzzer_pin, frequency)

    def on(self):
        # Start PWM: pwm.start(duty_cycle)
        # 50% duty cycle is a good choice for a simple square wave tone.
        self.pwm.start(50)

    def stop(self):
        self.pwm.stop()


def GetBuzzer(*args):
    return Buzzer(BUZZER_PIN, PURETONE_HZ)

