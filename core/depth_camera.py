import logging
from typing import Optional

import numpy as np
import open3d as o3d
from openni import openni2, _openni2
from core import csdevice as cs


class DepthCamera:
    """
    Depth camera:
    - Select best resolution depth mode (max res), lowest fps (since you don’t care about fps)
    - Force true depth format (DEPTH_100_UM), not GRAY8
    - Start stream before applying properties for reliability
    """

    def __init__(self, dev: openni2.Device, cfg: "CameraConfig", debug: bool = False):
        self.dev = dev
        self.cfg = cfg
        self.debug = debug
        self.log = logging.getLogger("capstone.depth")

        if not self.dev.has_sensor(openni2.SENSOR_DEPTH):
            raise RuntimeError("No depth sensor found")

        self.depth_stream = self.dev.create_stream(openni2.SENSOR_DEPTH)

        if self.debug:
            self.log.debug("Available depth modes:")
            for m in self.depth_stream.get_sensor_info().videoModes:
                self.log.debug("  %dx%d fps=%d fmt=%s", m.resolutionX, m.resolutionY, m.fps, m.pixelFormat)

        chosen = self._set_depth_mode_best_res_low_fps()
        self.log.info("Depth mode: %dx%d @%dfps (DEPTH_100_UM)", chosen.resolutionX, chosen.resolutionY, chosen.fps)

        # Start stream first
        self.depth_stream.start()

        # Apply properties (wrap in try so one failure doesn’t kill everything)
        try:
            self.depth_stream.set_property(
                cs.CS_PROPERTY_STREAM_EXT_DEPTH_RANGE,
                cs.DepthRange(int(self.cfg.depth_cam_MINrange), int(self.cfg.depth_cam_MAXrange))
            )
        except Exception as e:
            self.log.warning("Setting depth range failed (continuing): %s", e)

        try:
            self.depth_stream.set_property(_openni2.ONI_STREAM_PROPERTY_EXPOSURE, int(self.cfg.depth_cam_exp))
            self.depth_stream.set_property(_openni2.ONI_STREAM_PROPERTY_GAIN, int(self.cfg.depth_cam_gain))
        except Exception as e:
            self.log.warning("Setting exposure/gain failed (continuing): %s", e)

        # Intrinsics
        self.intrinsics = self.depth_stream.get_property(cs.CS_PROPERTY_STREAM_INTRINSICS, cs.Intrinsics)

        # Warmup
        for _ in range(int(self.cfg.warmup_frames)):
            self.depth_stream.read_frame()

    def _set_depth_mode_best_res_low_fps(self):
        modes = list(self.depth_stream.get_sensor_info().videoModes)

        depth_modes = [
            m for m in modes
            if m.pixelFormat == _openni2.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_100_UM
        ]
        if not depth_modes:
            raise RuntimeError("No DEPTH_100_UM modes found")

        # Highest pixel count first, then lowest fps
        depth_modes.sort(key=lambda m: (-(m.resolutionX * m.resolutionY), m.fps))
        chosen = depth_modes[0]

        self.depth_stream.set_video_mode(chosen)
        return chosen

    def capture_pcd(self, retries: int = 5) -> Optional[o3d.geometry.PointCloud]:
        for attempt in range(retries):
            frame = self.depth_stream.read_frame()
            if self.debug:
                self.log.debug("attempt %d: w=%d h=%d stride=%s",
                               attempt, frame.width, frame.height, getattr(frame, "stride", None))

            pcd = self.build_pcd_from_depth(frame, self.intrinsics)
            if pcd is not None and len(pcd.points) > 0:
                return pcd

        return None

    @staticmethod
    def build_pcd_from_depth(depth_frame, intrinsics) -> Optional[o3d.geometry.PointCloud]:
        pc_data = cs.generatePointCloud(depth_frame, intrinsics)

        if pc_data is None or not isinstance(pc_data, np.ndarray) or pc_data.size == 0:
            return None

        # Remove non-finite and (0,0,0) points
        mask = np.isfinite(pc_data).all(axis=1)
        pc_data = pc_data[mask]
        if pc_data.size == 0:
            return None

        pc_data = pc_data[np.any(pc_data != 0, axis=1)]
        if pc_data.size == 0:
            return None

        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(pc_data.astype(np.float64))
        return pcd

    def stop(self) -> None:
        if getattr(self, "depth_stream", None) is not None:
            try:
                self.depth_stream.stop()
            finally:
                self.depth_stream = None
