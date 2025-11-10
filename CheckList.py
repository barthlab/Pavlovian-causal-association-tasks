"""Hardware testing utility for Pavlovian causal association tasks.

Provides individual testing functions for all hardware components including
solenoids, sensors, camera, and other peripherals. Each component can be
tested independently using command-line arguments.
"""

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
args.add_argument("-temperature", "--temperature", action="store_true", help="check temperature sensor")
args.add_argument("-peltier", "--peltier", action="store_true", help="check peltier")
cfg = args.parse_args()
print(cfg)


def check_puff():
    """Test air puff and water delivery solenoids.

    Cycles through all solenoid valves for 10 minutes, activating each
    for 2 seconds with 5-second intervals between activations.
    """
    start_time = time.time()
    print(f"Starting puff check at: {start_time}")

    GPIO.setmode(GPIO.BOARD)
    check_pins = [
        Relay(Config.AIRPUFF_SOLENOID_PIN),
        Relay(Config.FAKEPUFF_SOLENOID_PIN),
        Relay(Config.WATER_SOLENOID_PIN),
        Relay(Config.FAKERELAY_SOLENOID_PIN),
        Relay(Config.BLUE_LED_PIN),
        Relay(Config.LIME_LED_PIN),
    ]
    pin_names = ["AirPuff", "FakePuff", "Water", "FakeRelay", "BlueLED", "LimeLED"]

    # Main testing loop
    while time.time() - start_time < 600:
        time.sleep(10)

        for i, name in zip(check_pins, pin_names):
            print(f"Testing pin {name} at GPIO pin {i.relaypin.pin_id}.")
            i.on()
            time.sleep(2)
            i.off()
            time.sleep(5)
    GPIO.cleanup()


def check_water():
    """Test water delivery solenoid with configurable duration.

    Provides two modes: always-open for draining, or timed pulses for
    testing water delivery timing and volume.
    """
    GPIO.setmode(GPIO.BOARD)
    WATER_DURATION = 0.05
    water_pin = Relay(Config.WATER_SOLENOID_PIN)

    drain_mode = input(
        "Enter anything to enable always-open mode, otherwise feed mode: "
    )
    if drain_mode:
        print("Always open mode enabled.")
        water_pin.on()
        _ = input("Press Enter to exit: ")
        water_pin.off()
    else:
        water_duration = input(
            f"Enter water duration, otherwise adopt default setup ({WATER_DURATION}s): "
        )
        water_duration = float(water_duration) if water_duration else WATER_DURATION
        print(f"Adopted water time: {water_duration}s.")
        while True:
            user_input = input(
                "Press Enter to deliver water (or type anything to stop): "
            )
            if not user_input:
                water_pin.on()
                time.sleep(water_duration)
                water_pin.off()
            else:
                break
    GPIO.cleanup()


def check_peltier():
    """Test peltier cooling system.
    """
    GPIO.setmode(GPIO.BOARD)
    check_pins = [
        Relay(Config.PELTIER_LEFT_PIN),
        Relay(Config.PELTIER_RIGHT_PIN),
    ]
    pin_names = ["PeltierLeft", "PeltierRight"]
    
    PELTIER_DURATION = 0.5
    on_duration = input(f"Enter on duration (in seconds), otherwise adopt default setup ({PELTIER_DURATION}s): ")
    on_duration = float(on_duration) if on_duration else PELTIER_DURATION

    print(f"Adopted on duration: {on_duration}s.")
    while True:
        user_input = input(
            "Press Enter to test peltier (or type anything to stop): "
        )
        if user_input:
            break
        for i, name in zip(check_pins, pin_names):
            print(f"Testing pin {name} at GPIO pin {i.relaypin.pin_id}.")
            i.on()
            time.sleep(on_duration)
            i.off()
            print(f"Testing pin {name} at GPIO pin {i.relaypin.pin_id} complete. Waiting 5s before next test...")
            time.sleep(5)
    GPIO.cleanup()


