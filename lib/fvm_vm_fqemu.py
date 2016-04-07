#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import time
import subprocess
import copy
import dbus
import shutil
import configparser
import collections
from fvm_util import FvmUtil

"""
Virt-machine directory structure:
    [vmname]
    |--element.ini                            element file
    |--fqemu.hw                               config file
    |--fqemu.win                              config file
    |--disk-main.img                          system disk image
"""


class FvmVmFqemuBuilder:

    def __init__(self, param):
        self.param = param

    def createVm(self, vmDir, vmCfgBasic, vmCfgHw):
        assert os.path.isabs(vmDir)
        assert not os.path.exists(vmDir)

        try:
            os.mkdir(vmDir)

            FvmUtil.createFile(os.path.join(vmDir, "disk-main.img"), vmCfgHw.mainDiskSize * 1024 * 1024)

            vmCfgBasic.writeToDisk(os.path.join(vmDir, "element.ini"))

            vmCfgHw.writeToDisk(os.path.join(vmDir, "fqemu.hw"))

            vmCfgWin = FvmVmFqemuConfigWin()
            vmCfgWin.writeToDisk(os.path.join(vmDir, "fqemu.win"))

            FvmUtil.touchFile(os.path.join(vmDir, "setup.mode"))
        except:
            if os.path.exists(vmDir):
                shutil.rmtree(vmDir)
            raise


class FvmVmFqemuInfo:

    def __init__(self, vmCfgBasic, vmCfgHw, vmCfgWin):
        self.vmCfgBasic = vmCfgBasic
        self.vmCfgHw = vmCfgHw
        self.vmCfgWin = vmCfgWin


class FvmVmFqemuObject:

    def __init__(self, param, vmDir):
        assert os.path.isabs(vmDir)

        self.param = param

        self.vmDir = vmDir
        self.vmCfgBasic = FvmVmFqemuConfigBasic()
        self.vmCfgBasic.readFromDisk(os.path.join(self.vmDir, "element.ini"))
        self.vmCfgHw = FvmVmFqemuConfigHardware()
        self.vmCfgHw.readFromDisk(os.path.join(self.vmDir, "fqemu.hw"))
        self.vmCfgWin = FvmVmFqemuConfigWin()
        self.vmCfgWin.readFromDisk(os.path.join(self.vmDir, "fqemu.win"))

        self.localFakeHarddisk = ""            # the second harddisk. the value is ifType, can be ""|"ide"|"virtio-scsi"|"virtio-blk"
        self.localUsbImgFile = ""
        self.localFloppyImgFile = ""
        self.localCdromImgFile = ""
        self.bootOrder = ["mainDisk"]
        self.networkStatus = ""                # "", "none", "isolate", "virtio-dummy"

        self.spicePort = -1
        self.tapVmId = -1
        self.tapNetId = -1

        self.showUi = False

    def getVmInfo(self):
        ret = FvmVmFqemuInfo(self.vmCfgBasic, self.vmCfgHw, self.vmCfgWin)
        return copy.deepcopy(ret)

    def setVmCfgWin(self, vmCfgWin):
        assert self.isLocked()
        self.vmCfgWin = copy.deepcopy(vmCfgWin)
        self.vmCfgWin.writeToDisk(os.path.join(self.vmDir, "fqemu.win"))

    def lock(self):
        assert not self.isLocked()
        FvmUtil.touchFile(os.path.join(self.vmDir, "lock"))

    def unlock(self):
        FvmUtil.forceDelete(os.path.join(self.vmDir, "lock"))

    def isLocked(self):
        lockFn = os.path.join(self.vmDir, "lock")
        return os.path.exists(lockFn)

    def getMainDiskImage(self):
        assert self.isLocked()
        return os.path.join(self.vmDir, "disk-main.img")

    def setSetupMode(self, setupMode):
        assert self.isLocked()
        assert setupMode is False
        if os.path.exists(os.path.join(self.vmDir, "setup.mode")):
            os.remove(os.path.join(self.vmDir, "setup.mode"))

    def getSetupMode(self):
        return os.path.exists(os.path.join(self.vmDir, "setup.mode"))

    def setLocalFakeHarddisk(self, ifType):
        assert self.isLocked()
        assert ifType in ["", "ide", "virtio-scsi", "virtio-blk"]
        self.localFakeHarddisk = ifType

    def setLocalFloppyImage(self, imgFile):
        assert self.isLocked()
        assert imgFile == "" or os.path.isabs(imgFile)
        self.localFloppyImgFile = imgFile

    def setLocalUsbImage(self, imgFile):
        assert self.isLocked()
        assert imgFile == "" or os.path.isabs(imgFile)
        self.localUsbImgFile = imgFile

    def setLocalCdromImage(self, imgFile):
        assert self.isLocked()
        assert imgFile == "" or os.path.isabs(imgFile)
        self.localCdromImgFile = imgFile

    def setBootOrder(self, bootOrder):
        assert self.isLocked()

        if bootOrder is None:
            self.bootOrder = ["mainDisk"]
        else:
            assert isinstance(bootOrder, list)
            self.bootOrder = bootOrder

    def setNetworkStatus(self, networkStatus):
        assert self.isLocked()
        self.networkStatus = networkStatus

    def setShowUi(self, showUi):
        assert self.isLocked()
        self.showUi = showUi

    def run(self):
        assert self.isLocked()

        self._checkQemuCapability()

        mycwd = os.getcwd()
        vmProc = None
        try:
            os.chdir(self.vmDir)
            self._allocSpicePort()
            if self.networkStatus == "virtio-dummy":
                self._allocVirtioDummyNetwork()

            # generate xml file
            qemuCmd = self._generateQemuCommand()
            qemuCmd += " >fqemu.log 2>&1"

            # generate a 100M fake harddisk image file
            if self.localFakeHarddisk != "":
                FvmUtil.createFile("fake-hdd.img", 100)

            # run virtual machine
            vmProc = subprocess.Popen(qemuCmd, shell=True)

            # open spice client, will be auto-closed when virtual machines stops
            if self.showUi:
                while not FvmUtil.isSocketPortBusy("tcp", self.spicePort):
                    time.sleep(0.2)
                FvmUtil.shell("/usr/bin/spicy -h localhost -p %d >/dev/null 2>&1 &" % (self.spicePort))

            # wait the virtual machine to stop
            vmProc.wait()

            if vmProc.returncode != 0:
                vmProc = None
                raise Exception("failed to execute fqemu")

            vmProc = None
            if os.path.exists("fqemu.log"):
                os.remove("fqemu.log")
        except:
            if vmProc is not None:
                vmProc.kill()
                vmProc = None
            raise
        finally:
            if self.localFakeHarddisk != "":
                os.remove("fake-hdd.img")
            if self.networkStatus == "virtio-dummy":
                self._freeVirtioDummyNetwork()
            self._freeSpicePort()
            os.chdir(mycwd)

    def _checkQemuCapability(self):
        pass
