from dataclasses import dataclass

@dataclass
class CameraConfig:
    # RBG Camera
    strobe_status: int = 0

    # Depth Camera
    depth_cam_exp: int = 16000
    depth_cam_gain: int = 1
    depth_cam_resolution: int = 960
    depth_cam_MINrange: int = 200
    depth_cam_MAXrange: int = 500

    # Both Cameras
    warmup_frames: int = 2

    # Save Outputs
    save_png: bool = False
    save_pcd: bool = False