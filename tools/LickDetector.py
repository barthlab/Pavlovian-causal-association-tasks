#!/bin/env python3

"""Lick sensor interface for Raspberry Pi behavioral monitoring."""

import time
import RPi.GPIO as GPIO
import os.path as path
import Config as Config
from utils.Utils import GetTime
from utils.PinManager import Pin
from utils.Logger import CSVFile
from copy import deepcopy
from typing import List


class LickDetector:
    """Lick sensor interface for detecting animal licking behavior.

    Monitors GPIO pin for lick events and logs timestamps to CSV file.
    Uses interrupt-based detection for precise timing.
    """

    def __init__(self, lickpin: int, exp_name: str):
        """Initialize lick detector with specified pin and experiment name.

        Args:
            lickpin: GPIO pin number connected to lick sensor.
            exp_name: Experiment name for data file naming.
        """
        self.lickpin = Pin(lickpin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.history: List[List[float]] = [[GetTime(),],]

        self.writer = CSVFile(path.join(Config.SAVE_DIR, f"LICK_{exp_name}.csv"), ["time", ])

        self.lickpin.add_event_detect(GPIO.BOTH, callback=self.register_history)

    def register_history(self, channel: int):
        """Callback function for lick event detection. 
        High state should persist for at least 1/Config.LICKING_MAXIMUM_FREQUENCY seconds.

        Args:
            channel: GPIO channel that triggered the event.
        """
        current_state = GPIO.input(channel)
        if current_state == GPIO.LOW:
            return
        time.sleep(1/Config.LICKING_MAXIMUM_FREQUENCY)
        current_state = GPIO.input(channel)
        if current_state == GPIO.LOW:
            print(":P", end='', flush=True)
            self.history.append([GetTime(),])

    def archive(self):
        """Write accumulated lick data to CSV file and clear history buffer."""
        tmp_snapshot = deepcopy(self.history)
        self.writer.addrows(tmp_snapshot)
        self.history = self.history[len(tmp_snapshot):]


def GetDetector(exp_name: str) -> LickDetector:
    """Create lick detector instance with default configuration.

    Args:
        exp_name: Experiment name for data file naming.

    Returns:
        Configured LickDetector instance using settings from Config.
    """
    return LickDetector(Config.LICKPORT_PIN, exp_name=exp_name)

