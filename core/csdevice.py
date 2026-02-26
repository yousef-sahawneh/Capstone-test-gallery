# -*- coding: utf-8 -*-
# @File   : csdevice.py
# @Date   : 2020/12/25
# @Author : PengLei
# @Mail   : penglei@chishine3d.com
# @bref   : extension property invoker

import ctypes
import numpy as np
from openni import _openni2
from enum import Enum
import time

# **********************************************************************************************************************
# Device property ID
# **********************************************************************************************************************
CS_PROPERTY_DEVICE_BASE = (0xD0000000)
CS_PROPERTY_DEVICE_IR_MODE = (CS_PROPERTY_DEVICE_BASE + 0x01)
CS_PROPERTY_DEVICE_EXTRINSICS = (CS_PROPERTY_DEVICE_BASE + 0x02)

# **********************************************************************************************************************
# Extension property ID
# **********************************************************************************************************************
CS_PROPERTY_STREAM_BASE                    = (0xE0000000)
CS_PROPERTY_STREAM_INTRINSICS              = (CS_PROPERTY_STREAM_BASE + 0x01)  # Intrinsics of depth camera or RGB camera
CS_PROPERTY_STREAM_EXT_DEPTH_RANGE         = (CS_PROPERTY_STREAM_BASE + 0x02)  # depth range of camera
CS_PROPERTY_STREAM_EXT_HDR_MODE            = (CS_PROPERTY_STREAM_BASE + 0x03)  # HDR mode
CS_PROPERTY_STREAM_EXT_HDR_SCALE_SETTING   = (CS_PROPERTY_STREAM_BASE + 0x04)  # setting of auto-HDR
CS_PROPERTY_STREAM_EXT_HDR_EXPOSURE        = (CS_PROPERTY_STREAM_BASE + 0x05)  # all params of HDR
CS_PROPERTY_STREAM_EXT_DEPTH_SCALE         = (CS_PROPERTY_STREAM_BASE + 0x06)  # depth unit for real distance
CS_PROPERTY_STREAM_EXT_TRIGGER_MODE        = (CS_PROPERTY_STREAM_BASE + 0x07)  # trigger mode
CS_PROPERTY_STREAM_EXT_CONTRAST_MIN        = (CS_PROPERTY_STREAM_BASE + 0x08)  # remove where fringe contrast below this value
CS_PROPERTY_STREAM_EXT_FRAMETIME           = (CS_PROPERTY_STREAM_BASE + 0x09)  # Frame time of depth camera
CS_PROPERTY_STREAM_EXT_DISTORT             = (CS_PROPERTY_STREAM_BASE + 0x11)  # distort of depth camera or rgb camera
CS_PROPERTY_STREAM_EXT_SOFT_TRIGGER        = (CS_PROPERTY_STREAM_BASE + 0x15)  # soft trigger.
CS_PROPERTY_STREAM_LED_CTRL                = (CS_PROPERTY_STREAM_BASE + 0x20)  # RGB or Depth LED ctrl.
CS_PROPERTY_STREAM_RGB_EXP_US              = (CS_PROPERTY_STREAM_BASE + 0x21)  # RGB exposure us unit.

# Distort of depth camera or RGB camera
class Distort(ctypes.Structure):
    _fields_ = [("k1", ctypes.c_float),
                ("k2", ctypes.c_float),
                ("k3", ctypes.c_float),
                ("k4", ctypes.c_float),
                ("k5", ctypes.c_float)]

    def __repr__(self):
        return 'Distort(k1 = %r, k2 = %r, k3 = %r, k4 = %r, k5 = %r)' % (
            self.k1, self.k2, self.k3, self.k4, self.k5)

# Intrinsics of depth camera or RGB camera
class Intrinsics(ctypes.Structure):
    _fields_ = [("width", ctypes.c_short),
                ("height", ctypes.c_short),
                ("fx", ctypes.c_float),
                ("zero01", ctypes.c_float),
                ("cx", ctypes.c_float),
                ("zeor10", ctypes.c_float),
                ("fy", ctypes.c_float),
                ("cy", ctypes.c_float),
                ("zeor20", ctypes.c_float),
                ("zero21", ctypes.c_float),
                ("one22", ctypes.c_float)]

    def __repr__(self):
        return 'Intrinsics(width = %r, height = %r, fx = %r, fy = %r, cx = %r, cy = %r, zero01 = %r, zeor10 = %r, ' \
               'zeor20 = %r, zero21 = %r, one22 = %r)' % (
                   self.width, self.height, self.fx, self.fy, self.cx, self.cy, self.zero01, self.zeor10, self.zeor20,
                   self.zero21, self.one22)