def check_camera():
    """Test camera functionality with live video stream.

    Creates a Flask web server to stream live video from the Pi camera.
    Access the stream through the displayed URL to verify camera operation.
    """
    app = Flask(__name__)

    def gen_frames():
        """Generate video frames from Pi camera for streaming."""
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

    @app.route("/video_feed")
    def video_feed():
        """Flask route to serve video stream."""
        return Response(
            gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    def get_ip():
        """Get the Raspberry Pi's IP address for stream access.

        Returns:
            IP address string, or localhost if detection fails.
        """
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
    print(f"Camera stream available at: http://{ip_address}:{port}/video_feed")
    print("#" * 70)
    app.run(host="0.0.0.0", port=port, debug=True)


def check_lick():
    """Test lick sensor detection and data logging.

    Monitors lick sensor for 10 minutes, displaying detected licks
    and saving data to CSV file.
    """
    GPIO.setmode(GPIO.BOARD)
    exp_name = input("Experiment ID: ")
    lick_detector = GetDetector(exp_name)
    start_time = time.time()
    print("Monitoring lick sensor for 10 minutes. Licks will be displayed as ':P'.")
    while time.time() - start_time < 600:
        time.sleep(5)
    lick_detector.archive()
    GPIO.cleanup()


def check_wheel():
    """Test rotary encoder position tracking.

    Monitors encoder position for 10 minutes, displaying current
    position value and elapsed time every 2 seconds.
    """
    GPIO.setmode(GPIO.BOARD)
    exp_name = input("Experiment ID: ")
    locomotion_encoder = GetEncoder(exp_name)
    start_time = time.time()
    print("Monitoring rotary encoder for 10 minutes.")
    while time.time() - start_time < 600:
        time.sleep(2)
        print(
            f"Position value: {locomotion_encoder.getValue()}, "
            f"elapsed time: {time.time() - start_time:.1f}s"
        )
    locomotion_encoder.archive()
    GPIO.cleanup()


def check_buzzer():
    """Test buzzer audio output.

    Activates buzzer 10 times with 1-second on/off cycles
    to verify audio stimulus functionality.
    """
    GPIO.setmode(GPIO.BOARD)
    buzzer_ = GetBuzzer()
    print("Remember to enable pigpiod sample rate at 1us")
    for _ in range(10):
        for freq2play in (4000, 5000, 8000, 10000):
            print(f"Testing buzzer cycle at {freq2play}Hz.")
            buzzer_.tune(freq2play)
            buzzer_.on()
            time.sleep(2)
            buzzer_.stop()
            time.sleep(1)
    GPIO.cleanup()


def check_temperature():
    """Test temperature sensor data collection and logging.

    Initializes temperature sensor and displays live readings until
    interrupted. Saves all data to CSV file automatically.
    """
    exp_name = input("Experiment ID (for logging): ")
    sensor = TemperatureSensor(exp_name)

    if not sensor.sensor_found:
        print("Cannot proceed as sensor was not initialized.")
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
                        print(f"Live reading at {tmp_t:.2f}s: {celsius:.2f}°C / {fahrenheit:.2f}°F")
                    last_history_len += len(new_readings)

        except KeyboardInterrupt:
            print("\nStopping temperature check.")

    print("Temperature check complete. Log file has been saved.")


if __name__ == "__main__":
    if cfg.puff:
        print("Checking puff delivery...")
        check_puff()
    elif cfg.water:
        print("Checking water delivery...")
        check_water()
    elif cfg.camera:
        print("Checking camera...")
        check_camera()
    elif cfg.lick:
        print("Checking lick sensor...")
        check_lick()
    elif cfg.wheel:
        print("Checking rotary encoder...")
        check_wheel()
    elif cfg.buzzer:
        print("Checking buzzer...")
        check_buzzer()
    elif cfg.temperature:
        print("Checking temperature sensor...")
        check_temperature()
    elif cfg.peltier:
        print("Checking peltier...")
        check_peltier()