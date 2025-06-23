#!/bin/env python3

"""
Lick sensor interface for raspberry pi
"""

import RPi.GPIO as GPIO
import os.path as path
import Config as Config
from utils.Utils import GetTime
from utils.PinManager import Pin
from utils.Logger import CSVFile
from copy import deepcopy


class LickDetector:
    def __init__(self, lickpin, exp_name):
        self.lickpin = Pin(lickpin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.history = [[GetTime(),],]

        self.writer = CSVFile(path.join(Config.SAVE_DIR, f"LICK_{exp_name}.csv"), ["time", ])

        self.lickpin.add_event_detect(GPIO.FALLING, callback=self.register_history)

    def register_history(self, channel):
        cur_char = len(self.history) % 10
        if cur_char ==0:
            print(":P", end='', flush=True)
        # else:
        #     sys.stdout.write("\b")
        #     print(cur_char, end='', flush=True)

        self.history.append([GetTime(),])

    def archive(self):
        tmp_snapshot = deepcopy(self.history)
        self.writer.addrows(tmp_snapshot)
        self.history = self.history[len(tmp_snapshot):]


def GetDetector(exp_name):
    return LickDetector(Config.LICKPORT_PIN, exp_name=exp_name)

