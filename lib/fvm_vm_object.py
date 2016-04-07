#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import socket
import time
import subprocess
import copy
import dbus
from fvm_util import FvmUtil
from fvm_param import FvmConfigBasic
from fvm_param import FvmConfigHardware
from fvm_param import FvmConfigWin

class FvmVmInfo:

	def __init__(self, vmCfgBasic, vmCfgHw, vmCfgWin):
		self.vmCfgBasic = vmCfgBasic
		self.vmCfgHw = vmCfgHw
		self.vmCfgWin = vmCfgWin

class FvmVmObject:

	def __init__(self, param, vmDir):
		assert os.path.isabs(vmDir)

		self.param = param

		self.vmDir = vmDir
		self.vmCfgBasic = FvmConfigBasic()
		self.vmCfgBasic.readFromDisk(os.path.join(self.vmDir, "element.ini"))
		self.vmCfgHw = FvmConfigHardware()
		self.vmCfgHw.readFromDisk(os.path.join(self.vmDir, "fqemu.hw"))
		self.vmCfgWin = FvmConfigWin()
		self.vmCfgWin.readFromDisk(os.path.join(self.vmDir, "fqemu.win"))

		self.localFakeHarddisk = ""			# the second harddisk. the value is ifType, can be ""|"ide"|"virtio-scsi"|"virtio-blk"
		self.localUsbImgFile = ""
		self.localFloppyImgFile = ""
		self.localCdromImgFile = ""
		self.bootOrder = ["mainDisk"]
		self.networkStatus = ""				# "", "none", "isolate", "virtio-dummy"

		self.spicePort = -1
		self.tapVmId = -1
		self.tapNetId = -1

		self.showUi = False

	def getVmInfo(self):
		ret = FvmVmInfo(self.vmCfgBasic, self.vmCfgHw, self.vmCfgWin)
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
			vmProc = subprocess.Popen(qemuCmd, shell = True)

			# open spice client, will be auto-closed when virtual machines stops
			if self.showUi:
				while not FvmUtil.isSocketPortBusy("tcp", self.spicePort):
					time.sleep(0.2)
				FvmUtil.shell("/usr/bin/spicy -h localhost -p %d >/dev/null 2>&1 &"%(self.spicePort))

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
#		ret = FvmUtil.shell("/usr/bin/qemu-system-x86_64 -device ? 2>&1", "stdout")
#		if "virtio-serial" not in ret:
#			raise Exception("QEMU doesn't support serial device of type virtio!")
#		if "virtio-blk" not in ret:
#			raise Exception("QEMU doesn't support block device of type virtio!")
#		if "virtio-net" not in ret:
#			raise Exception("QEMU doesn't support network card of type virtio!")

	def _generateQemuCommand(self):
		"""pci slot allcation:
			slot ?:			floppy bus
			slot ?:			ide bus
			slot 0x1.0x2:	usb bus
			slot 0x03:		virtio main-disk
			slot 0x10:		virtio extra-harddisk"""

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
		cmd += " -name \"%s\""%(self.vmCfgBasic.title)
		cmd += " -enable-kvm -no-user-config -nodefaults"
		cmd += " -M %s"%(self.vmCfgHw.qemuVmType)

		# platform device
		cmd += " -cpu host"
		cmd += " -smp 1,sockets=1,cores=%d,threads=1"%(self.vmCfgHw.cpuNumber)
		cmd += " -m %d"%(self.vmCfgHw.memorySize)
		cmd += " -rtc base=localtime"

		# main-disk
		if True:
			if self.vmCfgHw.mainDiskFormat == "raw-sparse":
				cmd += " -drive \'file=%s,if=none,id=main-disk,format=%s\'"%(os.path.join(self.vmDir, "disk-main.img"), "raw")
			else:
				cmd += " -drive \'file=%s,if=none,id=main-disk,format=%s\'"%(os.path.join(self.vmDir, "disk-main.img"), "qcow2")
			if self.vmCfgHw.mainDiskInterface == "virtio-blk" and not forSetup:
				cmd += " -device virtio-blk-pci,scsi=off,bus=%s,addr=0x03,drive=main-disk,id=main-disk,%s"%(pciBus, self._bootIndexStr(mainDiskBootIndex))
			elif self.vmCfgHw.mainDiskInterface == "virtio-scsi" and not forSetup:
				cmd += " -device virtio-blk-pci,scsi=off,bus=%s,addr=0x03,drive=main-disk,id=main-disk,%s"%(pciBus, self._bootIndexStr(mainDiskBootIndex))		# fixme
			else:
				cmd += " -device ide-hd,bus=ide.0,unit=0,drive=main-disk,id=main-disk,%s"%(self._bootIndexStr(mainDiskBootIndex))

		# extra disk
		if self.localFakeHarddisk != "":
			cmd += " -drive \'file=%s,if=none,id=fake-harddisk,readonly=on,format=raw\'"%(os.path.join(self.vmDir, "fake-hdd.img"))
			if self.localFakeHarddisk == "virtio-blk":
				cmd += " -device virtio-blk-pci,scsi=off,bus=%s,addr=0x10,drive=fake-harddisk,id=fake-harddisk"%(pciBus)
			elif self.localFakeHarddisk == "virtio-scsi":
				cmd += " -device virtio-blk-pci,scsi=off,bus=%s,addr=0x10,drive=fake-harddisk,id=fake-harddisk"%(pciBus)			# fixme
			else:
				cmd += " -device ide-hd,bus=ide.0,unit=0,drive=fake-harddisk,id=fake-harddisk"

		# extra disk
		if self.localFloppyImgFile != "":
			cmd += " -drive \'file=%s,if=none,id=extra-floopy,format=raw\'"%(self.localFloppyImgFile)
			cmd += " -global isa-fdc.driveA=extra-floopy"

		# extra disk
		if self.localUsbImgFile != "":
			cmd += " -drive \'file=%s,if=none,id=extra-usb-disk,format=raw\'"%(self.localUsbImgFile)
			cmd += " -device usb-storage,drive=extra-usb-disk,id=extra-usb-disk"

		# extra disk
		if self.localCdromImgFile != "":
			cmd += " -drive \'file=%s,if=none,id=extra-cdrom,readonly=on,format=raw\'"%(self.localCdromImgFile)
			cmd += " -device ide-cd,bus=ide.1,unit=0,drive=extra-cdrom,id=extra-cdrom,%s"%(self._bootIndexStr(cdromBootIndex))

		# graphics device
		if self.vmCfgHw.graphicsAdapterInterface == "qxl" and not forSetup:
			cmd += " -spice port=%d,addr=127.0.0.1,disable-ticketing,agent-mouse=off"%(self.spicePort)
			cmd += " -vga qxl -global qxl-vga.ram_size_mb=64 -global qxl-vga.vram_size_mb=64"
