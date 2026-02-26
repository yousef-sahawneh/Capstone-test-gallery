import numpy as np
import cv2
import matplotlib.pyplot as plt

from core.projector_config import ProjectorConfig
from core.cloud_compare_config import CompareConfig


class Projector:
    """Projects the offset color map onto the physical wood surface."""

    # Rotation matrix: projector faces straight down (optical axis = world -Z)
    R = np.array([
        [ 1,  0,  0],
        [ 0, -1,  0],
        [ 0,  0, -1],
    ], dtype=np.float64)

    def __init__(self, config: ProjectorConfig = None):
        self.cfg = config or ProjectorConfig()
        self._cmap = plt.get_cmap("RdYlGn_r")

    def build_image(
        self,
        offsets: np.ndarray,
        cad_heights: np.ndarray,
    ) -> np.ndarray:
        """
        Build an (800, 1280, 3) BGR projection image from the offset matrix.

        Parameters
        ----------
        offsets : (500, 500) float array — offset values in mm (NaN = no data)
        cad_heights : (500, 500) float array — CAD surface Z in mm

        Returns
        -------
        image : (800, 1280, 3) uint8 BGR array
        """
        cfg = self.cfg
        grid_n_x = offsets.shape[0]                    # num_col_x
        grid_n_y = offsets.shape[1]                    # num_row_y
        base_mm_x = CompareConfig.base_plate_x        # mm
        base_mm_y = CompareConfig.base_plate_y        # mm

        # --- Build world-space XYZ for every grid cell ---
        i_idx = np.arange(grid_n_x)
        j_idx = np.arange(grid_n_y)
        ii, jj = np.meshgrid(i_idx, j_idx, indexing="ij")  # (num_col_x, num_row_y)

        x_w = ii * (base_mm_x / grid_n_x)     # 0 → base_plate_x mm
        y_w = -jj * (base_mm_y / grid_n_y)    # 0 → -base_plate_y mm
        z_w = cad_heights                  # CAD surface height

        # --- Translate into projector-relative frame ---
        dx = x_w - cfg.world_pos_x
        dy = y_w - cfg.world_pos_y
        dz = z_w - cfg.world_pos_z

        # Stack to (500, 500, 3) then apply R
        P_rel = np.stack([dx, dy, dz], axis=-1)            # (500, 500, 3)
        P_proj = P_rel @ self.R.T                           # (500, 500, 3)

        px = P_proj[..., 0]
        py = P_proj[..., 1]
        pz = P_proj[..., 2]

        # --- Project to pixel coordinates ---
        with np.errstate(divide="ignore", invalid="ignore"):
            u = cfg.fx * px / pz + cfg.cx   # (500, 500)
            v = cfg.fy * py / pz + cfg.cy   # (500, 500)

        u_px = np.round(u).astype(int)
        v_px = np.round(v).astype(int)

        # --- Build output image (black background) ---
        image = np.zeros((cfg.height, cfg.width, 3), dtype=np.uint8)

        # Valid mask: inside image bounds, not NaN, point in front of projector (pz > 0)
        # With R = diag(1,-1,-1), objects below the lens have pz > 0 in projector space.
        valid = (
            (u_px >= 0) & (u_px < cfg.width) &
            (v_px >= 0) & (v_px < cfg.height) &
            np.isfinite(offsets) &
            (pz > 0)
        )

        off_valid = offsets[valid]
        u_valid   = u_px[valid]
        v_valid   = v_px[valid]

        # --- Colormap ---
        # offset <= 0  → blue BGR (255, 0, 0) — stop carving
        # 0 < offset <= max_carve_mm → RdYlGn_r (green→yellow→red)
        # NaN → black (already handled by valid mask)

        colors_bgr = np.zeros((off_valid.shape[0], 3), dtype=np.uint8)

        over_carved = off_valid <= 0
        colors_bgr[over_carved] = [255, 0, 0]  # blue

        to_carve = ~over_carved
        if to_carve.any():
            normalized = np.clip(off_valid[to_carve] / cfg.max_carve_mm, 0.0, 1.0)
            rgba = self._cmap(normalized)          # (N, 4) float [0,1]
            r = (rgba[:, 0] * 255).astype(np.uint8)
            g = (rgba[:, 1] * 255).astype(np.uint8)
            b = (rgba[:, 2] * 255).astype(np.uint8)
            colors_bgr[to_carve] = np.stack([b, g, r], axis=-1)  # BGR

        image[v_valid, u_valid] = colors_bgr

        return image

    def display(self, image: np.ndarray) -> None:
        """Display the projection image fullscreen (intended for projector screen)."""
        win = "Projector"
        cv2.namedWindow(win, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(win, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow(win, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
