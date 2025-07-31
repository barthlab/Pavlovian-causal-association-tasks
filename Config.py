import os
import os.path as path


# Camera Params
CAMERA_RESOLUTION = (1080, 768)
FRAME_RATE = 30


# Raspberry Pi pin idx
AIRPUFF_SOLENOID_PIN = 32
FAKEPUFF_SOLENOID_PIN = 36
WATER_SOLENOID_PIN = 38
FAKEWATER_SOLENOID_PIN = 40
ENCODER_A_PIN = 16
ENCODER_B_PIN = 18

MICROSCOPE_TTL_PULSE = 11
VIDEO_TTL_PULSE = 12

BUZZER_PIN = 33  # make sure it's PWM pin
LICKPORT_PIN = 29


PWM_FLAG = False
print("Training is now using PWM Buzzer" if PWM_FLAG else "Training is now using non-PWM Buzzer")

HIGH_LEVEL_TRIGGER = False
print("Training is now using High Level Trigger" if HIGH_LEVEL_TRIGGER else "Training is now using Low Level Trigger")

# Data Directory
SAVE_DIR = path.join(path.dirname(__file__), "data")
TASK_DIR = path.join(path.dirname(__file__), "tasks")
os.makedirs(SAVE_DIR, exist_ok=True)


# Response Window
RESPONSE_WINDOW_CHECKING_DT = 0.2
PURETONE_HZ = 4000

# Universal Water Volume
UNIVERSAL_WATER_VOLUME = None  # seconds, turn off by setting to None

# Random Number Generator
RANDOMSEED = None  # Warning!!!!!!! turn on RANDOMSEED will make the experiment deterministic

