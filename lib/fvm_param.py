#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import collections
import configparser

class FvmParam:
    """Virt-machine directory structure:
         [vmname]
           |--element.ini                            element file
           |--fqemu.hw                                config file
           |--fqemu.win                                config file
           |--disk-main.img                            system disk image
    """

    def __init__(self):
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.pwd = os.getcwd()

        self.libDir = "/usr/lib/fpemud-vmake"
        self.tmpDir = ""

        self.macOuiBr = "00:50:00"
        self.macOuiVm = "00:50:01"

        self.spicePortStart = 5910
        self.spicePortEnd = 5999

class FvmConfigBasic:

    name = None                                    # str
    title = None                                # str
    description = None                            # str

    def checkValid(self):
        """if FvmConfigBasic object is invalid, raise exception"""

        if self.name is None or not isinstance(self.name, str):
            raise Exception("name is invalid")

        if self.title is None or not isinstance(self.title, str):
            raise Exception("title is invalid")

        if self.description is None or not isinstance(self.description, str):
            raise Exception("description is invalid")

    def readFromDisk(self, fileName):
        """read object from disk"""

        # fixme: cfg.read(fileName) won't raise exception when file not exist, strange
        if not os.path.exists(fileName):
            raise Exception("config file \"%s\" does not exist"%(fileName))

        cfg = configparser.SafeConfigParser()
        cfg.optionxform = str                                # make option names case-sensitive
        cfg.read(fileName) 

        self.name = cfg.get("Element Entry", "Name")
        self.description = cfg.get("Element Entry", "Comment")

    def writeToDisk(self, fileName):
        """write object to disk"""

        cfg = configparser.SafeConfigParser()
        cfg.optionxform = str                                # make option names case-sensitive

        cfg.add_section("Element Entry")
        cfg.set("Element Entry", "Name", self.name)
        cfg.set("Element Entry", "Comment", self.description)
        cfg.set("Element Entry", "Type", "virtual-machine")

        cfg.write(open(fileName, "w"))

