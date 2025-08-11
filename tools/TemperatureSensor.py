#!/usr/bin/env python3

"""
A class to manage and read data from a DS18B20 temperature sensor
and log it to a file using a background thread.
If no sensor is found, it will print a warning and disable its functions.
"""

import logging
import queue
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Tuple, Union

# Assuming these are your existing utility modules
import Config as Config
from utils.Utils import GetTime
from utils.Logger import CSVFile

# Set up a logger for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TemperatureSensor:
    """
    Manages a DS18B20 temperature sensor. If the sensor is not found on
    initialization, it will print a warning and all subsequent method calls
    will be safely ignored.
    """

    # Constants for the sensor device
    _BASE_DIR = Path('/sys/bus/w1/devices/')
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
            device_folder = next(self._BASE_DIR.glob(self._DEVICE_PREFIX))
            self.device_file = device_folder / self._DEVICE_FILE
        except (StopIteration, FileNotFoundError):
            logging.warning("DS18B20 sensor not found. Temperature will not be recorded.")
            return # Exit init, self.sensor_found remains False

        # --- Sensor was found, proceed with setup ---
        self.sensor_found = True
        self.csv_path = Path(Config.SAVE_DIR) / f"TEMPERATURE_{exp_name}.csv"
        self._writer = CSVFile(str(self.csv_path), ["time", "celsius", "fahrenheit"])

        self._data_queue = queue.Queue()
        self._stop_event = threading.Event()
        self._producer_thread: Optional[threading.Thread] = None
        self._consumer_thread: Optional[threading.Thread] = None
        self._is_running = False

        logging.info(f"Temperature sensor initialized. Logging to {self.csv_path}")

    @staticmethod
    def _load_kernel_modules():
        """Loads the w1-gpio and w1-therm kernel modules."""
        try:
            subprocess.run(['modprobe', 'w1-gpio'], check=True, capture_output=True, text=True)
            subprocess.run(['modprobe', 'w1-therm'], check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # This is not a critical error if the modules are already loaded
            logging.debug("Could not run modprobe. Modules may already be loaded.")

    def _read_temp_raw(self) -> Optional[str]:
        """Reads the raw data from the sensor's device file."""
        try:
            return self.device_file.read_text()
        except IOError as e:
            logging.warning(f"Could not read sensor file: {e}")
            return None

    def read_temp(self, retries: int = 3, delay: float = 0.2) -> Union[Tuple[float, float], Tuple[None, None]]:
        """
        Reads and parses the temperature. Returns None if the sensor was not
        found or if the read fails.
        """
        if not self.sensor_found:
            return None, None

        for _ in range(retries):
            content = self._read_temp_raw()
            if content and 'YES' in content:
                match = self._TEMP_REGEX.search(content)
                if match:
                    temp_string = match.group(1)
                    temp_c = float(temp_string) / 1000.0
                    temp_f = temp_c * (9.0 / 5.0) + 32.0
                    return temp_c, temp_f
            time.sleep(delay)
        
        logging.warning("Failed to read valid temperature after multiple retries.")
        return None, None

    def _producer(self, interval: float):
        """Target function for the recording thread."""
        while not self._stop_event.is_set():
            temps = self.read_temp()
            if temps[0] is not None:
                record = [GetTime(), *temps]
                self._data_queue.put(record)
            self._stop_event.wait(interval)

    def _consumer(self):
        """Target function for the writing thread."""
        while not (self._stop_event.is_set() and self._data_queue.empty()):
            try:
                record = self._data_queue.get(timeout=1)
                self._writer.addrow(record)
                self._data_queue.task_done()
            except queue.Empty:
                continue

    def start(self, interval: float = 1.0):
        """Starts background threads if the sensor was found."""
        if not self.sensor_found or self._is_running:
            return

        self._stop_event.clear()
        
        self._consumer_thread = threading.Thread(target=self._consumer, daemon=True)
        self._consumer_thread.start()

        self._producer_thread = threading.Thread(target=self._producer, args=(interval,), daemon=True)
        self._producer_thread.start()

        self._is_running = True
        logging.info(f"Started temperature recording (interval: {interval}s).")

    def stop(self):
        """Stops background threads if they are running."""
        if not self.sensor_found or not self._is_running:
            return

        logging.info("Stopping temperature recording threads...")
        self._stop_event.set()

        if self._producer_thread:
            self._producer_thread.join()
        
        self._data_queue.join()
        if self._consumer_thread:
            self._consumer_thread.join()
        
        self._is_running = False
        logging.info("Temperature recording stopped.")

    def __enter__(self):
        """Context manager entry point: starts recording."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point: stops recording."""
        self.stop()

def GetSensor(exp_name: str) -> TemperatureSensor:
    """Factory function to create a TemperatureSensor instance."""
    return TemperatureSensor(exp_name=exp_name)