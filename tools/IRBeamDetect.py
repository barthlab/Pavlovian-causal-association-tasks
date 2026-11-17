"""Active-low IR beam detection for Raspberry Pi behavioral monitoring."""

import time
import RPi.GPIO as GPIO

import Config
from utils.PinManager import Pin
from utils.Utils import GetTime


class BeamBreakDetector:
    """Record beam breaks and wait for breaks or continuous beam clearance.

    HIGH indicates a clear beam; LOW indicates a broken beam.
    History stores single-item lists of monotonic timestamps in milliseconds.
    """

    def __init__(self, beampin: int):
        """Configure the input pin with a pull-up and falling-edge detection.

        Args:
            beampin: GPIO pin number connected to the beam sensor.
        """
        self.beampin = Pin(
            beampin, GPIO.IN,
            pull_up_down=GPIO.PUD_UP
        )

        self.history = []

        # Beam break: HIGH -> LOW
        self.beampin.add_event_detect(
            GPIO.FALLING,
            callback=self.register_history
        )

    def register_history(self, channel):
        """Record a beam-break timestamp in milliseconds.

        Args:
            channel: GPIO channel that triggered the callback.
        """
        self.history.append([GetTime()])
    
    def wait_for_break(self) -> float:
        """Wait for a new falling-edge event, ignoring earlier history.

        Returns:
            Approximate seconds waited, accumulated from polling intervals.
        """        
        start_history_len = len(self.history)
        current_state = self.beampin.get_input()
        if current_state == GPIO.LOW:
            return 0
        waiting_duration = 0
        last_warning_time = GetTime() / 1000

        while len(self.history) == start_history_len:
            time.sleep(Config.RESPONSE_WINDOW_CHECKING_DT)
            waiting_duration += Config.RESPONSE_WINDOW_CHECKING_DT
            
            now_time = GetTime() / 1000
            if now_time - last_warning_time >= Config.FOREVER_LOOP_WARNING_DT:
                print("\nWaiting for beam break")
                last_warning_time = now_time

        return waiting_duration

    def timeout(self, duration: float) -> float:
        """Wait until the beam stays HIGH for the requested duration.

        A new history event or sampled LOW resets the timer.
        Warn periodically while LOW.

        Args:
            duration: Required continuous HIGH time in seconds.

        Returns:
            Total seconds waited, including interruptions by LOW readings.
        """
        start_history_len = len(self.history)
        start_time = GetTime() / 1000
        last_warning_time = start_time
        high_since = None

        while True:
            now_history_len = len(self.history)
            current_state = self.beampin.get_input()
            now_time = GetTime() / 1000

            if now_history_len != start_history_len:
                high_since = None
                start_history_len = now_history_len

            if current_state == GPIO.HIGH:
                if high_since is None:
                    high_since = now_time
                if now_time - high_since >= duration and len(self.history) == start_history_len:
                    return now_time - start_time
            else:
                high_since = None
                if now_time - last_warning_time >= Config.FOREVER_LOOP_WARNING_DT:
                    print("\nWarning: Stuck in timeout loop")
                    last_warning_time = now_time

            time.sleep(Config.RESPONSE_WINDOW_CHECKING_DT)


def GetBeamDetector() -> BeamBreakDetector:
    return BeamBreakDetector(beampin=Config.BEAM_BREAK_PIN)