class FvmConfigHardware:

    qemuVmType = None                            # str        "pc", "q35"
    cpuArch = None                                # str
    cpuNumber = None                            # int
    memorySize = None                            # int        unit: MB
    mainDiskInterface = None                    # str        "virtio-blk" => "ide", '=>' means 'can fallback to'
    mainDiskFormat = None                        # str        "raw-sparse" => "qcow2"
    mainDiskSize = None                            # int        unit: MB
    graphicsAdapterInterface = None                # str        "qxl" => "vga"
    graphicsAdapterPciSlot = None                # int
    soundAdapterInterface = None                # str        "ac97" => ""
    soundAdapterPciSlot = None                    # int
    networkAdapterInterface = None                # str        "virtio" => "user" => ""
    networkAdapterPciSlot = None                # int
    balloonDeviceSupport = None                    # bool
    balloonDevicePciSlot = None                    # int
    vdiPortDeviceSupport = None                    # bool
    vdiPortDevicePciSlot = None                    # int
    shareDirectoryNumber = None                    # int
    shareDirectoryHotplugSupport = None            # bool
    shareUsbNumber = None                        # int
    shareUsbHotplugSupport = None                # bool
    shareScsiNumber = None                        # int
    shareScsiHotplugSupport = None                # bool

    def checkValid(self):
        """if FvmConfigHardware object is invalid, raise exception"""

        validQemuVmType = [ "pc", "q35" ]
        validArch = [ "x86", "amd64" ]
        validDiskInterface = [ "virtio-blk", "ide" ]
        validDiskFormat = [ "raw-sparse", "qcow2" ]
        validGraphicsAdapterInterface = [ "qxl", "vga" ]
        validSoundAdapterInterface = [ "ac97", "" ]
        validNetworkAdapterInterface = [ "virtio", "user", "" ]

        if self.qemuVmType is None or not isinstance(self.qemuVmType, str):
            raise Exception("qemuVmType is invalid")
        if self.qemuVmType not in validQemuVmType:
            raise Exception("qemuVmType is invalid")

        if self.cpuArch is None or not isinstance(self.cpuArch, str):
            raise Exception("cpuArch is invalid")
        if self.cpuArch not in validArch:
            raise Exception("cpuArch is invalid")

        if self.cpuNumber is None or not isinstance(self.cpuNumber, int):
            raise Exception("cpuNumber is invalid")
        if self.cpuNumber <= 0:
            raise Exception("cpuNumber is invalid")

        if self.memorySize is None or not isinstance(self.memorySize, int):
            raise Exception("memorySize is invalid")
        if self.memorySize <= 0:
            raise Exception("memorySize is invalid")

        if self.mainDiskInterface is None or not isinstance(self.mainDiskInterface, str):
            raise Exception("mainDiskInterface is invalid")
        if self.mainDiskInterface not in validDiskInterface:
            raise Exception("mainDiskInterface is invalid")

        if self.mainDiskFormat is None or not isinstance(self.mainDiskFormat, str):
            raise Exception("mainDiskFormat is invalid")
        if self.mainDiskFormat not in validDiskFormat:
            raise Exception("mainDiskFormat is invalid")

        if self.mainDiskSize is None or not isinstance(self.mainDiskSize, int):
            raise Exception("mainDiskSize is invalid")
        if self.mainDiskSize <= 0:
            raise Exception("mainDiskSize is invalid")

        if self.graphicsAdapterInterface is None or not isinstance(self.graphicsAdapterInterface, str):
            raise Exception("graphicsAdapterInterface is invalid")
        if self.graphicsAdapterInterface not in validGraphicsAdapterInterface:
            raise Exception("graphicsAdapterInterface is invalid")

        if self.graphicsAdapterPciSlot is None or not isinstance(self.graphicsAdapterPciSlot, int):
            raise Exception("graphicsAdapterPciSlot is invalid")

        if self.soundAdapterInterface is None or not isinstance(self.soundAdapterInterface, str):
            raise Exception("soundAdapterInterface is invalid")
        if self.soundAdapterInterface not in validSoundAdapterInterface:
            raise Exception("soundAdapterInterface is invalid")

        if self.soundAdapterInterface != "":
            if self.soundAdapterPciSlot is None or not isinstance(self.soundAdapterPciSlot, int):
                raise Exception("soundAdapterPciSlot is invalid")

        if self.networkAdapterInterface is None or not isinstance(self.networkAdapterInterface, str):
            raise Exception("networkAdapterInterface is invalid")
        if self.networkAdapterInterface not in validNetworkAdapterInterface:
            raise Exception("networkAdapterInterface is invalid")

        if self.networkAdapterInterface != "":
            if self.networkAdapterPciSlot is None or not isinstance(self.networkAdapterPciSlot, int):
                raise Exception("networkAdapterPciSlot is invalid")

        if self.balloonDeviceSupport is None or not isinstance(self.balloonDeviceSupport, bool):
            raise Exception("balloonDeviceSupport is invalid")

        if self.balloonDeviceSupport:
            if self.balloonDevicePciSlot is None or not isinstance(self.balloonDevicePciSlot, int):
                raise Exception("balloonDevicePciSlot is invalid")

        if self.vdiPortDeviceSupport is None or not isinstance(self.vdiPortDeviceSupport, bool):
            raise Exception("vdiPortDeviceSupport is invalid")

        if self.vdiPortDeviceSupport:
            if self.vdiPortDevicePciSlot is None or not isinstance(self.vdiPortDevicePciSlot, int):
                raise Exception("vdiPortDevicePciSlot is invalid")

        if self.shareDirectoryNumber is None or not isinstance(self.shareDirectoryNumber, int):
            raise Exception("shareDirectoryNumber is invalid")
        if self.shareDirectoryNumber < 0:
            raise Exception("shareDirectoryNumber is invalid")

        if self.shareDirectoryHotplugSupport is None or not isinstance(self.shareDirectoryHotplugSupport, bool):
            raise Exception("shareDirectoryHotplugSupport is invalid")

        if self.shareUsbNumber is None or not isinstance(self.shareUsbNumber, int):
            raise Exception("shareUsbNumber is invalid")
        if self.shareUsbNumber < 0:
            raise Exception("shareUsbNumber is invalid")

        if self.shareUsbHotplugSupport is None or not isinstance(self.shareUsbHotplugSupport, bool):
            raise Exception("shareUsbHotplugSupport is invalid")

        if self.shareScsiNumber is None or not isinstance(self.shareScsiNumber, int):
            raise Exception("shareScsiNumber is invalid")
        if self.shareScsiNumber < 0:
            raise Exception("shareScsiNumber is invalid")

        if self.shareScsiHotplugSupport is None or not isinstance(self.shareScsiHotplugSupport, bool):
            raise Exception("shareScsiHotplugSupport is invalid")

    def readFromDisk(self, fileName):
        """read object from disk"""

        # fixme: cfg.read(fileName) won't raise exception when file not exist, strange
        if not os.path.exists(fileName):
            raise Exception("config file \"%s\" does not exist"%(fileName))

        cfg = configparser.SafeConfigParser()
        cfg.read(fileName) 

        self.qemuVmType = cfg.get("hardware", "qemuVmType")
        self.cpuArch = cfg.get("hardware", "cpuArch")
        self.cpuNumber = cfg.getint("hardware", "cpuNumber")
        self.memorySize = cfg.getint("hardware", "memorySize")
        self.mainDiskInterface = cfg.get("hardware", "mainDiskInterface")
        self.mainDiskFormat = cfg.get("hardware", "mainDiskFormat")
        self.mainDiskSize = cfg.getint("hardware", "mainDiskSize")
        self.graphicsAdapterInterface = cfg.get("hardware", "graphicsAdapterInterface")
        self.graphicsAdapterPciSlot = cfg.getint("hardware", "graphicsAdapterPciSlot")
        self.soundAdapterInterface = cfg.get("hardware", "soundAdapterInterface")
        self.soundAdapterPciSlot = cfg.getint("hardware", "soundAdapterPciSlot")
        self.networkAdapterInterface = cfg.get("hardware", "networkAdapterInterface")
        self.networkAdapterPciSlot = cfg.getint("hardware", "networkAdapterPciSlot")
        self.balloonDeviceSupport = cfg.getboolean("hardware", "balloonDeviceSupport")
        self.balloonDevicePciSlot = cfg.getint("hardware", "balloonDevicePciSlot")
        self.vdiPortDeviceSupport = cfg.getboolean("hardware", "vdiPortDeviceSupport")
        self.vdiPortDevicePciSlot = cfg.getint("hardware", "vdiPortDevicePciSlot")
        self.shareDirectoryNumber = cfg.getint("hardware", "shareDirectoryNumber")
        self.shareDirectoryHotplugSupport = cfg.getboolean("hardware", "shareDirectoryHotplugSupport")
        self.shareUsbNumber = cfg.getint("hardware", "shareUsbNumber")
        self.shareUsbHotplugSupport = cfg.getboolean("hardware", "shareUsbHotplugSupport")
        self.shareScsiNumber = cfg.getint("hardware", "shareScsiNumber")
        self.shareScsiHotplugSupport = cfg.getboolean("hardware", "shareScsiHotplugSupport")

    def writeToDisk(self, fileName):
        """write object to disk"""

        cfg = configparser.SafeConfigParser()

        cfg.add_section("hardware")
        cfg.set("hardware", "qemuVmType", self.qemuVmType)
        cfg.set("hardware", "cpuArch", self.cpuArch)
        cfg.set("hardware", "cpuNumber", str(self.cpuNumber))
        cfg.set("hardware", "memorySize", str(self.memorySize))
        cfg.set("hardware", "mainDiskInterface", self.mainDiskInterface)
        cfg.set("hardware", "mainDiskFormat", self.mainDiskFormat)
        cfg.set("hardware", "mainDiskSize", str(self.mainDiskSize))
        cfg.set("hardware", "graphicsAdapterInterface", self.graphicsAdapterInterface)
        cfg.set("hardware", "graphicsAdapterPciSlot", str(self.graphicsAdapterPciSlot))
        cfg.set("hardware", "soundAdapterInterface", self.soundAdapterInterface)
        cfg.set("hardware", "soundAdapterPciSlot", str(self.soundAdapterPciSlot))
        cfg.set("hardware", "networkAdapterInterface", self.networkAdapterInterface)
        cfg.set("hardware", "networkAdapterPciSlot", str(self.networkAdapterPciSlot))
        cfg.set("hardware", "balloonDeviceSupport", str(self.balloonDeviceSupport))
        cfg.set("hardware", "balloonDevicePciSlot", str(self.balloonDevicePciSlot))
        cfg.set("hardware", "vdiPortDeviceSupport", str(self.vdiPortDeviceSupport))
        cfg.set("hardware", "vdiPortDevicePciSlot", str(self.vdiPortDevicePciSlot))
        cfg.set("hardware", "shareDirectoryNumber", str(self.shareDirectoryNumber))
        cfg.set("hardware", "shareDirectoryHotplugSupport", str(self.shareDirectoryHotplugSupport))
        cfg.set("hardware", "shareUsbNumber", str(self.shareUsbNumber))
        cfg.set("hardware", "shareUsbHotplugSupport", str(self.shareUsbHotplugSupport))
        cfg.set("hardware", "shareScsiNumber", str(self.shareScsiNumber))
        cfg.set("hardware", "shareScsiHotplugSupport", str(self.shareScsiHotplugSupport))

        cfg.write(open(fileName, "w"))