# Rotation and translation offrom depth camera to RGB camera
class Extrinsics(ctypes.Structure):
    _fields_ = [("rotation", ctypes.c_float * 9),
                ("translation", ctypes.c_float * 3)]

    def __repr__(self):
        return 'Extrinsics(rotation = %r, translation = %r)' % (self.rotation, self.translation)

# range of depth， value out of range will be set to zero
class DepthRange(ctypes.Structure):
    _fields_ = [("min", ctypes.c_int),
                ("max", ctypes.c_int)]

    def __repr__(self):
        return 'DepthRange(min = %r, max = %r)' % (self.min, self.max)



# exposure times and interstage scale of HDR
class HdrScaleSetting(ctypes.Structure):
    _fields_ = [("highReflectModeCount", ctypes.c_uint),
                ("highReflectModeScale", ctypes.c_uint),
                ("lowReflectModeCount", ctypes.c_uint),
                ("lowReflectModeScale", ctypes.c_uint)]

    def __repr__(self):
        return 'HdrScaleSetting(highReflectModeCount = %r, highReflectModeScale = %r, lowReflectModeCount = %r, lowReflectModeScale = %r)' \
            % (self.highReflectModeCount, self.highReflectModeScale, self.lowReflectModeCount, self.lowReflectModeScale)

# exposure param of HDR
class HdrExposureParam(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("exposure", ctypes.c_uint),
                ("gain", ctypes.c_ubyte)]

    def __repr__(self):
        return 'HdrExposureParam(exposure = %r, gain = %r)' % (self.exposure, self.gain)

# all exposure params of HDR
class HdrExposureSetting(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("count", ctypes.c_ubyte),
                ("param", HdrExposureParam * 11)]

    def __repr__(self):
        return 'HdrExposureSetting(count = %r, param = %r)' % (self.count, self.param)

def generatePointCloud(frame, intrinsics):
    pc = []
    frame_data = np.array(frame.get_buffer_as_uint16()).reshape(
        [frame.height, frame.width])
    if frame.videoMode.pixelFormat == _openni2.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_100_UM:
        depthScale = 0.1
    elif frame.videoMode.pixelFormat == _openni2.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM:
        depthScale = 1.0
    else:
        pc = np.array(pc)
        return pc

    fx = intrinsics.fx * frame.width / intrinsics.width
    fy = intrinsics.fy * frame.height / intrinsics.height
    cx = intrinsics.cx * frame.width / intrinsics.width
    cy = intrinsics.cy * frame.height / intrinsics.height

    for v in range(frame.height):
        for u in range(frame.width):
            if frame_data[v, u] > 0:
                z = frame_data[v, u] * depthScale
                x = (u - cx) * z / fx
                y = (v - cy) * z / fy
                pc.append([x, y, z])

    pc = np.array(pc)
    return pc

def generatePointCloud1(frame, intrinsics):
    pc = []
    frame_data = np.array(frame.get_buffer_as_uint16()).reshape(
        [frame.height, frame.width])
    if frame.videoMode.pixelFormat == _openni2.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_100_UM:
        depthScale = 0.1
    elif frame.videoMode.pixelFormat == _openni2.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM:
        depthScale = 1.0
    else:
        pc = np.array(pc)
        return pc

    fx = intrinsics.fx * frame.width / intrinsics.width
    fy = intrinsics.fy * frame.height / intrinsics.height
    cx = intrinsics.cx * frame.width / intrinsics.width
    cy = intrinsics.cy * frame.height / intrinsics.height

    inz = np.nonzero(frame_data)

    zz = frame_data * depthScale

    ur = np.array([np.arange(frame.width)])
    uh = np.repeat(ur, frame.height, axis=0)
    uscx = uh - cx
    uscxdz = uscx * zz
    xx = uscxdz / fx

    vc = np.array([np.arange(frame.height)]).T
    vw = np.repeat(vc, frame.width, axis=1)
    vscy = vw - cy
    vscydz = vscy * zz
    yy = vscydz / fy

    pc1 = np.array([xx, yy, zz]).transpose((1, 2, 0))

    pc2 = pc1[inz]

    return pc2

