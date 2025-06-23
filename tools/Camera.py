import picamera
import os
import Config as Config


class PiCameraRecorder:
    def __init__(self, exp_name, records=True):
        self.filename = os.path.join(Config.SAVE_DIR, f"VIDEO_{exp_name}.h264")
        self.record_flag = records

    def __enter__(self):
        self._camera = None
        if self.record_flag:
            self._camera = picamera.PiCamera()
            self._camera.resolution = Config.CAMERA_RESOLUTION
            self._camera.framerate = Config.FRAME_RATE
            self._camera.start_recording(self.filename)
        return self._camera

    def __exit__(self, exc_type, exc_value, exc_tb):
        if self._camera is not None:
            self._camera.stop_recording()
            self._camera.close()
        return None
