import sys
import threading
from ctypes import *
from datetime import datetime

import numpy as np
from MvCameraControl_class import *


class StreamConstructor:
    def __init__(self, queue, image_callback):
        self.queue = queue
        self.image_callback = image_callback


def GetStreamManager():
    queue = ArrayQueue()

    def image_callback(pData, pFrameInfo, pUser):
        if pData is None or pFrameInfo is None:
            print("ImageCallBack Input Param invalid.")
            return
        pFrameInfo = cast(pFrameInfo, POINTER(MV_FRAME_OUT_INFO_EX)).contents
        queue.push(pFrameInfo, pData)

    winfunctype = CFUNCTYPE
    stFrameInfo = POINTER(MV_FRAME_OUT_INFO_EX)
    pData = POINTER(c_ubyte)
    FrameCallback = winfunctype(None, pData, stFrameInfo, c_void_p)
    return StreamConstructor(queue, FrameCallback(image_callback))


class ImageNode:
    def __init__(self, default_image_len):
        self.pInfo = {}
        self.pData = np.empty(default_image_len, np.uint8)


class ArrayQueue:
    def __init__(self):
        self.size = 0
        self.start = 0
        self.end = 0
        self.Queue = []
        self.Qlen = 0
        self.g_mutex = threading.Lock()

    def init(self, n_buf_count, default_image_len):
        self.Qlen = n_buf_count
        self.Queue = [ImageNode(default_image_len) for _ in range(n_buf_count)]

    def push(self, frame_info, p_data):
        with self.g_mutex:

            node = self.Queue[self.end]

            self.end = (self.end + 1) % self.Qlen
            if self.size < self.Qlen:
                self.size += 1
            else:
                self.start = (self.end + 1) % self.Qlen
            frame_len = frame_info.nFrameLen
            node.pInfo = {
                "size": frame_info.nFrameLen,
                "height": frame_info.nHeight,
                "width": frame_info.nWidth,
                "frame_num": frame_info.nFrameNum,
                "time": datetime.now(),
            }

            memmove(node.pData.ctypes.data, p_data, frame_len)

    def poll(self):
        with self.g_mutex:
            if self.size == 0:
                return None, None  # Equivalent to MV_E_NODATA

            node = self.Queue[self.start]
            # Retrieve data and advance the start index
            self.start = (self.start + 1) % self.Qlen
            self.size -= 1
            return node.pData, node.pInfo
