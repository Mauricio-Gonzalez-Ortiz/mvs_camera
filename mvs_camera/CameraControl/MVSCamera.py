import sys
import warnings
from ctypes import *

from MvCameraControl_class import *
from StreamFrame_Control import *


class MvsCamera:
    def __init__(self) -> None:
        MvCamera.MV_CC_Initialize()
        device = self.__manage_devices()
        device = cast(device, POINTER(MV_CC_DEVICE_INFO)).contents
        self.cam = MvCamera()
        ret = self.cam.MV_CC_CreateHandle(device)
        if ret != 0:
            raise RuntimeError("Create handle failed")

        ret = self.cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
        if ret != 0:
            raise RuntimeError("Open Device failed")

        self.__create_cam_params()
        ret = self.cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
        # self.set_enum_value("TriggerMode", MV_TRIGGER_MODE_OFF)

        if device.nTLayerType in [MV_GIGE_DEVICE, MV_GENTL_GIGE_DEVICE]:  # type: ignore
            optimal_packet_size = self.cam.MV_CC_GetOptimalPacketSize()
            if int(optimal_packet_size) > 0:
                self.set_int_value("GevSCPSPacketSize", optimal_packet_size)

        ret = self.cam.MV_CC_SetBoolValue("AcquisitionFrameRateEnable", False)
        if ret != 0:
            raise RuntimeError("Set AcquisitionFrameRateEnable fail!")
        self.frame_number = None

    def start_stream(self, stream_manager: StreamConstructor, buff_size=5):
        queue = stream_manager.queue
        queue.init(buff_size, self.size)
        ret = self.cam.MV_CC_RegisterImageCallBackEx(
            stream_manager.image_callback, None
        )
        if ret != 0:
            print("Register callback fail! ret[0x%x]" % ret)

        ret = self.cam.MV_CC_StartGrabbing()

        if ret != 0:
            print("Start grabbing fail! ret[0x%x]" % ret)
            sys.exit()
        self._is_stream = True

    def get_frame(self, stream_manager: StreamConstructor = None):
        if self._is_stream:
            if stream_manager is not None:
                return stream_manager.queue.poll()
            else:
                raise RuntimeError("No Stream Constructor has been provided")

    @property
    def height(self):
        return self.get_int_value("Height")

    @height.setter
    def height(self, value):
        self.set_int_value("Height", value)

    @property
    def width(self):
        return self.get_int_value("Width")

    @width.setter
    def width(self, value):
        self.set_int_value("Width", value)

    @property
    def size(self):
        return self.get_int_value("PayloadSize")

    def __create_cam_params(self):
        self.intParams = MVCC_INTVALUE()
        self.floatParams = MVCC_FLOATVALUE()
        self.strParams = MVCC_STRINGVALUE()
        self.enumParams = MVCC_ENUMVALUE()

        memset(byref(self.intParams), 0, sizeof(MVCC_INTVALUE))
        memset(byref(self.floatParams), 0, sizeof(MVCC_FLOATVALUE))
        memset(byref(self.strParams), 0, sizeof(MVCC_STRINGVALUE))
        memset(byref(self.enumParams), 0, sizeof(MVCC_ENUMVALUE))

    def get_int_value(self, name):
        ret = self.cam.MV_CC_GetIntValue(name, self.intParams)
        if ret != 0:
            warnings.warn(f"Get {name} failed")
            return None
        return self.intParams.nCurValue

    def set_int_value(self, name, value):
        ret = self.cam.MV_CC_SetIntValue(name, value)
        if ret != 0:
            warnings.warn(f"Set {name} to {value} failed")

    def get_str_value(self, name):
        ret = self.cam.MV_CC_GetStringValue(name, self.intParams)
        if ret != 0:
            warnings.warn(f"Get {name} failed")
            return None
        return self.strParams.nCurValue

    def set_str_value(self, name, value):
        ret = self.cam.MV_CC_SetStringValue(name, value)
        if ret != 0:
            warnings.warn(f"Set {name} to {value} failed")

    def get_enum_value(self, name):
        ret = self.cam.MV_CC_GetEnumValue(name, self.intParams)
        if ret != 0:
            warnings.warn(f"Get {name} failed")
            return None
        return self.enumParams.nCurValue

    def set_enum_value(self, name, value):
        ret = self.cam.MV_CC_SetEnumValue(name, value)
        if ret != 0:
            warnings.warn(f"Set {name} to {value} failed")

    def get_float_value(self, name):
        ret = self.cam.MV_CC_GetFloatValue(name, self.intParams)
        if ret != 0:
            warnings.warn(f"Get {name} failed")
            return None
        return self.floatParams.nCurValue

    def set_float_value(self, name, value):
        ret = self.cam.MV_CC_SetFloatValue(name, value)
        if ret != 0:
            warnings.warn(f"Set {name} to {value} failed")

    def __manage_devices(self):

        deviceList = MV_CC_DEVICE_INFO_LIST()

        tlayerType = (
            MV_GIGE_DEVICE  # type: ignore
            | MV_USB_DEVICE  # type: ignore
            | MV_GENTL_CAMERALINK_DEVICE  # type: ignore
            | MV_GENTL_CXP_DEVICE  # type: ignore
            | MV_GENTL_XOF_DEVICE  # type: ignore
        )
        ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)

        if ret != 0:
            raise RuntimeError("Couldn't enumerate devices")

        num_devices = deviceList.nDeviceNum
        if num_devices == 0:
            raise RuntimeError("No camera found")

        if num_devices == 1:
            return deviceList.pDeviceInfo[0]
        return self.__device_selector(deviceList, num_devices)

    def __device_selector(self, deviceList, num_devices):

        for i in range(0, num_devices):
            mvcc_dev_info = cast(
                deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)
            ).contents
            layer_type = mvcc_dev_info.nTLayerType
            if layer_type in [MV_GIGE_DEVICE, MV_GENTL_GIGE_DEVICE]:
                print("\ngige device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                nip1 = (
                    mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xFF000000
                ) >> 24
                nip2 = (
                    mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00FF0000
                ) >> 16
                nip3 = (
                    mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000FF00
                ) >> 8
                nip4 = mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000FF
                print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
            elif layer_type == MV_USB_DEVICE:
                print("\nu3v device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)
            elif layer_type == MV_GENTL_CAMERALINK_DEVICE:
                print("\nCML device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stCMLInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stCMLInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)
            elif layer_type == MV_GENTL_XOF_DEVICE:
                print("\nXoF device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stXoFInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stXoFInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)
            elif layer_type == MV_GENTL_CXP_DEVICE:
                print("\nCXP device: [%d]" % i)
                strModeName = ""
                for per in mvcc_dev_info.SpecialInfo.stCXPInfo.chModelName:
                    if per == 0:
                        break
                    strModeName = strModeName + chr(per)
                print("device model name: %s" % strModeName)

                strSerialNumber = ""
                for per in mvcc_dev_info.SpecialInfo.stCXPInfo.chSerialNumber:
                    if per == 0:
                        break
                    strSerialNumber = strSerialNumber + chr(per)
                print("user serial number: %s" % strSerialNumber)

        while True:
            device_num = int(input("please input the number of the device to connect:"))
            if 0 <= device_num < num_devices:
                return deviceList.pDeviceInfo[device_num]
            print("Please select a valid number")


if __name__ == "__main__":
    cam = MvsCamera()
    cam.start_stream()

    while True:
        continue
