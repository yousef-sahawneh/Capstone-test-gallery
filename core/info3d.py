import open3d as o3d
import numpy as np
import math
import time
import matplotlib.pyplot as plt
from typing import Annotated


class Info3D():
    def __init__(self):
        self.initializedPcdLocation = False
        self.fixedStock = True
        self.pcd = o3d.geometry.PointCloud()
        self.confidentPcd = o3d.geometry.PointCloud()
        self.mesh = o3d.geometry.TriangleMesh()
        self.meshVertices = None
        self.pcdRotation = (0, 0, 0)
        self.pcdTranslation = (0, 0, 0)
        self.meshRotation = (0, 0, 0)
        self.meshTranslation = (0, 0, 0)

        self.pixSizeX = 0.25 #mm
        self.pixSizeY = 0.25 #mm

        self.vis = o3d.visualization.Visualizer()
        self.vis.create_window()
        self.vis.add_geometry(self.pcd)
    
    # Initializes the camera Pose
    def setCamPose(self, 
                   translation : Annotated[np.typing.ArrayLike, np.float64, '[3, 1]'], 
                   rotation : Annotated[np.typing.ArrayLike, np.float64, '[3, 1]']):
        self.camTranslation = translation
        self.camRotation = rotation
        
    # Set the Point cloud (does not replace it)
    def setPcd(self, pcd : o3d.geometry.PointCloud, confident=False):

        new_points = np.asarray(pcd.points)
        
        # Rotates the inputted PCD from camera frame to global frame
        R = pcd.get_rotation_matrix_from_xyz(self.camRotation)
        T = (self.camTranslation)

        new_points = (R @ new_points.T).T + T
        self.pcd.points = o3d.utility.Vector3dVector(new_points)

        if not self.fixedStock:
            self.comparePcds()
        
        if confident:
            R = pcd.get_rotation_matrix_from_xyz(self.pcdRotation)
            T = (self.pcdTranslation)

            self.confidentPcd = pcd.clone()

    # ICP
    def comparePcds(self):
        print(self.initializedPcdLocation) # This must be true to compare it
        print("TODO")
        # first translate from camera frame to global frame
        # do ICP to get the transformation from one point cloud to the next one (save the translation)
        # Set the pcd to be the new pcd (set confident PCD if confident)
        # Note: add the translation and rotation to the previous one

    # Sets the initial position for the point cloud relative to the cad model for ICP
    def initPtCloudLocation(self):
        # reset the pcd transformation to the origin
        self.pcdRotation = (0, 0, 0)
        self.pcdTranslation = (0, 0, 0)
        self.initializedPcdLocation = True

    # Yousef fill this
    def getHeightMap(self):
        print("TODO")
        # Make a copy of the mesh, and translate it to the pcd transformation (From ICP) if that exists
        # compare the height and return the pixel errors
        # Call inpainting before returning the height map

    
    # TODO yousef
    def inpainting():
        print("TODO")
        # this function takes the pixel values outputted from the height map and 
        # based on the maximum inpainting distance, fills the pixels with missing point cloud data



    # Allows the user to change the location of the mesh
    def setMesh(self, mesh : o3d.geometry.TriangleMesh):
        if self.meshVertices != None:
            self.vis.remove_geometry(self.mesh)

        self.meshRotation = (0, 0, 0)
        self.meshTranslation = (0, 0, 0)
        
        self.initializedPcdLocation = False

        # compute minimum and maximums
        meshVerticies = np.asarray(mesh.vertices)
        min_xyz = meshVerticies.min(axis=0)
        max_xyz = meshVerticies.max(axis=0)

        # translate so that corner is at the axis origin
        mesh.translate((-min_xyz[0], -max_xyz[1], -min_xyz[2]))

        self.meshVertices = np.asarray(mesh.vertices).copy()
        self.mesh = mesh
        self.calculateMeshHeights()

        self.vis.add_geometry(self.mesh)

    
    def setMeshPose(self, 
                    translation : Annotated[np.typing.ArrayLike, np.float64, '[3, 1]'], 
                    rotation : Annotated[np.typing.ArrayLike, np.float64, '[3, 1]']):
        
        self.meshRotation = rotation
        self.meshTranslation = translation

        verts = (self.meshRotation @ self.meshVertices.T).T + self.meshTranslation
        self.mesh.vertices = o3d.utility.Vector3dVector(verts)
        self.calculateMeshHeights()


    def calculateMeshHeights(self):
        if self.mesh == None:
            return
        
        scene = o3d.t.geometry.RaycastingScene()
        scene.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(self.mesh))

        meshVerticies = np.asarray(self.mesh.vertices)
        min_xyz = meshVerticies.min(axis=0)
        max_xyz = meshVerticies.max(axis=0)

        sizeX = (max_xyz[0] - min_xyz[0])
        sizeY = (max_xyz[1] - min_xyz[1])
        zMax = max_xyz[2]

        numPixX = math.ceil(sizeX / self.pixSizeX)
        numPixY = math.ceil(sizeY / self.pixSizeY)
        
        xVals = np.linspace(0, sizeX, numPixX)
        yVals = np.linspace(0, -sizeY, numPixY)
        xv, yv = np.meshgrid(xVals, yVals)

        print(xv.shape)
        zv = np.full(xv.shape, zMax)
        origins = np.stack([xv, yv, zv], axis=-1).reshape(-1, 3)

        # initialize the rays that shoot into the model
        directions = np.tile([0, 0, -1], (origins.shape[0], 1))
        rays = o3d.core.Tensor(
            np.hstack([origins, directions]),
            dtype=o3d.core.Dtype.Float32
        )

        ans = scene.cast_rays(rays)
        t = ans['t_hit'].numpy()
        self.meshHeights = zMax - t
        self.meshHeights[~np.isfinite(t)] = np.nan
        self.meshHeights.reshape(numPixX, numPixY)

    def setPixSizes(self, pixSizeX, pixSizeY):
        self.pixSizeX = pixSizeX
        self.pixSizeY = pixSizeY

        self.calculateMeshHeights()


    def detectCamPose(self):
        print("TODO")
        # call the camera to get a 3d frame
        # cearch for defined landmarks to get the 3d orientation of the camera
        # Call setCamPose


# TODO
# warning call that warns you that your point cloud position is uninitialized (user can ignore)
# Add stl rotation and translation