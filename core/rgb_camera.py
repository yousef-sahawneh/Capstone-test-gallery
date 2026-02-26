import logging
import numpy as np
from openni import openni2, _openni2
from core import csdevice as cs


class RGBCamera:
    """
    RGB camera based on your working approach:
    - Select RGB888 video mode
    - Use get_buffer_as_triplet() to decode RGB safely
    """

    def __init__(self, dev: openni2.Device, cfg: "CameraConfig", debug: bool = False):
        self.dev = dev
        self.cfg = cfg
        self.debug = debug
        self.log = logging.getLogger("capstone.rgb")

        if not self.dev.has_sensor(openni2.SENSOR_COLOR):
            raise RuntimeError("No color sensor found")

        self.color_stream = self.dev.create_stream(openni2.SENSOR_COLOR)

        if self.debug:
            self.log.debug("Available color modes:")
            for m in self.color_stream.get_sensor_info().videoModes:
                self.log.debug("  %dx%d fps=%d fmt=%s", m.resolutionX, m.resolutionY, m.fps, m.pixelFormat)

        chosen = self._set_rgb888_mode_prefer_low_fps()
        self.log.info("RGB mode: %dx%d @%dfps (RGB888)", chosen.resolutionX, chosen.resolutionY, chosen.fps)

        # Start stream first (more robust on some devices)
        self.color_stream.start()

        # Set LED control (optional; don’t break capture if it fails)
        try:
            self.color_stream.set_property(cs.CS_PROPERTY_STREAM_LED_CTRL, int(self.cfg.strobe_status))
            if self.debug:
                self.log.debug("LED_CTRL set to %s", self.cfg.strobe_status)
        except Exception as e:
            self.log.warning("LED_CTRL set_property failed (continuing): %s", e)

        # Warmup
        for _ in range(int(self.cfg.warmup_frames)):
            self.color_stream.read_frame()

    def _set_rgb888_mode_prefer_low_fps(self):
        modes = [
            m for m in self.color_stream.get_sensor_info().videoModes
            if m.pixelFormat == _openni2.OniPixelFormat.ONI_PIXEL_FORMAT_RGB888
        ]
        if not modes:
            raise RuntimeError("RGB888 video mode not found for color stream")

        # Prefer lowest fps (more reliable / less bandwidth)
        modes.sort(key=lambda m: m.fps)
        chosen = modes[0]
        self.color_stream.set_video_mode(chosen)
        return chosen

    def capture_rgb(self, retries: int = 5) -> np.ndarray:
        last_err = None
        for _ in range(retries):
            try:
                frame = self.color_stream.read_frame()

                if self.debug:
                    self.log.debug("frame w=%d h=%d stride=%s",
                                   frame.width, frame.height, getattr(frame, "stride", None))

                rgb = np.array(frame.get_buffer_as_triplet(), dtype=np.uint8).reshape(
                    frame.height, frame.width, 3
                )
                return rgb
            except Exception as e:
                last_err = e

        raise RuntimeError(f"Failed to capture RGB frame after {retries} tries. Last error: {last_err}")

    def stop(self) -> None:
        if getattr(self, "color_stream", None) is not None:
            try:
                self.color_stream.stop()
            finally:
                self.color_stream = None
