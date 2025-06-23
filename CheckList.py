import RPi.GPIO as GPIO
import Config as Config
import argparse
import time
from utils.PinManager import Pin
from flask import Flask, Response
import io
import picamera
import socket
from tools.LickDetector import GetDetector
from tools.PositionRecorder import GetEncoder
from tools.Buzzer import GetBuzzer


args = argparse.ArgumentParser()
args.add_argument("-puff", "--puff", action="store_true", help="check puff")
args.add_argument("-water", "--water", action="store_true", help="check water delivery")
args.add_argument("-camera", "--camera", action="store_true", help="check camera")
args.add_argument("-lick", "--lick", action="store_true", help="check lick sensor")
args.add_argument(
    "-wheel", "--wheel", action="store_true", help="check rotatory encoder"
)
args.add_argument("-buzzer", "--buzzer", action="store_true", help="check buzzer")
cfg = args.parse_args()
print(cfg)


def check_puff():
    start_time = time.time()
    print(start_time)

    GPIO.setmode(GPIO.BOARD)
    check_pins = [
        Pin(Config.AIRPUFF_SOLENOID_PIN, GPIO.OUT),
        Pin(Config.FAKE1_SOLENOID_PIN, GPIO.OUT),
        Pin(Config.FAKE2_SOLENOID_PIN, GPIO.OUT),
        # Pin(BUZZER_PIN, GPIO.OUT),
    ]
    for tmp_pin in check_pins:
        tmp_pin.output(GPIO.HIGH)

    # main loop
    while time.time() - start_time < 600:
        time.sleep(10)

        for i in check_pins:
            print(f"Check Pin {i.pin_id}")
            i.output(GPIO.LOW)
            time.sleep(2)
            i.output(GPIO.HIGH)
            time.sleep(5)
    GPIO.cleanup()


def check_water():
    GPIO.setmode(GPIO.BOARD)
    WATER_DURATION = 0.05
    water_pin = Pin(Config.WATER_SOLENOID_PIN, GPIO.OUT)
    water_pin.output(GPIO.HIGH)

    drain_mode = input(
        "Enter anything to enable always-open mode, otherwise feed mode: "
    )
    if drain_mode:
        print("Always Open")
        water_pin.output(GPIO.LOW)
        _ = input("Press Enter to exit: ")
        water_pin.output(GPIO.HIGH)
    else:
        water_duration = input(
            f"Enter water duration, otherwise adopt default setup ({WATER_DURATION}s): "
        )
        water_duration = float(water_duration) if water_duration else WATER_DURATION
        print(f"Adopted water time: {water_duration}s")
        while True:
            user_input = input(
                "Press Enter to drain the water (or type in anything stop the loop):"
            )
            if not user_input:
                water_pin.output(GPIO.LOW)
                time.sleep(water_duration)
                water_pin.output(GPIO.HIGH)
            else:
                break
    GPIO.cleanup()


def check_camera():
    app = Flask(__name__)

    # Function to capture frames from the camera
    def gen_frames():
        with picamera.PiCamera(
            resolution=Config.CAMERA_RESOLUTION, framerate=Config.FRAME_RATE
        ) as camera:
            stream = io.BytesIO()
            for _ in camera.capture_continuous(
                stream, format="jpeg", use_video_port=True
            ):
                stream.seek(0)
                frame = stream.read()

                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

                stream.seek(0)
                stream.truncate()

    # Flask route to stream video
    @app.route("/video_feed")
    def video_feed():
        return Response(
            gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    # Get the Raspberry Pi's IP address
    def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't need to connect, just to get the local IP address
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"  # fallback to localhost
        finally:
            s.close()
        return ip

    ip_address = get_ip()
    port = 8000
    print("#" * 70)
    print(f"###Camera stream available at: http://{ip_address}:{port}/video_feed")
    print("#" * 70)
    app.run(host="0.0.0.0", port=port, debug=True)


def check_lick():
    GPIO.setmode(GPIO.BOARD)
    exp_name = input("Experiment ID: ")
    lick_detector = GetDetector(exp_name)
    start_time = time.time()
    while time.time() - start_time < 600:
        time.sleep(5)
    lick_detector.archive()
    GPIO.cleanup()


def check_wheel():
    GPIO.setmode(GPIO.BOARD)
    exp_name = input("Experiment ID: ")
    locomotion_encoder = GetEncoder(exp_name)
    start_time = time.time()
    while time.time() - start_time < 600:
        time.sleep(2)
        print(
            "Value is {}".format(locomotion_encoder.getValue()),
            f"time is {time.time() - start_time}",
        )
    locomotion_encoder.archive()
    GPIO.cleanup()


def check_buzzer():
    GPIO.setmode(GPIO.BOARD)
    buzzer_ = GetBuzzer()
    for i in range(10):
        buzzer_.on()
        time.sleep(1)
        buzzer_.stop()
        time.sleep(1)
    GPIO.cleanup()


if __name__ == "__main__":
    if cfg.puff:
        print("Checking Puff...")
        check_puff()
    elif cfg.water:
        print("Checking Water Delivery...")
        check_water()
    elif cfg.camera:
        print("Checking Camera...")
        check_camera()
    elif cfg.lick:
        print("Checking Lick Sensor...")
        check_lick()
    elif cfg.wheel:
        print("Checking Rotatory Encoder...")
        check_wheel()
    elif cfg.buzzer:
        print("Checking Buzzer...")
        check_buzzer()
