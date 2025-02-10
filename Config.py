import os
import os.path as path


# Camera Params
CAMERA_RESOLUTION = (1080, 768)
FRAME_RATE = 30


# Raspberry Pi pin idx
AIRPUFF_SOLENOID_PIN = 35
WATER_SOLENOID_PIN = 29
FAKE1_SOLENOID_PIN = 33
FAKE2_SOLENOID_PIN = None
ENCODER_A_PIN = 38
ENCODER_B_PIN = 36

MICROSCOPE_TTL_PULSE = None
VIDEO_TTL_PULSE = None

BUZZER_PIN = 31
LICKPORT_PIN = 37


# Data Directory
SAVE_DIR = path.join(path.dirname(__file__), "data")
TASK_DIR = path.join(path.dirname(__file__), "tasks")
os.makedirs(SAVE_DIR, exist_ok=True)

