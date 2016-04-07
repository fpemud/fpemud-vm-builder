#!/usr/bin/python2
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-


class FvmPlugin:

	def getUsage(self):
		"""Get the plugin usage options"""
		assert False

	def getOsName(self):
		assert False

	def getVmCfgHw(self, param, createOptList):				# fixme: should return hardware spec
		"""Get the hardware specification of this OS.
		   The hw-spec may be affected by the options specified when creating the virtual machine.
		   NOTE: currently it returns FvmConfigHardware directly, we should create a dedicate class for hw-spec."""
		assert False

	def doSetup(self, param, vmInfo, optList):
		"""Get the FvmWork object for doing OS setup. It will be used when creating the virtual machine.
		   Should return a FvmWorkFullControl object.
		   Should leave nothing in <param.tmpDir>."""
		assert False

	def doConfigure(self, param, vmInfo, optList):
		"""Get the FvmWork object list for configuring the virtual machine."""
		assert False

	def mergeCfgOptList(self, param, vmCfgWin, optList):
		"""Returns FvmVmConfigWin object. optList may be an empty list."""
		assert False

	def doExecute(self, param, vmInfo, optList):
		"""Get the FvmWork object list for executing job on the virtual machine."""
		assert False

	def doPauseAutoShowWindow(self, param):
		"""Get the FvmWork object list for pausing auto show window.
		   The general method is to backup and delete all the auto start item, like startup directory and 'Run/RunOnce' registry item."""
		assert False

	def doResumeAutoShowWindow(self, param):
		"""Get the FvmWork object list for resuming auto show window.
		   The general method is to resume all the auto start item, like startup directory and 'Run/RunOnce' registry item."""
		assert False

class FvmWork:

	"""What does this work do"""
	workName = None

class FvmWorkFullControl(FvmWork):
	"""A work with full control on the virtual machine"""

	def doWork(self, param, vmObj, infoPrinter):
		assert False

class FvmWorkOffLineFree(FvmWork):
	"""An off-line work with user defined action.
	   The main-disk is mounted, you can freely operate its content"""

	def operateMainDisk(self, param, mainDiskDir):
		assert False

class FvmWorkOffLineModifyRegistry(FvmWork):
	"""A simple off-line work: modify registry of the guest os"""

	def setWorkName(self, workName):
		self.workName = workName

	def setAddOrModifyInfo(self, key, name, valueType, value):
		self.op = "addOrModify"
		self.key = key
		self.name = name
		self.valueType = valueType
		self.value = value

	def setDeleteInfo(self, key, name):
		self.op = "delete"
		self.key = key
		self.name = name
		self.valueType = None
		self.value = None

class FvmWorkOffLineInjectFile(FvmWork):
	"""A simple off-line work: inject a file into the guest os"""

	def setWorkName(self, workName):
		self.workName = workName

	def setInjectFileInfo(self, filename, dstDir, isBinary):
		"""dstDir is a path relative to mountPoint"""

		self.filename = filename
		self.dstDir = dstDir
		self.isBinary = isBinary

class FvmWorkOffLineInitDesktopBackup(FvmWork):
	"""A simple off-line work: initialize desktop backup"""

	def __init__(self):
		self.desktopBackupObj = None

	def setWorkName(self, workName):
		self.workName = workName

	def setDesktopBackup(self, desktopBackupObj):
		self.desktopBackupObj = desktopBackupObj

class FvmWorkOffLineOperateDesktopBackup(FvmWork):
	"""A simple off-line work: operate desktop backup"""

	def __init__(self):
		self.desktopBackupObj = None
		self.itemStateList = []

	def setWorkName(self, workName):
		self.workName = workName

	def setDesktopBackup(self, desktopBackupObj):
		self.desktopBackupObj = desktopBackupObj

	def setItemState(self, itemName, state):
		elem = (itemName, state)
		self.itemStateList.append(elem)

class FvmWorkOnLineFree(FvmWork):
	"""An on-line work with user defined action.
	   A virtual usb-stick with your own data directory is mounted, you can put any files into it in function fillUsbDataDir.
	   You must specify a *.au3|*.bat|*.exe in data directory in function getExecFile, it will get executed when virtual machine boots up.
	   You can specify requirements, including:
	     network: need network
	     noNetwork: remove virtual network hardware
	     isolatedNetwork: disable network forwarding
	     shutdown: must shutdown the virtual machine after operation
	     rebootAndShutdown: will reboot severial times in operation, must shutdown the virtual machine after operation
	     cdrom=*.iso: must mount a iso file as the cdrom when doing operation"""

	def fillUsbDataDir(self, param, usbDataDir):
		assert False

	def getCmdLine(self):
		"""Returns (execFile, argList)"""
		assert False

	def getReqList(self):
		assert False

class FvmWorkOnLineExec(FvmWork):
	"""A simple on-line work: execute a *.au3|*.bat|*.exe file, can have reqLists"""

	def __init__(self):
		self.execFile = None
		self.argList = []
		self.reqList = []
		self.fileList = []
		self.tmpFileList = []
		self.zipFileList = []

	def setWorkName(self, workName):
		self.workName = workName

	def setExecFileInfo(self, execFile, argList=[]):
		assert isinstance(argList, list)

		self.execFile = execFile
		self.argList = argList

	def setReqList(self, reqList):
		self.reqList = reqList

	def addFile(self, filename, isBinary):
		e = (filename, isBinary)
		self.fileList.append(e)

	def addTmpFile(self, filename, isBinary):
		e = (filename, isBinary)
		self.tmpFileList.append(e)

	def addZipFile(self, filename):
		self.zipFileList.append(filename)

