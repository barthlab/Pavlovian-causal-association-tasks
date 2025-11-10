#!/bin/env python3

"""PWM tone generator for audio stimulus control."""

import RPi.GPIO as GPIO
import Config as Config
import time
from typing import cast
from gpiozero import PWMOutputDevice
from utils.PinManager import Pin


class Buzzer:
    """PWM-based buzzer controller for audio stimulus delivery.

    Supports both PWM and simple digital output modes based on configuration.
    Automatically tests the buzzer during initialization.
    """

    def __init__(self, buzzer_pin: int, frequency: int):
        """Initialize buzzer with specified pin and frequency.

        Args:
            buzzer_pin: Board pin number for buzzer control.
            frequency: PWM frequency in Hz for tone generation.
        """
        if Config.PWM_FLAG: # PWM Buzzer
            print("Initializing PWM Buzzer, make sure you are in the right pigpiod sample rate...")
            self.buzzer = PWMOutputDevice(f"BOARD{buzzer_pin}", frequency=frequency)
            self.buzzer.value = 1
        else:
            self.buzzer = Pin(buzzer_pin, GPIO.OUT)
            self.buzzer.output(GPIO.HIGH)

        # Test the PWM buzzer
        if Config.PWM_FLAG: # PWM Buzzer
            self.on()
            time.sleep(0.1)
            self.stop()

    def on(self):
        """Start buzzer tone output.

        Uses 50% duty cycle for PWM mode or sets pin LOW for digital mode.
        """
        if Config.PWM_FLAG: # PWM Buzzer
            self.buzzer.value = 0.5
        else:
            self.buzzer.output(GPIO.LOW)

    def stop(self):
        """Stop buzzer tone output.

        Stops PWM signal or sets pin HIGH for digital mode.
        """
        if Config.PWM_FLAG: # PWM Buzzer
            self.buzzer.value = 1
        else:
            self.buzzer.output(GPIO.HIGH)

    def tune(self, frequency: int):
        """Change buzzer frequency.

        Args:
            frequency: New PWM frequency in Hz.
        """
        if Config.PWM_FLAG: # PWM Buzzer
            assert frequency in (4000, 5000, 8000, 10000), f"Frequency {frequency} not supported."
            self.buzzer.frequency = frequency

def GetBuzzer(*args) -> Buzzer:
    """Create buzzer instance with default configuration.

    Args:
        *args: Unused arguments for compatibility.

    Returns:
        Configured Buzzer instance using settings from Config.
    """
    return Buzzer(Config.BUZZER_PIN, Config.PURETONE_HZ)
