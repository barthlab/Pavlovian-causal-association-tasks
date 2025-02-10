import RPi.GPIO as GPIO


class Pin:
    def __init__(self, pin_id, *args, **kwargs):
        self.pin_id = pin_id
        if self.pin_id is not None:
            self.setup(*args, **kwargs)

    def setup(self, *args, **kwargs):
        if self.pin_id is not None:
            GPIO.setup(self.pin_id, *args, **kwargs)

    def add_event_detect(self, *args, **kwargs):
        if self.pin_id is not None:
            GPIO.add_event_detect(self.pin_id, *args, **kwargs)

    def output(self, *args, **kwargs):
        if self.pin_id is not None:
            GPIO.output(self.pin_id, *args, **kwargs)

    def lh_pulse(self):
        if self.pin_id is not None:
            GPIO.output(self.pin_id, GPIO.LOW)
            GPIO.output(self.pin_id, GPIO.HIGH)

    def hl_pulse(self):
        if self.pin_id is not None:
            GPIO.output(self.pin_id, GPIO.HIGH)
            GPIO.output(self.pin_id, GPIO.LOW)

    def get_input(self):
        if self.pin_id is not None:
            return GPIO.input(self.pin_id)
        else:
            return None
