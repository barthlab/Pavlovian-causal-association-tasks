#!/usr/bin/env python3

"""DS18B20 temperature sensor interface for environmental monitoring.

Manages temperature data collection using background threading and provides
batch writing capabilities. Designed to be consistent with other data
recorders in the project.
"""

import os
import re
import subprocess
import threading
import time
from copy import deepcopy
from typing import List, Optional

import Config as Config
from utils.Utils import GetTime
from utils.Logger import CSVFile


class TemperatureSensor:
    """DS18B20 temperature sensor manager with background data collection.

    Collects temperature data in a background thread and saves it in batches.
    If the sensor is not found on initialization, it will print a warning
    and all subsequent method calls will be safely ignored.
    """

    # Constants for the sensor device
    _BASE_DIR = '/sys/bus/w1/devices/'
    _DEVICE_PREFIX = '28*'
    _DEVICE_FILE = 'w1_slave'
    _TEMP_REGEX = re.compile(r"t=(\d+)")

    def __init__(self, exp_name: str):
        """Initialize temperature sensor with experiment name.

        If no sensor is found, prints a warning and disables all functions.

        Args:
            exp_name: Experiment name for data file naming.
        """
        self.sensor_found = False
        self._load_kernel_modules()

        try:
            # Use glob to find the device folder, which is more robust
            import glob
            device_folders = glob.glob(os.path.join(self._BASE_DIR, self._DEVICE_PREFIX))
            if not device_folders:
                raise FileNotFoundError
            # Use the first sensor found
            self.device_file = os.path.join(device_folders[0], self._DEVICE_FILE)
        except (StopIteration, FileNotFoundError):
            print("Warning: DS18B20 sensor not found. Temperature will not be recorded.")
            return # Exit init, self.sensor_found remains False

        # --- Sensor was found, proceed with setup ---
        self.sensor_found = True
        self.csv_path = os.path.join(Config.SAVE_DIR, f"TEMPERATURE_{exp_name}.csv")
        self._writer = CSVFile(self.csv_path, ["time", "celsius", "fahrenheit"])

        self.history: List[List] = []
        self._stop_event = threading.Event()
        self._thread = None
        self._is_running = False

        print(f"Temperature sensor initialized. Logging to {self.csv_path}.")

    @staticmethod
    def _load_kernel_modules():
        """Load w1-gpio and w1-therm kernel modules if not already loaded."""
        try:
            # Using capture_output=True to hide success messages from modprobe
            subprocess.run(['modprobe', 'w1-gpio'], check=True, capture_output=True, text=True)
            subprocess.run(['modprobe', 'w1-therm'], check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # This is not critical if modules are loaded at boot or already present.
            pass

    def _read_temp_raw(self) -> Optional[str]:
        """Read raw data from the sensor's device file.

        Returns:
            Raw sensor data string, or None if read fails.
        """
        try:
            with open(self.device_file, 'r') as f:
                return f.read()
        except IOError as e:
            print(f"Warning: could not read sensor file: {e}.")
            return None

    def _read_temp(self) -> Optional[List]:
        """Read and parse temperature from sensor.

        Returns:
            List containing [timestamp, celsius, fahrenheit] or None if read fails.
        """
        content = self._read_temp_raw()
        if content and 'YES' in content:
            match = self._TEMP_REGEX.search(content)
            if match:
                temp_string = match.group(1)
                temp_c = float(temp_string) / 1000.0
                temp_f = temp_c * (9.0 / 5.0) + 32.0
                return [GetTime(), temp_c, temp_f]

        print("Warning: failed to read valid temperature.")
        return None

    def _recorder_thread(self):
        """Target function for the background recording thread."""
        while not self._stop_event.is_set():
            record = self._read_temp()
            if record:
                self.history.append(record)

    def archive(self):
        """Write collected temperature history to CSV file and clear buffer."""
        if not self.sensor_found or not self.history:
            return

        tmp_snapshot = deepcopy(self.history)
        self._writer.addrows(tmp_snapshot)
        # Efficiently clear the portion of history that was just saved
        self.history = self.history[len(tmp_snapshot):]

    def start(self):
        """Start background thread for temperature recording."""
        if not self.sensor_found or self._is_running:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._recorder_thread, daemon=True)
        self._thread.start()
        self._is_running = True
        print("Started temperature recording.")

    def stop(self):
        """Stop background thread and save any remaining data."""
        if not self.sensor_found or not self._is_running:
            return

        print("Stopping temperature recording thread...")
        self._stop_event.set()
        if self._thread:
            self._thread.join()

        self._is_running = False
        # Perform one final archive to save any data collected before stopping
        self.archive()
        print("Temperature recording stopped.")

    def __enter__(self):
        """Context manager entry point: start recording.

        Returns:
            Self for use in with statement.
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point: stop recording.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        self.stop()


def GetSensor(exp_name: str) -> TemperatureSensor:
    """Create temperature sensor instance with default configuration.

    Args:
        exp_name: Experiment name for data file naming.

    Returns:
        Configured TemperatureSensor instance.
    """
    return TemperatureSensor(exp_name=exp_name)