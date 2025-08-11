#!/bin/env python3

"""Rotary encoder interface for Raspberry Pi locomotion tracking."""

import RPi.GPIO as GPIO
import os.path as path
import Config as Config
from utils.Utils import GetTime
from utils.PinManager import Pin
from utils.Logger import CSVFile
from copy import deepcopy
from typing import List, Optional, Callable


class PositionEncoder:
    """Quadrature rotary encoder interface for tracking animal locomotion.

    Monitors two GPIO pins to detect rotation direction and count position
    changes. Uses state machine logic to handle quadrature encoding.
    """

    def __init__(self, leftPin: int, rightPin: int, exp_name: str, callback: Optional[Callable] = None):
        """Initialize position encoder with specified pins and experiment name.

        Args:
            leftPin: GPIO pin number for encoder channel A.
            rightPin: GPIO pin number for encoder channel B.
            exp_name: Experiment name for data file naming.
            callback: Optional callback function for position changes.
        """
        self.leftPin = Pin(leftPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.rightPin = Pin(rightPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.value = 0
        self.state = '00'
        self.direction = None

        self.callback = callback if callback is not None else self.register_history
        self.history: List[List] = [[GetTime(), 0, None],]

        self.writer = CSVFile(path.join(Config.SAVE_DIR, f"LOCOMOTION_{exp_name}.csv"), ["time", "position", "direction"])

        self.leftPin.add_event_detect(GPIO.BOTH, callback=self.transition_occurred)
        self.rightPin.add_event_detect(GPIO.BOTH, callback=self.transition_occurred)

    def register_history(self, value: int, direction: Optional[str]):
        """Record position change in history buffer.

        Args:
            value: Current position value.
            direction: Direction of movement ("L" or "R").
        """
        self.history.append([GetTime(), value, direction])

    def transition_occurred(self, channel: int):
        """Handle encoder state transition events.

        Implements quadrature decoding state machine to track rotation
        direction and count position changes.

        Args:
            channel: GPIO channel that triggered the event.
        """
        p1 = self.leftPin.get_input()
        p2 = self.rightPin.get_input()
        newState = "{}{}".format(p1, p2)

        if self.state == "00":  # Resting position
            if newState == "01":  # Turned right 1
                self.direction = "R"
            elif newState == "10":  # Turned left 1
                self.direction = "L"

        elif self.state == "01":  # R1 or L3 position
            if newState == "11":  # Turned right 1
                self.direction = "R"
            elif newState == "00":  # Turned left 1
                if self.direction == "L":
                    self.value = self.value - 1
                    if self.callback is not None:
                        self.callback(self.value, self.direction)

        elif self.state == "10":  # R3 or L1
            if newState == "11":  # Turned left 1
                self.direction = "L"
            elif newState == "00":  # Turned right 1
                if self.direction == "R":
                    self.value = self.value + 1
                    if self.callback is not None:
                        self.callback(self.value, self.direction)

        else:  # self.state == "11"
            if newState == "01":  # Turned left 1
                self.direction = "L"
            elif newState == "10":  # Turned right 1
                self.direction = "R"
            elif newState == "00":  # Skipped an intermediate 01 or 10 state, but if we know direction then a turn is complete
                if self.direction == "L":
                    self.value = self.value - 1
                    if self.callback is not None:
                        self.callback(self.value, self.direction)
                elif self.direction == "R":
                    self.value = self.value + 1
                    if self.callback is not None:
                        self.callback(self.value, self.direction)

        self.state = newState

    def getValue(self) -> int:
        """Get current position value.

        Returns:
            Current encoder position count.
        """
        return self.value

    def archive(self):
        """Write accumulated position data to CSV file and clear history buffer."""
        tmp_snapshot = deepcopy(self.history)
        self.writer.addrows(tmp_snapshot)
        self.history = self.history[len(tmp_snapshot):]


def GetEncoder(exp_name: str) -> PositionEncoder:
    """Create position encoder instance with default configuration.

    Args:
        exp_name: Experiment name for data file naming.

    Returns:
        Configured PositionEncoder instance using settings from Config.
    """
    return PositionEncoder(Config.ENCODER_A_PIN, Config.ENCODER_B_PIN, exp_name=exp_name)

