#!/bin/env python3
import RPi.GPIO as GPIO
import Config as Config
from RealTimeTaskManager import GetModules
import argparse
from utils.PinManager import Pin
from tools.Camera import PiCameraRecorder
from tools.LickDetector import GetDetector
from tools.PositionRecorder import GetEncoder
from tools.Buzzer import GetBuzzer


args = argparse.ArgumentParser()
args.add_argument("-M", "-Module", "-m", "--M", "--m", type=str, help='Choose the module from Modules.')
args.add_argument("-cam", "--cam", action='store_true', help="enable camera recording (require more disk space)")
cfg = args.parse_args()
print(cfg)


print(f"Data saved at: {Config.SAVE_DIR}")
video_recording = cfg.cam
if video_recording:
    print("-"*8, "camera recording... pay attention to disk space", "-"*8)


def main():
    """Set up all the pins and set their initial values"""
    GPIO.setmode(GPIO.BOARD)

    water_pin = Pin(Config.WATER_SOLENOID_PIN, GPIO.OUT)
    airpuff_pin = Pin(Config.AIRPUFF_SOLENOID_PIN, GPIO.OUT)
    fakepuff_pin = Pin(Config.FAKEPUFF_SOLENOID_PIN, GPIO.OUT)
    fakewater_pin = Pin(Config.FAKEWATER_SOLENOID_PIN, GPIO.OUT)

    microscope_pin = Pin(Config.MICROSCOPE_TTL_PULSE, GPIO.OUT)
    video_pin = Pin(Config.VIDEO_TTL_PULSE, GPIO.OUT)

    water_pin.output(GPIO.HIGH)
    airpuff_pin.output(GPIO.HIGH)
    fakepuff_pin.output(GPIO.HIGH)
    fakewater_pin.output(GPIO.HIGH)

    microscope_pin.output(GPIO.LOW)
    video_pin.output(GPIO.LOW)

    # main loop
    exp_name = input("Experiment ID: ")

    lick_detector = GetDetector(exp_name=exp_name)
    locomotion_encoder = GetEncoder(exp_name=exp_name)
    buzzer_ = GetBuzzer()
    module = GetModules(module_name=cfg.M, exp_name=exp_name, lick_detector=lick_detector)

    with PiCameraRecorder(exp_name =exp_name, records= video_recording) as camera:
        for _, command in enumerate(module.run()):
            if command== 'ShortPulse':
                video_pin.hl_pulse()
            elif command == 'CheckCamera':
                if camera is not None:
                    camera.wait_recording()
            elif command == 'VerticalPuffOn':
                airpuff_pin.output(GPIO.LOW)
                microscope_pin.hl_pulse()
            elif command == "VerticalPuffOff":
                airpuff_pin.output(GPIO.HIGH)
            elif command == 'BlankOn':
                fakepuff_pin.output(GPIO.LOW)
                microscope_pin.hl_pulse()
            elif command == "BlankOff":
                fakepuff_pin.output(GPIO.HIGH)
            elif command == 'HorizontalPuffOn':
                fakepuff_pin.output(GPIO.LOW)
                microscope_pin.hl_pulse()
            elif command == "HorizontalPuffOff":
                fakepuff_pin.output(GPIO.HIGH)

            elif command == "BuzzerOn":
                buzzer_.on()
            elif command == "BuzzerOff":
                buzzer_.stop()

            elif command == 'WaterOn':
                water_pin.output(GPIO.LOW)
            elif command == 'WaterOff':
                water_pin.output(GPIO.HIGH)
            elif command == 'NoWaterOn':
                fakewater_pin.output(GPIO.LOW)
            elif command == 'NoWaterOff':
                fakewater_pin.output(GPIO.HIGH)

            elif command == 'RegisterBehavior':
                locomotion_encoder.archive()
                lick_detector.archive()
                module.archive()
            else:
                print(command)
                raise NotImplementedError

    # cleanup
    GPIO.cleanup()


if "__main__" == __name__:
    main()
