#!/bin/env python3

"""
Relay interface for raspberry pi
"""

import RPi.GPIO as GPIO
import Config as Config
from utils.PinManager import Pin

class Relay:
    def __init__(self, relaypin):
        self.relaypin = Pin(relaypin, GPIO.OUT)
        if Config.HIGH_LEVEL_TRIGGER:
            self.relaypin.output(GPIO.LOW)
        else:
            self.relaypin.output(GPIO.HIGH)
    
    def on(self):
        if Config.HIGH_LEVEL_TRIGGER:
            self.relaypin.output(GPIO.HIGH)
        else:
            self.relaypin.output(GPIO.LOW)
    
    def off(self):
        if Config.HIGH_LEVEL_TRIGGER:
            self.relaypin.output(GPIO.LOW)
        else:
            self.relaypin.output(GPIO.HIGH)
        
