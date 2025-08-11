#!/bin/env python3

"""Relay interface for Raspberry Pi GPIO control."""

import RPi.GPIO as GPIO
import Config as Config
from utils.PinManager import Pin


class Relay:
    """GPIO relay controller with configurable trigger logic.

    Supports both high-level and low-level trigger relays based on
    configuration settings. Automatically initializes to off state.
    """

    def __init__(self, relaypin: int):
        """Initialize relay with specified GPIO pin.

        Args:
            relaypin: GPIO pin number for relay control.
        """
        self.relaypin = Pin(relaypin, GPIO.OUT)
        if Config.HIGH_LEVEL_TRIGGER:
            self.relaypin.output(GPIO.LOW)
        else:
            self.relaypin.output(GPIO.HIGH)

    def on(self):
        """Activate the relay.

        Sets appropriate GPIO state based on trigger configuration.
        """
        if Config.HIGH_LEVEL_TRIGGER:
            self.relaypin.output(GPIO.HIGH)
        else:
            self.relaypin.output(GPIO.LOW)

    def off(self):
        """Deactivate the relay.

        Sets appropriate GPIO state based on trigger configuration.
        """
        if Config.HIGH_LEVEL_TRIGGER:
            self.relaypin.output(GPIO.LOW)
        else:
            self.relaypin.output(GPIO.HIGH)
        
