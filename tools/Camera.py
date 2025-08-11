"""Raspberry Pi camera recording interface."""

import picamera
import os
import Config as Config
from typing import Optional


class PiCameraRecorder:
    """Context manager for Raspberry Pi camera video recording.

    Handles video recording with configurable resolution and frame rate.
    Can be disabled for testing without affecting experiment flow.
    """

    def __init__(self, exp_name: str, records: bool = True):
        """Initialize camera recorder.

        Args:
            exp_name: Experiment name for video file naming.
            records: Whether to actually record video (False for testing).
        """
        self.filename = os.path.join(Config.SAVE_DIR, f"VIDEO_{exp_name}.h264")
        self.record_flag = records

    def __enter__(self) -> Optional[picamera.PiCamera]:
        """Start camera recording if enabled.

        Returns:
            PiCamera instance if recording is enabled, None otherwise.
        """
        self._camera = None
        if self.record_flag:
            self._camera = picamera.PiCamera()
            self._camera.resolution = Config.CAMERA_RESOLUTION
            self._camera.framerate = Config.FRAME_RATE
            self._camera.start_recording(self.filename)
        return self._camera

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        """Stop camera recording and cleanup resources.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_value: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        if self._camera is not None:
            self._camera.stop_recording()
            self._camera.close()
