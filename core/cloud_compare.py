import numpy as np
import open3d as o3d

from core.cloud_compare_config import CompareConfig

class CloudCompare:

    @staticmethod
    def normalize_and_align_cad(cad_model: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
        cad_vertices = np.asarray(cad_model.vertices)
        min_xyz = cad_vertices.min(axis=0)
        max_xyz = cad_vertices.max(axis=0)

        # Aligns the CAD model to the origin based on its bounding box.
        # Note: TriangleMesh.translate() segfaults on open3d 0.18 / macOS arm64,
        # so we mutate the vertex array directly instead.
        new_verts = cad_vertices.copy()
        new_verts += np.array([-min_xyz[0], -max_xyz[1], -min_xyz[2]])
        cad_model.vertices = o3d.utility.Vector3dVector(new_verts)

        return cad_model

    @staticmethod
    def apply_camera_transform(pcd: o3d.geometry.PointCloud) -> None:
        """Applies transformation using values from CompareConfig."""
        # Note: open3d 0.18 / macOS arm64 segfaults on .rotate(), .translate(),
        # and .get_rotation_matrix_from_xyz().  Build the XYZ Euler rotation
        # matrix with numpy and apply it by mutating the points array directly.
        rx = CompareConfig.cam_rot_x
        ry = CompareConfig.cam_rot_y
        rz = CompareConfig.cam_rot_z
        Rx = np.array([[1, 0, 0],
                       [0, np.cos(rx), -np.sin(rx)],
                       [0, np.sin(rx),  np.cos(rx)]])
        Ry = np.array([[ np.cos(ry), 0, np.sin(ry)],
                       [0,           1, 0          ],
                       [-np.sin(ry), 0, np.cos(ry)]])
        Rz = np.array([[np.cos(rz), -np.sin(rz), 0],
                       [np.sin(rz),  np.cos(rz), 0],
                       [0,           0,           1]])
        R = Rz @ Ry @ Rx

        T = np.array([CompareConfig.cam_trans_x, CompareConfig.cam_trans_y, CompareConfig.cam_trans_z])

        pts = np.asarray(pcd.points).copy()
        pts = pts @ R.T
        pts += T
        pcd.points = o3d.utility.Vector3dVector(pts)

    @staticmethod
    def ray_casting(cad_model: o3d.geometry.TriangleMesh) -> np.ndarray:
        scene = o3d.t.geometry.RaycastingScene()
        scene.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(cad_model))

        x_vals = np.linspace(0, CompareConfig.base_plate_x, CompareConfig.num_col_x)
        y_vals = np.linspace(0, -CompareConfig.base_plate_y, CompareConfig.num_row_y)

        z_max = np.asarray(cad_model.vertices).max(axis=0)[2]

        xv, yv = np.meshgrid(x_vals, y_vals)
        zv = np.full(xv.shape, z_max)

        origins = np.stack([xv, yv, zv], axis=-1).reshape(-1, 3)
        directions = np.tile([0, 0, -1], (origins.shape[0], 1))

        rays = o3d.core.Tensor(np.hstack([origins, directions]), dtype=o3d.core.Dtype.Float32)
        hits = scene.cast_rays(rays)
        t = hits["t_hit"].numpy()

        z = z_max - t
        z[~np.isfinite(t)] = np.nan

        return z.reshape(CompareConfig.num_col_x, CompareConfig.num_row_y)

    @staticmethod
    def calculate_offset(pcd: o3d.geometry.PointCloud, cad_raycast: np.ndarray) -> np.ndarray:
        p = np.asarray(pcd.points)
        x, y, z = p[:, 0], p[:, 1], p[:, 2]

        x_edges = np.linspace(0, CompareConfig.base_plate_x, CompareConfig.num_col_x + 1)
        y_edges = np.linspace(0, -CompareConfig.base_plate_y, CompareConfig.num_row_y + 1)

        i = np.digitize(x, x_edges) - 1
        j = np.digitize(y, y_edges) - 1

        valid = (i >= 0) & (i < CompareConfig.num_col_x) & (j >= 0) & (j < CompareConfig.num_row_y)
        i, j, z = i[valid], j[valid], z[valid]

        idx = i * CompareConfig.num_row_y + j
        n_bins = CompareConfig.num_col_x * CompareConfig.num_row_y

        z_sum = np.bincount(idx, weights=z, minlength=n_bins)
        z_cnt = np.bincount(idx, minlength=n_bins)

        mean_z = np.full(n_bins, np.nan, dtype=np.float64)
        nz = z_cnt > 0
        mean_z[nz] = z_sum[nz] / z_cnt[nz]
        mean_z = mean_z.reshape(CompareConfig.num_col_x, CompareConfig.num_row_y)

        offset = mean_z - cad_raycast
        offset[np.isnan(cad_raycast)] = np.nan

        return offset