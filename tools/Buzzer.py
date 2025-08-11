#!/bin/env python3

"""PWM tone generator for audio stimulus control."""

import RPi.GPIO as GPIO
import Config as Config
import time
from utils.PinManager import Pin


class Buzzer:
    """PWM-based buzzer controller for audio stimulus delivery.

    Supports both PWM and simple digital output modes based on configuration.
    Automatically tests the buzzer during initialization.
    """

    def __init__(self, buzzer_pin: int, frequency: int):
        """Initialize buzzer with specified pin and frequency.

        Args:
            buzzer_pin: GPIO pin number for buzzer control.
            frequency: PWM frequency in Hz for tone generation.
        """
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
        """Start buzzer tone output.

        Uses 50% duty cycle for PWM mode or sets pin LOW for digital mode.
        """
        if Config.PWM_FLAG: # PWM Buzzer
            self.buzzer.start(50)
        else:
            self.buzzer.output(GPIO.LOW)

    def stop(self):
        """Stop buzzer tone output.

        Stops PWM signal or sets pin HIGH for digital mode.
        """
        if Config.PWM_FLAG: # PWM Buzzer
            self.buzzer.stop()
        else:
            self.buzzer.output(GPIO.HIGH)


def GetBuzzer(*args) -> Buzzer:
    """Create buzzer instance with default configuration.

    Args:
        *args: Unused arguments for compatibility.

    Returns:
        Configured Buzzer instance using settings from Config.
    """
    return Buzzer(Config.BUZZER_PIN, Config.PURETONE_HZ)
