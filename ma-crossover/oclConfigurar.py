#Embedded file name: /home/kilikkuo/Projects/pyopencl-example/financial-cl/ma-crossover/oclConfigurar.py
import pyopencl as cl
PREFERRED_GPU = 0
PREFERRED_CPU = 1
PREFERRED_MCU = 2

class OCLConfigurar:

    def __init__(self):
        self.dicIdx2Platform = {}
        self.dicPlatform2Devices = {}
        self.__parseInfo()

    def __parseInfo(self):
        for idx, platform in enumerate(cl.get_platforms()):
            self.dicIdx2Platform[idx] = platform
            self.dicPlatform2Devices[platform] = platform.get_devices()

    def __getDefaultDevice(self):
        platform = self.dicIdx2Platform[0]
        default_dev = platform.get_devices(device_type=cl.device_type.DEFAULT)
        return cl.Context(devices=default_dev)

    def getContext(self, DEVICE = PREFERRED_GPU):
        assert len(self.dicIdx2Platform) > 0, 'No platform'
        context = None
        if DEVICE == PREFERRED_CPU:
            for lstDev in self.dicPlatform2Devices.itervalues():
                for dev in lstDev:
                    if 'CPU' in cl.device_type.to_string(dev.type):
                        context = cl.Context(devices=[dev])
                        break

        elif DEVICE == PREFERRED_MCU:
            mcu_dev = None
            mcu = 0
            for lstDev in self.dicPlatform2Devices.itervalues():
                for dev in lstDev:
                    if dev.max_compute_units > mcu:
                        mcu = dev.max_compute_units
                        mcu_dev = dev

            context = cl.Context(devices=[mcu_dev])
        else:
            for lstDev in self.dicPlatform2Devices.itervalues():
                for dev in lstDev:
                    if 'GPU' in cl.device_type.to_string(dev.type):
                        context = cl.Context(devices=[dev])
                        break

        if not context:
            context = self.__getDefaultDevice()
        return context
