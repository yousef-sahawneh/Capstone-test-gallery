import numpy as np

class CompareConfig:
    num_col_x: int = 500
    num_row_y: int = 500
    base_plate_x: float = 300.0  # mm
    base_plate_y: float = 300.0  # mm

    cam_trans_x: float = 160.0
    cam_trans_y: float = -50.0
    cam_trans_z: float = 515.0
    
    cam_rot_x: float = np.pi
    cam_rot_y: float = 0.0
    cam_rot_z: float = np.pi