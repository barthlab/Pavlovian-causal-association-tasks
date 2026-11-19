"""Raspberry Pi camera recording interface."""

import io
import logging
import os
from contextlib import ExitStack
from typing import Optional

import Config as Config


logger = logging.getLogger(__name__)


class _RecordingFile(io.BufferedIOBase):
    """Keep the first write failure for the task thread to report."""

    def __init__(self, file):
        self._file = file
        self.error = None

    def write(self, frame):
        if self.error is not None:
            return 0
        try:
            written = self._file.write(frame)
            if written != len(frame):
                raise OSError(f"Short camera write ({written} of {len(frame)} bytes)")
            return written
        except (OSError, ValueError) as error:
            # FileOutput ignores the return value. Keep the encoder thread
            # running so it can release its frames and shut down normally.
            self.error = error
            return 0


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
        self._sink = None

    def __enter__(self) -> Optional["PiCameraRecorder"]:
        """Start recording and return the recorder, or None if disabled."""
        if not self.record_flag:
            return None

        from picamera2 import Picamera2
        from picamera2.encoders import H264Encoder
        from picamera2.outputs import FileOutput

        self._cleanup = ExitStack()
        self._sink = None
        try:
            camera = Picamera2()
            self._cleanup.callback(camera.close)

            resolution = tuple(Config.CAMERA_RESOLUTION)
            frame_duration = round(1_000_000 / Config.FRAME_RATE)
            config = camera.create_video_configuration(
                main={"size": resolution, "format": "YUV420"},
                controls={"FrameDurationLimits": (frame_duration, frame_duration)},
                display=None,
            )
            camera.configure(config)
            actual_size = camera.stream_configuration("main")["size"]
            if actual_size != resolution:
                raise RuntimeError(f"Camera negotiated {actual_size}, expected {resolution}")

            # Match the legacy encoder's default bitrate.
            encoder = H264Encoder(bitrate=17_000_000, framerate=Config.FRAME_RATE)
            # Send each write to the file so errors reach the sink immediately.
            video_file = open(self.filename, "wb", buffering=0)
            self._cleanup.callback(video_file.close)
            self._sink = _RecordingFile(video_file)
            output = FileOutput(self._sink)
            self._cleanup.callback(self._stop_recording, camera, encoder)
            camera.start_recording(encoder, output)
            self.wait_recording()
        except BaseException as error:
            self._finish(error)
            raise
        return self

    @staticmethod
    def _stop_recording(camera, encoder):
        try:
            camera.stop_recording()
        finally:
            # Picamera2 registers the encoder only after it starts successfully.
            if encoder.running:
                encoder.stop()

    def wait_recording(self) -> None:
        """Raise a pending output error without waiting for a frame."""
        if self._sink is not None and self._sink.error is not None:
            raise RuntimeError(
                f"Camera recording failed for {self.filename}"
            ) from self._sink.error

    def _finish(self, task_error):
        try:
            self._cleanup.close()
        except BaseException as cleanup_error:
            if task_error is None:
                task_error = cleanup_error
                raise
            logger.exception("Camera cleanup failed for %s", self.filename)
        finally:
            if self._sink is not None and self._sink.error is not None:
                if task_error is None:
                    self.wait_recording()
                elif task_error.__cause__ is not self._sink.error:
                    logger.error(
                        "Camera recording failed for %s",
                        self.filename,
                        exc_info=self._sink.error,
                    )

    def __exit__(self, exc_type, exc_value, exc_tb) -> None:
        """Release the camera and report recording failures."""
        if self.record_flag:
            self._finish(exc_value)