#        ret = FvmUtil.shell("/usr/bin/qemu-system-x86_64 -device ? 2>&1", "stdout")
#        if "virtio-serial" not in ret:
#            raise Exception("QEMU doesn't support serial device of type virtio!")
#        if "virtio-blk" not in ret:
#            raise Exception("QEMU doesn't support block device of type virtio!")
#        if "virtio-net" not in ret:
#            raise Exception("QEMU doesn't support network card of type virtio!")

    def _generateQemuCommand(self):
        """pci slot allcation:
            slot ?:            floppy bus
            slot ?:            ide bus
            slot 0x1.0x2:    usb bus
            slot 0x03:        virtio main-disk
            slot 0x10:        virtio extra-harddisk"""

        forSetup = os.path.exists(os.path.join(self.vmDir, "setup.mode"))
        if self.vmCfgHw.qemuVmType == "pc":
            pciBus = "pci.0"
        else:
            pciBus = "pcie.0"

        mainDiskBootIndex = -1
        cdromBootIndex = -1
        if True:
            bi = 1
            for bo in self.bootOrder:
                if bo == "mainDisk":
                    mainDiskBootIndex = bi
                    bi = bi + 1
                if bo == "cdrom":
                    cdromBootIndex = bi
                    bi = bi + 1

        cmd = "/usr/bin/qemu-system-x86_64"
        cmd += " -name \"%s\"" % (self.vmCfgBasic.title)
        cmd += " -enable-kvm -no-user-config -nodefaults"
        cmd += " -M %s" % (self.vmCfgHw.qemuVmType)

        # platform device
        cmd += " -cpu host"
        cmd += " -smp 1,sockets=1,cores=%d,threads=1" % (self.vmCfgHw.cpuNumber)
        cmd += " -m %d" % (self.vmCfgHw.memorySize)
        cmd += " -rtc base=localtime"

        # main-disk
        if True:
            if self.vmCfgHw.mainDiskFormat == "raw-sparse":
                cmd += " -drive \'file=%s,if=none,id=main-disk,format=%s\'" % (os.path.join(self.vmDir, "disk-main.img"), "raw")
            else:
                cmd += " -drive \'file=%s,if=none,id=main-disk,format=%s\'" % (os.path.join(self.vmDir, "disk-main.img"), "qcow2")
            if self.vmCfgHw.mainDiskInterface == "virtio-blk" and not forSetup:
                cmd += " -device virtio-blk-pci,scsi=off,bus=%s,addr=0x03,drive=main-disk,id=main-disk,%s" % (pciBus, self._bootIndexStr(mainDiskBootIndex))
            elif self.vmCfgHw.mainDiskInterface == "virtio-scsi" and not forSetup:
                cmd += " -device virtio-blk-pci,scsi=off,bus=%s,addr=0x03,drive=main-disk,id=main-disk,%s" % (pciBus, self._bootIndexStr(mainDiskBootIndex))        # fixme
            else:
                cmd += " -device ide-hd,bus=ide.0,unit=0,drive=main-disk,id=main-disk,%s" % (self._bootIndexStr(mainDiskBootIndex))

        # extra disk
        if self.localFakeHarddisk != "":
            cmd += " -drive \'file=%s,if=none,id=fake-harddisk,readonly=on,format=raw\'" % (os.path.join(self.vmDir, "fake-hdd.img"))
            if self.localFakeHarddisk == "virtio-blk":
                cmd += " -device virtio-blk-pci,scsi=off,bus=%s,addr=0x10,drive=fake-harddisk,id=fake-harddisk" % (pciBus)
            elif self.localFakeHarddisk == "virtio-scsi":
                cmd += " -device virtio-blk-pci,scsi=off,bus=%s,addr=0x10,drive=fake-harddisk,id=fake-harddisk" % (pciBus)            # fixme
            else:
                cmd += " -device ide-hd,bus=ide.0,unit=0,drive=fake-harddisk,id=fake-harddisk"

        # extra disk
        if self.localFloppyImgFile != "":
            cmd += " -drive \'file=%s,if=none,id=extra-floopy,format=raw\'" % (self.localFloppyImgFile)
            cmd += " -global isa-fdc.driveA=extra-floopy"

        # extra disk
        if self.localUsbImgFile != "":
            cmd += " -drive \'file=%s,if=none,id=extra-usb-disk,format=raw\'" % (self.localUsbImgFile)
            cmd += " -device usb-storage,drive=extra-usb-disk,id=extra-usb-disk"

        # extra disk
        if self.localCdromImgFile != "":
            cmd += " -drive \'file=%s,if=none,id=extra-cdrom,readonly=on,format=raw\'" % (self.localCdromImgFile)
            cmd += " -device ide-cd,bus=ide.1,unit=0,drive=extra-cdrom,id=extra-cdrom,%s" % (self._bootIndexStr(cdromBootIndex))

        # graphics device
        if self.vmCfgHw.graphicsAdapterInterface == "qxl" and not forSetup:
            cmd += " -spice port=%d,addr=127.0.0.1,disable-ticketing,agent-mouse=off" % (self.spicePort)
            cmd += " -vga qxl -global qxl-vga.ram_size_mb=64 -global qxl-vga.vram_size_mb=64"
