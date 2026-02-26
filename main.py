# import numpy as np

# from PySide6.QtWidgets import QApplication
# from app import MainWindow

import os
import cv2
import sys
import open3d as o3d
import logging
import matplotlib.pyplot as plt

from core.cloud_compare import CloudCompare
from core.projector import Projector
from helpers.native_silence import redirect_native_output


def setup_logging(debug: bool = False) -> logging.Logger:
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    ))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    return logging.getLogger("capstone")


if __name__ == "__main__":

    # app = QApplication()
    # window = MainWindow()
    # window.show()
    # window.resize(1000, 600)

    # sys.exit(app.exec())

    # Current folder path

    debug = False
    log = setup_logging(debug=debug)

    run_mode = 1
    log.info("Current Run Mode: %s", run_mode)

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    log.info("Current Folder: %s", cur_dir)

    pcd = None
    rgb = None

    if run_mode == 0:
        from core.openni_device import OpenNIDevice
        from core.camera_config import CameraConfig
        from core.depth_camera import DepthCamera
        from core.rgb_camera import RGBCamera
        cfg = CameraConfig()

        with OpenNIDevice() as device:
            
            with redirect_native_output("vendor_native.log", "vendor_native.log"):

                # Initialize cameras
                depth_cam = DepthCamera(device.dev, cfg, debug=debug)
                rgb_cam = RGBCamera(device.dev, cfg, debug=debug)

                log.info("Capturing data...")

                rgb = rgb_cam.capture_rgb()
                pcd = depth_cam.capture_pcd()

                log.info("RGB: %s", "None" if rgb is None else f"{rgb.shape}, min={rgb.min()}, max={rgb.max()}")
                log.info("PCD: %s", "None" if pcd is None else f"{len(pcd.points)} points")

                # # Save RGB
                # if rgb is not None and CameraConfig.save_png:
                #     png_path = os.path.join(cur_dir, "test1.png")
                #     bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                #     ok = cv2.imwrite(png_path, bgr)
                #     log.info("Saved PNG: %s", png_path if ok else "FAILED")
                # else:
                #     log.warning("RGB capture failed; PNG not saved.")

                # # Save PCD
                # if pcd is not None and len(pcd.points) > 0 and CameraConfig.save_pcd:
                #     ply_path = os.path.join(cur_dir, "test1.ply")
                #     ok = o3d.io.write_point_cloud(ply_path, pcd)
                #     log.info("Saved PLY: %s", ply_path if ok else "FAILED")
                # else:
                #     log.warning("PCD capture failed/empty; PLY not saved.")

                # Cleanup
                rgb_cam.stop()
                depth_cam.stop()

    elif run_mode == 1:

        log.info("Loading sample data...")
        pcd_path = os.path.join(cur_dir, "SampleCaptured.ply")
        img_path = os.path.join(cur_dir, "SampleCaptured.png")
        
        if os.path.exists(pcd_path):
            pcd = o3d.io.read_point_cloud(pcd_path)
        if os.path.exists(img_path):
            bgr = cv2.imread(img_path)
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


    # def imshow_with_colorbar(data, title=None):
    #     fig, ax = plt.subplots()
    #     im = ax.imshow(data, cmap="jet")
    #     plt.colorbar(im, ax=ax)
    #     if title:
    #         ax.set_title(title)
    #     plt.tight_layout()
    #     plt.show()

    
    # Proceed only if point cloud was acquired
    if pcd is not None and len(pcd.points) > 0:

        # 1. Prepare CAD Model
        cad_path = os.path.join(cur_dir, "SampleCAD.stl")

        if not os.path.exists(cad_path):
            log.error("CAD file not found at %s", cad_path)
        else:
            log.info("Processing CAD and Point Cloud...")
            cad_model = o3d.io.read_triangle_mesh(cad_path)
            cad_model.compute_vertex_normals()
            
            # Normalize CAD
            cad_model = CloudCompare.normalize_and_align_cad(cad_model)

            # 2. Transform point cloud into CAD/global frame
            CloudCompare.apply_camera_transform(pcd)

            # 3. Compute offsets
            cad_model_raycast = CloudCompare.ray_casting(cad_model)
            offsets = CloudCompare.calculate_offset(pcd, cad_model_raycast)

            log.info("Analysis complete. Offset matrix shape: %s", offsets.shape)

            # Projection step
            proj = Projector()
            proj_image = proj.build_image(offsets, cad_model_raycast)
            log.info("Projection image shape: %s", proj_image.shape)
            proj.display(proj_image)

            # Visualization
            # imshow_with_colorbar(offsets, "Results")
    else:
        log.error("No point cloud data available for comparison.")

    log.info("Done.")