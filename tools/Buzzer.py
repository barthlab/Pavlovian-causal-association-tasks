#!/bin/env python3

"""
PWM tone generator
"""

import RPi.GPIO as GPIO
import Config as Config


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
    return Buzzer(Config.BUZZER_PIN, Config.PURETONE_HZ)