class FvmConfigWin:

    class OsPluginInfo:
        pluginName = None                                # str
        setupOptList = None                                # list<str>
        cfgOptList = None                                # list<str>

    class AppPluginInfo:
        installOptList = None                            # list<str>
        cfgOptList = None                                # list<str>

    os = OsPluginInfo()
    appDict = collections.OrderedDict()

    def readFromDisk(self, fileName):
        """read object from disk"""

        # fixme: cfg.read(fileName) won't raise exception when file not exist, strange
        if not os.path.exists(fileName):
            raise Exception("config file \"%s\" does not exist"%(fileName))

        # clear self
        self.os.pluginName = None
        self.os.setupOptList = None
        self.os.cfgOptList = None
        self.appDict.clear()

        # do operation
        cfg = configparser.SafeConfigParser()
        cfg.read(fileName) 

        self.os.pluginName = cfg.get("os", "pluginname")
        self.os.setupOptList = []
        for (name, value) in cfg.items("os"):
            if name.startswith("setupopt"):
                self.os.setupOptList.append(value)
        self.os.cfgOptList = []
        for (name, value) in cfg.items("os"):
            if name.startswith("cfgopt"):
                self.os.cfgOptList.append(value)

        for secName in cfg.sections():
            if secName.startswith("app"):
                appPluginName = cfg.get(secName, "pluginname")
                app = FvmConfigWin.AppPluginInfo()
                app.installOptList = []
                for (name, value) in cfg.items(secName):
                    if name.startswith("installopt"):
                        app.installOptList.append(value)
                app.cfgOptList = []
                for (name, value) in cfg.items(secName):
                    if name.startswith("appcfgopt"):
                        app.cfgOptList.append(value)
                self.appDict[appPluginName] = app

    def writeToDisk(self, fileName):
        """write object to disk"""

        # give OsPluginInfo an initial value
        if self.os.pluginName is None:
            self.os.pluginName = ""
            self.os.setupOptList = []
            self.os.cfgOptList = []

        # save config file
        cfg = configparser.SafeConfigParser()

        cfg.add_section("os")
        cfg.set("os", "pluginName", self.os.pluginName)
        i = 0
        for co in self.os.setupOptList:
            cfg.set("os", "setupOpt%d"%(i), co)
            i = i + 1
        i = 0
        for co in self.os.cfgOptList:
            cfg.set("os", "cfgOpt%d"%(i), co)
            i = i + 1

        i = 0
        for appPluginName in self.appDict:
            app = self.appDict[appPluginName]
            secName = "app%d"%(i)
            cfg.add_section(secName)
            cfg.set(secName, "pluginName", appPluginName)
            j = 0
            for co in app.installOptList:
                cfg.set(secName, "installOpt%d"%(j), co)
                j = j + 1
            j = 0
            for co in app.cfgOptList:
                cfg.set(secName, "appCfgOpt%d"%(j), co)
                j = j + 1
            i = i + 1

        cfg.write(open(fileName, "w"))