#            cmd += " -device qxl-vga,bus=%s,addr=0x04,ram_size_mb=64,vram_size_mb=64"%(pciBus)                        # see https://bugzilla.redhat.com/show_bug.cgi?id=915352
        else:
            cmd += " -spice port=%d,addr=127.0.0.1,disable-ticketing,agent-mouse=off" % (self.spicePort)
            cmd += " -device VGA,bus=%s,addr=0x04" % (pciBus)

        # sound device
        if self.vmCfgHw.soundAdapterInterface == "ac97" and not forSetup:
            cmd += " -device AC97,id=sound0,bus=%s,addr=0x%x" % (pciBus, self.vmCfgHw.soundAdapterPciSlot)

        # network device
        if not forSetup and self.networkStatus != "none":
            if self.networkStatus == "virtio-dummy":
                assert self.vmCfgHw.networkAdapterInterface == "virtio"
                cmd += " -netdev tap,id=eth0,ifname=%s,script=no,downscript=no" % (self._getVirtioDummyTapInterface())
                cmd += " -device virtio-net-pci,netdev=eth0,mac=%s,bus=%s,addr=0x%x,romfile=" % (self._getVirtioDummyTapVmMacAddress(), pciBus, self.vmCfgHw.networkAdapterPciSlot)
            elif self.vmCfgHw.networkAdapterInterface != "":
                if self.networkStatus == "isolate":
                    restrictStr = "yes"
                else:
                    restrictStr = "no"
                cmd += " -netdev user,id=eth0,restrict=%s" % (restrictStr)
                cmd += " -device rtl8139,netdev=eth0,id=eth0,bus=%s,addr=0x%x,romfile=" % (pciBus, self.vmCfgHw.networkAdapterPciSlot)

        # balloon device
        if self.vmCfgHw.balloonDeviceSupport and not forSetup:
            cmd += " -device virtio-balloon-pci,id=balloon0,bus=%s,addr=0x%x" % (pciBus, self.vmCfgHw.balloonDevicePciSlot)

        # vdi-port
        if self.vmCfgHw.vdiPortDeviceSupport and not forSetup:
            cmd += " -device virtio-serial-pci,id=vdi-port,bus=%s,addr=0x%x" % (pciBus, self.vmCfgHw.vdiPortDevicePciSlot)

            # usb redirection
            for i in range(0, self.vmCfgHw.shareUsbNumber):
                cmd += " -chardev spicevmc,name=usbredir,id=usbredir%d" % (i)
                cmd += " -device usb-redir,chardev=usbredir%d,id=usbredir%d" % (i, i)

            # vdagent
            cmd += " -chardev spicevmc,id=vdagent,debug=0,name=vdagent"
            cmd += " -device virtserialport,chardev=vdagent,name=com.redhat.spice.0"

        # input device
        if True:
            cmd += " -usbdevice tablet"

        return cmd

    def _allocSpicePort(self):
        assert self.spicePort == -1
        self.spicePort = FvmUtil.getFreeSocketPort("tcp", self.param.spicePortStart, self.param.spicePortEnd)

    def _freeSpicePort(self):
        assert self.spicePort != -1
        self.spicePort = -1

    def _allocVirtioDummyNetwork(self):
        assert self.tapNetId == -1 and self.tapVmId == -1

        # create network and add vm
        dbusObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService')
        self.tapNetId = dbusObj.NewNetwork("isolate", dbus_interface='org.fpemud.VirtService')
        netObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService/%d/Networks/%d' % (self.param.uid, self.tapNetId))
        self.tapVmId = netObj.AddVm(self.vmDir, dbus_interface='org.fpemud.VirtService.Network')

    def _freeVirtioDummyNetwork(self):
        assert self.tapNetId != -1 and self.tapVmId != -1

        # delete vm and network
        dbusObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService')
        netObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService/%d/Networks/%d' % (self.param.uid, self.tapNetId))
        netObj.DeleteVm(self.tapVmId, dbus_interface='org.fpemud.VirtService.Network')
        dbusObj.DeleteNetwork(self.tapNetId, dbus_interface='org.fpemud.VirtService')

        # reset variable
        self.tapNetId = -1
        self.tapVmId = -1

    def _getVirtioDummyTapInterface(self):
        assert self.tapNetId != -1 and self.tapVmId != -1

        vmObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService/%d/Networks/%d/NetVirtMachines/%d' % (self.param.uid, self.tapNetId, self.tapVmId))
        return vmObj.GetTapInterface(dbus_interface='org.fpemud.VirtService.NetVirtMachine')

    def _getVirtioDummyTapVmMacAddress(self):
        assert self.tapNetId != -1 and self.tapVmId != -1

        vmObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService/%d/Networks/%dNetVirtMachines/%d' % (self.param.uid, self.tapNetId, self.tapVmId))
        return vmObj.GetTapVmMacAddress(dbus_interface='org.fpemud.VirtService.NetVirtMachine')

    def _bootIndexStr(self, bootIndex):
        if bootIndex == -1:
            return ""
        else:
            return "bootindex=%d" % (bootIndex)


