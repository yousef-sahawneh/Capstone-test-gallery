import sys

from PySide6 import QtWidgets, QtGui, QtCore

from .viewer3d import Viewer3D

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.viewer_3d = Viewer3D()

        # viewer_3d = QPushButton("viewer3D") ##TODO
        side_bar = QtWidgets.QPushButton("sideBar") ##TODO
        side_bar.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        main_splitter = QtWidgets.QSplitter()
        main_splitter.addWidget(self.viewer_3d)
        main_splitter.addWidget(side_bar)
        main_splitter.setSizes([200, 100])

        self.setCentralWidget(main_splitter)
        self.setWindowTitle("Woodcarving Dexterity")


#TODO add ui elements here + you can create sub elements too if you want