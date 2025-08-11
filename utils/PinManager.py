import time
import RPi.GPIO as GPIO
from typing import Optional


class Pin:
    """GPIO pin management wrapper for Raspberry Pi.

    Provides a safe interface for GPIO operations with null pin handling.
    All operations are no-ops if pin_id is None, allowing for safe testing
    and development without hardware.
    """

    def __init__(self, pin_id: Optional[int], *args, **kwargs):
        """Initialize GPIO pin with optional configuration.

        Args:
            pin_id: GPIO pin number, or None to disable all operations.
            *args: Additional arguments passed to GPIO.setup().
            **kwargs: Additional keyword arguments passed to GPIO.setup().
        """
        self.pin_id = pin_id
        if self.pin_id is not None:
            self.setup(*args, **kwargs)

    def setup(self, *args, **kwargs):
        """Configure the GPIO pin.

        Args:
            *args: Arguments passed to GPIO.setup().
            **kwargs: Keyword arguments passed to GPIO.setup().
        """
        if self.pin_id is not None:
            GPIO.setup(self.pin_id, *args, **kwargs)

    def add_event_detect(self, *args, **kwargs):
        """Add event detection to the GPIO pin.

        Args:
            *args: Arguments passed to GPIO.add_event_detect().
            **kwargs: Keyword arguments passed to GPIO.add_event_detect().
        """
        if self.pin_id is not None:
            GPIO.add_event_detect(self.pin_id, *args, **kwargs)

    def output(self, *args, **kwargs):
        """Set the output state of the GPIO pin.

        Args:
            *args: Arguments passed to GPIO.output().
            **kwargs: Keyword arguments passed to GPIO.output().
        """
        if self.pin_id is not None:
            GPIO.output(self.pin_id, *args, **kwargs)

    def lh_pulse(self):
        """Generate a low-to-high pulse on the GPIO pin."""
        if self.pin_id is not None:
            GPIO.output(self.pin_id, GPIO.LOW)
            GPIO.output(self.pin_id, GPIO.HIGH)

    def hl_pulse(self):
        """Generate a high-to-low pulse with 10ms duration on the GPIO pin."""
        if self.pin_id is not None:
            GPIO.output(self.pin_id, GPIO.HIGH)
            time.sleep(0.01)
            GPIO.output(self.pin_id, GPIO.LOW)

    def h_pulse(self):
        """Set the GPIO pin to HIGH state."""
        if self.pin_id is not None:
            GPIO.output(self.pin_id, GPIO.HIGH)

    def l_pulse(self):
        """Set the GPIO pin to LOW state."""
        if self.pin_id is not None:
            GPIO.output(self.pin_id, GPIO.LOW)

    def get_input(self) -> Optional[int]:
        """Read the current state of the GPIO pin.

        Returns:
            GPIO pin state (GPIO.HIGH or GPIO.LOW), or None if pin is disabled.
        """
        if self.pin_id is not None:
            return GPIO.input(self.pin_id)
        else:
            return None