class FvmVmFqemuConfigBasic:

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
            raise Exception("config file \"%s\" does not exist" % (fileName))

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


class FvmVmFqemuConfigHardware:

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

        validQemuVmType = ["pc", "q35"]
        validArch = ["x86", "amd64"]
        validDiskInterface = ["virtio-blk", "ide"]
        validDiskFormat = ["raw-sparse", "qcow2"]
        validGraphicsAdapterInterface = ["qxl", "vga"]
        validSoundAdapterInterface = ["ac97", ""]
        validNetworkAdapterInterface = ["virtio", "user", ""]

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
            raise Exception("config file \"%s\" does not exist" % (fileName))

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


class FvmVmFqemuConfigWin:

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
            raise Exception("config file \"%s\" does not exist" % (fileName))

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
                app = FvmVmFqemuConfigWin.AppPluginInfo()
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
            cfg.set("os", "setupOpt%d" % (i), co)
            i = i + 1
        i = 0
        for co in self.os.cfgOptList:
            cfg.set("os", "cfgOpt%d" % (i), co)
            i = i + 1

        i = 0
        for appPluginName in self.appDict:
            app = self.appDict[appPluginName]
            secName = "app%d" % (i)
            cfg.add_section(secName)
            cfg.set(secName, "pluginName", appPluginName)
            j = 0
            for co in app.installOptList:
                cfg.set(secName, "installOpt%d" % (j), co)
                j = j + 1
            j = 0
            for co in app.cfgOptList:
                cfg.set(secName, "appCfgOpt%d" % (j), co)
                j = j + 1
            i = i + 1

        cfg.write(open(fileName, "w"))