#			cmd += " -device qxl-vga,bus=%s,addr=0x04,ram_size_mb=64,vram_size_mb=64"%(pciBus)						# see https://bugzilla.redhat.com/show_bug.cgi?id=915352
		else:
			cmd += " -spice port=%d,addr=127.0.0.1,disable-ticketing,agent-mouse=off"%(self.spicePort)
			cmd += " -device VGA,bus=%s,addr=0x04"%(pciBus)

		# sound device
		if self.vmCfgHw.soundAdapterInterface == "ac97" and not forSetup:
			cmd += " -device AC97,id=sound0,bus=%s,addr=0x%x"%(pciBus, self.vmCfgHw.soundAdapterPciSlot)

		# network device
		if not forSetup and self.networkStatus != "none":
			if self.networkStatus == "virtio-dummy":
				assert self.vmCfgHw.networkAdapterInterface == "virtio"
				cmd += " -netdev tap,id=eth0,ifname=%s,script=no,downscript=no"%(self._getVirtioDummyTapInterface())
				cmd += " -device virtio-net-pci,netdev=eth0,mac=%s,bus=%s,addr=0x%x,romfile="%(self._getVirtioDummyTapVmMacAddress(), pciBus, self.vmCfgHw.networkAdapterPciSlot)
			elif self.vmCfgHw.networkAdapterInterface != "":
				if self.networkStatus == "isolate":
					restrictStr = "yes"
				else:
					restrictStr = "no"
				cmd += " -netdev user,id=eth0,restrict=%s"%(restrictStr)
				cmd += " -device rtl8139,netdev=eth0,id=eth0,bus=%s,addr=0x%x,romfile="%(pciBus, self.vmCfgHw.networkAdapterPciSlot)

		# balloon device
		if self.vmCfgHw.balloonDeviceSupport and not forSetup:
			cmd += " -device virtio-balloon-pci,id=balloon0,bus=%s,addr=0x%x"%(pciBus, self.vmCfgHw.balloonDevicePciSlot)

		# vdi-port
		if self.vmCfgHw.vdiPortDeviceSupport and not forSetup:
			cmd += " -device virtio-serial-pci,id=vdi-port,bus=%s,addr=0x%x"%(pciBus, self.vmCfgHw.vdiPortDevicePciSlot)

			# usb redirection
			for i in range(0,self.vmCfgHw.shareUsbNumber):
				cmd += " -chardev spicevmc,name=usbredir,id=usbredir%d"%(i)
				cmd += " -device usb-redir,chardev=usbredir%d,id=usbredir%d"%(i,i)

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
		netObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService/%d/Networks/%d'%(self.param.uid, self.tapNetId))
		self.tapVmId = netObj.AddVm(self.vmDir, dbus_interface='org.fpemud.VirtService.Network')

	def _freeVirtioDummyNetwork(self):
		assert self.tapNetId != -1 and self.tapVmId != -1

		# delete vm and network
		dbusObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService')
		netObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService/%d/Networks/%d'%(self.param.uid, self.tapNetId))
		netObj.DeleteVm(self.tapVmId, dbus_interface='org.fpemud.VirtService.Network')
		dbusObj.DeleteNetwork(self.tapNetId, dbus_interface='org.fpemud.VirtService')

		# reset variable
		self.tapNetId = -1
		self.tapVmId = -1

	def _getVirtioDummyTapInterface(self):
		assert self.tapNetId != -1 and self.tapVmId != -1

		vmObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService/%d/Networks/%d/NetVirtMachines/%d'%(self.param.uid, self.tapNetId, self.tapVmId))
		return vmObj.GetTapInterface(dbus_interface='org.fpemud.VirtService.NetVirtMachine')

	def _getVirtioDummyTapVmMacAddress(self):
		assert self.tapNetId != -1 and self.tapVmId != -1

		vmObj = dbus.SystemBus().get_object('org.fpemud.VirtService', '/org/fpemud/VirtService/%d/Networks/%dNetVirtMachines/%d'%(self.param.uid, self.tapNetId, self.tapVmId))
		return vmObj.GetTapVmMacAddress(dbus_interface='org.fpemud.VirtService.NetVirtMachine')

	def _bootIndexStr(self, bootIndex):
		if bootIndex == -1:
			return ""
		else:
			return "bootindex=%d"%(bootIndex)

