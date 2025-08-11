import RPi.GPIO as GPIO
import Config as Config
import argparse
import time
from flask import Flask, Response
import io
import picamera
import socket
from tools.LickDetector import GetDetector
from tools.PositionRecorder import GetEncoder
from tools.Buzzer import GetBuzzer
from tools.Relay import Relay
from tools.TemperatureSensor import TemperatureSensor


args = argparse.ArgumentParser()
args.add_argument("-puff", "--puff", action="store_true", help="check puff")
args.add_argument("-water", "--water", action="store_true", help="check water delivery")
args.add_argument("-camera", "--camera", action="store_true", help="check camera")
args.add_argument("-lick", "--lick", action="store_true", help="check lick sensor")
args.add_argument(
    "-wheel", "--wheel", action="store_true", help="check rotatory encoder"
)
args.add_argument("-buzzer", "--buzzer", action="store_true", help="check buzzer")
args.add_argument("-temp", "--temp", action="store_true", help="check temperature sensor")
cfg = args.parse_args()
print(cfg)


def check_puff():
    start_time = time.time()
    print(start_time)

    GPIO.setmode(GPIO.BOARD)
    check_pins = [
        Relay(Config.AIRPUFF_SOLENOID_PIN),
        Relay(Config.FAKEPUFF_SOLENOID_PIN),
        Relay(Config.WATER_SOLENOID_PIN),
        Relay(Config.FAKEWATER_SOLENOID_PIN),
    ]
    pin_names = ["AirPuff", "FakePuff", "Water", "FakeWater"]

    # main loop
    while time.time() - start_time < 600:
        time.sleep(10)

        for i, name in zip(check_pins, pin_names):
            print(f"Check Pin {name} at pin {i.relaypin.pin_id}")
            i.on()
            time.sleep(2)
            i.off()
            time.sleep(5)
    GPIO.cleanup()


def check_water():
    GPIO.setmode(GPIO.BOARD)
    WATER_DURATION = 0.05
    water_pin = Relay(Config.WATER_SOLENOID_PIN)

    drain_mode = input(
        "Enter anything to enable always-open mode, otherwise feed mode: "
    )
    if drain_mode:
        print("Always Open")
        water_pin.on()
        _ = input("Press Enter to exit: ")
        water_pin.off()
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
                water_pin.on()
                time.sleep(water_duration)
                water_pin.off()
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

def check_temperature():
    """Initializes the temp sensor and prints live readings from its history."""
    exp_name = input("Experiment ID (for logging): ")
    sensor = TemperatureSensor(exp_name)

    if not sensor.sensor_found:
        print("Checklist cannot proceed as sensor was not initialized.")
        return
    
    print("Starting temperature sensor check. Press Ctrl+C to stop.")
    
    last_history_len = 0
    # The 'with' statement handles starting and stopping the sensor's background thread
    with sensor:
        try:
            while True:
                # If the history list has grown, print the new readings
                if len(sensor.history) > last_history_len:
                    new_readings = sensor.history[last_history_len:]
                    for reading in new_readings:
                        # Reading format is [timestamp, celsius, fahrenheit]
                        tmp_t, celsius, fahrenheit = reading
                        print(f"Live Reading at {tmp_t:.2f}s: {celsius:.2f}°C / {fahrenheit:.2f}°F")
                    last_history_len += len(new_readings)
                time.sleep(1) # Wait a second before checking for new readings
        except KeyboardInterrupt:
            print("\nStopping temperature check.")
    
    print("Temperature check complete. Log file has been saved.")
    # The sensor's __exit__ method handles the final archive call automatically.



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
    elif cfg.temp:
        print("Checking Temperature Sensor...")
        check_temperature()