def generateRGBFrame(frame, intrinsics, extrinsics, intrinsics_rgb, rgb_height, rgb_width):
    frame_data = np.array(frame.get_buffer_as_uint16()).reshape([frame.height, frame.width])
    frame_data_in_rgb_view = np.zeros((rgb_height, rgb_width))

    if frame.videoMode.pixelFormat == _openni2.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_100_UM:
        depthScale = 0.1
    elif frame.videoMode.pixelFormat == _openni2.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM:
        depthScale = 1.0
    else:
        return frame_data_in_rgb_view

    fx = intrinsics.fx * frame.width / intrinsics.width
    fy = intrinsics.fy * frame.height / intrinsics.height
    cx = intrinsics.cx * frame.width / intrinsics.width
    cy = intrinsics.cy * frame.height / intrinsics.height

    for v in range(frame.height):
        for u in range(frame.width):
            if frame_data[int(v),int(u)] > 0:
                z = frame_data[int(v), int(u)] * depthScale
                x = (u - cx) * z / fx
                y = (v - cy) * z / fy

                x = x + extrinsics.translation[0]
                y = y + extrinsics.translation[1]
                z = z + extrinsics.translation[2]

                x_ = x * extrinsics.rotation[0] + y * extrinsics.rotation[1] + z * extrinsics.rotation[2]
                y_ = x * extrinsics.rotation[3] + y * extrinsics.rotation[4] + z * extrinsics.rotation[5]
                z_ = x * extrinsics.rotation[6] + y * extrinsics.rotation[7] + z * extrinsics.rotation[8]

                x = x_
                y = y_
                z = z_

                u_ = (intrinsics_rgb.fx * x / z + intrinsics_rgb.cx) / intrinsics_rgb.width * rgb_width
                v_ = (intrinsics_rgb.fy * y / z + intrinsics_rgb.cy) / intrinsics_rgb.height * rgb_height
                z = z * 10
                if u_ >= 0 and u_ < rgb_width and v_ >= 0 and v_ <= rgb_height:
                    frame_data_in_rgb_view[int(v_), int(u_)] = int(z)

    return frame_data_in_rgb_view

def generateRGBFrame1(frame, intrinsics, extrinsics, intrinsics_rgb, rgb_height, rgb_width):
    frame_data = np.array(frame.get_buffer_as_uint16()).reshape([frame.height, frame.width])
    frame_data_in_rgb_view = np.zeros((rgb_height, rgb_width))

    if frame.videoMode.pixelFormat == _openni2.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_100_UM:
        depthScale = 0.1
    elif frame.videoMode.pixelFormat == _openni2.OniPixelFormat.ONI_PIXEL_FORMAT_DEPTH_1_MM:
        depthScale = 1.0
    else:
        return frame_data_in_rgb_view

    fx = intrinsics.fx * frame.width / intrinsics.width
    fy = intrinsics.fy * frame.height / intrinsics.height
    cx = intrinsics.cx * frame.width / intrinsics.width
    cy = intrinsics.cy * frame.height / intrinsics.height

    zz = frame_data * depthScale

    ur = np.array([np.arange(frame.width)])
    uh = np.repeat(ur, frame.height, axis=0)
    uscx = uh - cx
    uscxdz = uscx * zz
    xx = uscxdz / fx

    vc = np.array([np.arange(frame.height)]).T
    vw = np.repeat(vc, frame.width, axis=1)
    vscy = vw - cy
    vscydz = vscy * zz
    yy = vscydz / fy

    xx = xx + extrinsics.translation[0]
    yy = yy + extrinsics.translation[1]
    zz = zz + extrinsics.translation[2]

    x_ = xx * extrinsics.rotation[0] + yy * extrinsics.rotation[1] + zz * extrinsics.rotation[2]
    y_ = xx * extrinsics.rotation[3] + yy * extrinsics.rotation[4] + zz * extrinsics.rotation[5]
    z_ = xx * extrinsics.rotation[6] + yy * extrinsics.rotation[7] + zz * extrinsics.rotation[8]

    xx = x_
    yy = y_
    zz = z_

    uu_ = (intrinsics_rgb.fx * xx / zz + intrinsics_rgb.cx) / intrinsics_rgb.width * rgb_width
    vv_ = (intrinsics_rgb.fy * yy / zz + intrinsics_rgb.cy) / intrinsics_rgb.height * rgb_height
    zz = zz * 10

    ub1 = uu_ >= 0
    ub2 = uu_ < rgb_width
    ub = ub1 & ub2

    vb1 = vv_ >= 0
    vb2 = vv_ < rgb_height
    vb = vb1 & vb2

    uvb = ub & vb
    ind = np.argwhere(uvb)

    uv = np.array([vv_, uu_]).transpose((1, 2, 0))

    pci = uv[ind[:,0],ind[:,1]].astype('i')

    frame_data_in_rgb_view[pci[:,0],pci[:,1]] = zz[ind[:,0],ind[:,1]].astype('i');

    return frame_data_in_rgb_view;
