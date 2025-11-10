"""Configuration settings for Pavlovian causal association tasks.

This module contains all hardware pin assignments, camera settings, timing
parameters, and other configuration constants used throughout the system.
"""

import os
import os.path as path


# Camera Parameters
CAMERA_RESOLUTION = (1080, 768)
FRAME_RATE = 30


# Raspberry Pi GPIO Pin Assignments
AIRPUFF_SOLENOID_PIN = 32
FAKEPUFF_SOLENOID_PIN = 36
PELTIER_LEFT_PIN = None
PELTIER_RIGHT_PIN = None
WATER_SOLENOID_PIN = 38
FAKERELAY_SOLENOID_PIN = 40
ENCODER_A_PIN = 16
ENCODER_B_PIN = 18

MICROSCOPE_TTL_PULSE = 11
VIDEO_TTL_PULSE = 12

BUZZER_PIN = 33  # make sure it's PWM pin
LICKPORT_PIN = 29

BLUE_LED_PIN = None
LIME_LED_PIN = None


# Hardware Configuration Flags
PWM_FLAG = False
print("Attention: Training is now using ", "PWM buzzer." if PWM_FLAG else "non-PWM buzzer.")

HIGH_LEVEL_TRIGGER = False
print("Attention: Training is now using ", "high level trigger." if HIGH_LEVEL_TRIGGER else "low level trigger.")

# Data Directory Configuration
SAVE_DIR = path.join(path.dirname(__file__), "data")
TASK_DIR = path.join(path.dirname(__file__), "tasks")
os.makedirs(SAVE_DIR, exist_ok=True)


# Timing Parameters
RESPONSE_WINDOW_CHECKING_DT = 0.2
PURETONE_HZ = 6000
LICKING_MAXIMUM_FREQUENCY = 20  # Hz

# Water Delivery Configuration
UNIVERSAL_WATER_VOLUME = 0.04  # seconds, turn off by setting to None

# Random Number Generator Configuration
RANDOMSEED = None  # Warning: setting RANDOMSEED will make experiments deterministic

