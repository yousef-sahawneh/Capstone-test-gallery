# from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6 import QtWidgets, QtGui, QtCore
from OpenGL.GL import *
import open3d as o3d
import win32gui

class Viewer3D(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # TODO initialize info3d, plus callbacks for all the things users might change + point cloud update

        hwnd = win32gui.FindWindowEx(0, 0, None, "Open3D")
        self.window = QtGui.QWindow.fromWinId(hwnd)
        self.windowcontainer = self.createWindowContainer(self.window)

        mainLayout = QtWidgets.QGridLayout()
        mainLayout.addWidget(self.windowcontainer, 0, 0)
        self.setLayout(mainLayout)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_vis)
        timer.start(1)

    def update_vis(self):
        self.vis.poll_events()
        self.vis.update_renderer()

    def addPtc(self, pcd : o3d.geometry.PointCloud):
        # pcd = o3d.io.read_point_cloud("Testing_1.ply")
        self.vis.add_geometry(pcd)

