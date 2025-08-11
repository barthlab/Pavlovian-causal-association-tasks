#!/usr/bin/env python3

"""
A class to manage and read data from a DS18B20 temperature sensor
and log it to a file. This version is designed to be consistent with
other data recorders in the project, using a background thread for data
collection and an archive method for batch writing.
"""

import os
import re
import subprocess
import threading
import time
from copy import deepcopy

# Assuming these are your existing utility modules
import Config as Config
from utils.Utils import GetTime
from utils.Logger import CSVFile


class TemperatureSensor:
    """
    Manages a DS18B20 temperature sensor, collecting data in a background
    thread and saving it in batches. If the sensor is not found on
    initialization, it will print a warning and all subsequent method calls
    will be safely ignored.
    """

    # Constants for the sensor device
    _BASE_DIR = '/sys/bus/w1/devices/'
    _DEVICE_PREFIX = '28*'
    _DEVICE_FILE = 'w1_slave'
    _TEMP_REGEX = re.compile(r"t=(\d+)")

    def __init__(self, exp_name: str):
        """
        Initializes the sensor. If no sensor is found, it will print a
        warning and disable its functions.
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
            print("WARNING: DS18B20 sensor not found. Temperature will not be recorded.")
            return # Exit init, self.sensor_found remains False

        # --- Sensor was found, proceed with setup ---
        self.sensor_found = True
        self.csv_path = os.path.join(Config.SAVE_DIR, f"TEMPERATURE_{exp_name}.csv")
        self._writer = CSVFile(self.csv_path, ["time", "celsius", "fahrenheit"])

        self.history = []
        self._stop_event = threading.Event()
        self._thread = None
        self._is_running = False

        print(f"Temperature sensor initialized. Logging to {self.csv_path}")

    @staticmethod
    def _load_kernel_modules():
        """Loads the w1-gpio and w1-therm kernel modules if not already loaded."""
        try:
            # Using capture_output=True to hide success messages from modprobe
            subprocess.run(['modprobe', 'w1-gpio'], check=True, capture_output=True, text=True)
            subprocess.run(['modprobe', 'w1-therm'], check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # This is not critical if modules are loaded at boot or already present.
            pass

    def _read_temp_raw(self):
        """Reads the raw data from the sensor's device file."""
        try:
            with open(self.device_file, 'r') as f:
                return f.read()
        except IOError as e:
            print(f"WARNING: Could not read sensor file: {e}")
            return None

    def _read_temp(self, retries: int = 3, delay: float = 0.2):
        """
        Reads and parses the temperature. Returns a record for the CSV file
        or None if the read fails.
        """
        for _ in range(retries):
            content = self._read_temp_raw()
            if content and 'YES' in content:
                match = self._TEMP_REGEX.search(content)
                if match:
                    temp_string = match.group(1)
                    temp_c = float(temp_string) / 1000.0
                    temp_f = temp_c * (9.0 / 5.0) + 32.0
                    return [GetTime(), temp_c, temp_f]
            time.sleep(delay)
        
        print("WARNING: Failed to read valid temperature after multiple retries.")
        return None

    def _recorder_thread(self, interval: float):
        """Target function for the background recording thread."""
        while not self._stop_event.is_set():
            record = self._read_temp()
            if record:
                self.history.append(record)
            # wait() is better than sleep() as it can be interrupted immediately
            self._stop_event.wait(interval)

    def archive(self):
        """Writes the collected temperature history to the CSV file."""
        if not self.sensor_found or not self.history:
            return
            
        tmp_snapshot = deepcopy(self.history)
        self._writer.addrows(tmp_snapshot)
        # Efficiently clear the portion of history that was just saved
        self.history = self.history[len(tmp_snapshot):]

    def start(self, interval: float = 1):
        """Starts the background thread for temperature recording."""
        if not self.sensor_found or self._is_running:
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._recorder_thread, args=(interval,), daemon=True)
        self._thread.start()
        self._is_running = True
        print(f"Started temperature recording (interval: {interval}s).")

    def stop(self):
        """Stops the background thread and saves any remaining data."""
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
        """Context manager entry point: starts recording."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point: stops recording."""
        self.stop()


def GetSensor(exp_name: str):
    """Factory function to create a TemperatureSensor instance."""
    return TemperatureSensor(exp_name=exp_name)