#!/bin/env python3

"""Relay interface for Raspberry Pi GPIO control."""

from typing import Optional
import RPi.GPIO as GPIO
import Config as Config
from utils.PinManager import Pin


class Relay:
    """GPIO relay controller with configurable trigger logic.

    Supports both high-level and low-level trigger relays based on
    configuration settings. Automatically initializes to off state.
    """

    def __init__(self, relaypin: Optional[int], mode=Config.HIGH_LEVEL_TRIGGER):
        """Initialize relay with specified GPIO pin.

        Args:
            relaypin: GPIO pin number for relay control.
        """
        self.relaypin = Pin(relaypin, GPIO.OUT)
        print(f"Initializing relay on pin {relaypin} with mode {'HIGH' if mode else 'LOW'}")
        self.mode = mode
        if self.mode:
            self.relaypin.output(GPIO.LOW)
        else:
            self.relaypin.output(GPIO.HIGH)

    def on(self):
        """Activate the relay.

        Sets appropriate GPIO state based on trigger configuration.
        """
        if self.mode:
            self.relaypin.output(GPIO.HIGH)
        else:
            self.relaypin.output(GPIO.LOW)

    def off(self):
        """Deactivate the relay.

        Sets appropriate GPIO state based on trigger configuration.
        """
        if self.mode:
            self.relaypin.output(GPIO.LOW)
        else:
            self.relaypin.output(GPIO.HIGH)
        
