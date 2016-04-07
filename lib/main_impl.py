#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import shutil
from fvm_util import FvmUtil
from fvm_util import InfoPrinter
from fvm_util import CfgOptUtil
from fvm_param import FvmConfigBasic
from fvm_param import FvmConfigWin
from fvm_plugin import FvmPluginOs
from fvm_plugin import FvmWorkFullControl
from fvm_plugin import FvmWorkOffLineInitDesktopBackup
from fvm_plugin import FvmWorkOffLineOperateDesktopBackup
from fvm_worklist_executor import FvmWorkListExecutor
from fvm_vm_builder import FvmVmBuilder
from fvm_vm_object import FvmVmObject

class MainImpl:

    def __init__(self, param, args):
		self.param = param
		self.args = args
		self.pluginList = self._getPluginList()
		self.infoPrinter = InfoPrinter()

	def main(self):
		if self.args.path == "":
			if self.args.os == "?":
				self.showOsList()
			elif self.args.type == "?":
				self.showTypeList()
			else:
				self.usage()
			return 1

		self.doCreate()
		return 0

	def showOsList(self):
		for pObj in self.pluginList:
			for osName in pObj.getOsNames():
				print(osName)
		
	def showTypeList(self):
		print("fqemu")

	def doCreate(self):
		"""create new virtual machine and do an unattended os setup"""

		self.args.vmdir = os.path.abspath(self.args.path)
		if os.path.exists(self.args.vmdir):
			raise Exception("target virtual machine directory already exists")

		pObj = self.getPluginByOsName(self.pluginList, self.args.os)
		if pObj is None:
			raise Exception("the specified operating system is not supported")

		try:
			# create virt-machine
			self.infoPrinter.printInfo("Creating virtual machine in directory \"%s\"..."%(self.args.vmdir))
			self.infoPrinter.incIndent()

			vmCfgBasic = self._getVmCfgBasicByArgs(self.args)
			vmCfgHw = pObj.getVmCfgHw(self.param, self.args.popt)				# fixme: should return hardware spec
			vmCfgBasic.checkValid()
			vmCfgHw.checkValid()
			self._printVmInfo(self.infoPrinter, vmCfgBasic, vmCfgHw)

			vb = FvmVmFqemuBuilder(self.param)
			vb.createVm(self.args.vmdir, vmCfgBasic, vmCfgHw)

			self.infoPrinter.decIndent()
			self.infoPrinter.printInfo("Complete!")

			# open vmObj and run os setup
			self.infoPrinter.printInfo("Doing \"%s\" setup..."%(pObj.getOsName()))
			self.infoPrinter.incIndent()

			vmObj = FvmVmObject(self.param, self.args.vmdir)
			self.param.tmpDir = os.path.join(self.args.vmdir, "temp")
			try:
				vmObj.lock()
				vmObj.setShowUi(self.args.showui)

				FvmUtil.mkDirAndClear(self.param.tmpDir)

				# execute os setup work
				workList = pObj.doSetup(self.param, vmObj.getVmInfo(), self.args.popt)
				for w in workList:
					assert isinstance(w, FvmWorkFullControl)
				wlExec = FvmWorkListExecutor(self.param, vmObj, self.infoPrinter)
				wlExec.executeWorkList(workList)
				assert not vmObj.getSetupMode()
				self._changeVmCfgWinForOsSetup(vmObj, self.args.plugin, self.args.popt)

				# execute initial configure work
				workList = pObj.doInitialConfigure(self.param, vmObj.getVmInfo())
				wlExec = FvmWorkListExecutor(self.param, vmObj, self.infoPrinter)
				wlExec.executeWorkList(workList)
			finally:
				if not self.args.keep:
					FvmUtil.forceDelete(self.param.tmpDir)
					self.param.tmpDir = ""
				vmObj.unlock()

			self.infoPrinter.decIndent()
			self.infoPrinter.printInfo("Complete!")
		except:
			if not self.args.keep:
				if os.path.exists(self.args.vmdir):
					FvmUtil.forceDelete(self.args.vmdir)
			raise

	def _getPluginList(self):
		ret = []
		for fn in os.listdir(self.param.libDir):
			if fn.startswith("plugin-"):
				pluginName = fn[len("plugin-"):]
				pDir = os.path.join(self.param.libDir, fn)
				pDataDir = os.path.join(pDir, "data")
		
				tmp = sys.path
				try:
					sys.path.append(pDir)
					exec "import plugin_%s" % (pluginName)
					exec "obj = plugin_%s.PluginObject(\"%s\")" % (pluginName, pDataDir)
					ret.append(obj)
				finally:
					sys.path = tmp
		return ret

	def _getPluginByOsName(self, pluginList, osName):
		for pObj in pluginList:
			if osName in pObj.getOsNames():
				return pObj
		return None
		
	def _getVmCfgBasicByArgs(self, args):
		ret = FvmConfigBasic()
		ret.name = os.path.basename(args.vmdir)
		ret.title = os.path.basename(args.title)
		ret.description = args.description
		return ret

	def _printVmInfo(self, infoPrinter, vmCfgBasic, vmCfgHw):
		infoPrinter.printInfo(">> Virtual machine configuration:")

		infoPrinter.printInfo("     name: %s"%(vmCfgBasic.name))
		infoPrinter.printInfo("     title: %s"%(vmCfgBasic.title))

		if not "\n" in vmCfgBasic.description:
			infoPrinter.printInfo("     description: %s"%(vmCfgBasic.description))
		else:
			infoPrinter.printInfo("     description:")
			for line in vmCfgBasic.description.split("\n"):
				infoPrinter.printInfo("       %s"%(line))

		infoPrinter.printInfo("     cpuArch: %s"%(vmCfgHw.cpuArch))
		infoPrinter.printInfo("     cpuNumber: %d"%(vmCfgHw.cpuNumber))
		infoPrinter.printInfo("     memorySize: %d MB"%(vmCfgHw.memorySize))
		infoPrinter.printInfo("     mainDiskSize: %d MB"%(vmCfgHw.mainDiskSize))
		infoPrinter.printInfo("     mainDiskInterface: %s"%(vmCfgHw.mainDiskInterface))
		infoPrinter.printInfo("     networkAdapterInterface: %s"%(vmCfgHw.networkAdapterInterface))
		infoPrinter.printInfo("")

	def _getAppCfgWorkList(self, vmObj, pluginObj, pluginName, optList):
		workList = []

		tmpOptList = []
		for opt in optList:
			if not opt.startswith("desktop-option="):
				tmpOptList.append(opt)
				continue

			if len(tmpOptList) > 0:
				workList += pluginObj.doConfigure(self.param, vmObj.getVmInfo(), tmpOptList)
				tmpOptList = []

			if opt.startswith("desktop-option="):
				work = self._getCfgWorkDesktopOption(vmObj.getVmInfo(), pluginObj, pluginName, opt)
				workList.append(work)

		if len(tmpOptList) > 0:
			workList += pluginObj.doConfigure(self.param, vmObj.getVmInfo(), tmpOptList)
			tmpOptList = []

		return workList

	def _getCfgWorkDesktopOption(self, vmInfo, pluginObj, pluginName, opt):
		installOptList = vmInfo.vmCfgWin.appDict[pluginName].installOptList
		desktopBackup = pluginObj.getDesktopItemBackup(self.param, vmInfo, installOptList)
		if desktopBackup is None:
			raise Exception("invalid option \"%s\""%(opt))

		work = FvmWorkOffLineOperateDesktopBackup()
		work.setWorkName("Configure desktop option")
		work.setDesktopBackup(desktopBackup)
		for v in opt[15:].split(";"):
			t = v.split(":")
			if len(t) != 2 or t[0] not in desktopBackup.getItemNameList() or (t[1] != "on" and t[1] != "off"):
				raise Exception("invalid desktop item option\"%s\""%(v))
			if t[1] == "on":
				work.setItemState(t[0], True)
			else:
				work.setItemState(t[0], False)
		return work

	def _changeVmCfgWinForOsSetup(self, vmObj, pluginName, optList):
		vmCfgWin = vmObj.getVmInfo().vmCfgWin
		vmCfgWin.os.pluginName = pluginName
		vmCfgWin.os.setupOptList = optList
		vmObj.setVmCfgWin(vmCfgWin)

	def _changeVmCfgWinForOsConfigure(self, vmObj, pluginObj, optList):
		vmCfgWin = vmObj.getVmInfo().vmCfgWin
		vmCfgWin.os.cfgOptList = pluginObj.mergeCfgOptList(self.param, vmCfgWin, optList)
		vmObj.setVmCfgWin(vmCfgWin)

	def _changeVmCfgWinForAppInstall(self, vmObj, pluginName, optList):
		vmCfgWin = vmObj.getVmInfo().vmCfgWin
		app = FvmConfigWin.AppPluginInfo()
		app.installOptList = optList
		app.cfgOptList = []
		vmCfgWin.appDict[pluginName] = app
		vmObj.setVmCfgWin(vmCfgWin)

	def _changeVmCfgWinForAppUninstall(self, vmObj, pluginName):
		vmCfgWin = vmObj.getVmInfo().vmCfgWin
		vmCfgWin.appDict.remove(pluginName)
		vmObj.setVmCfgWin(vmCfgWin)

	def _changeVmCfgWinForAppConfigure(self, vmObj, pluginObj, pluginName, optList):
		tmpOptList = []
		for opt in optList:
			if not opt.startswith("desktop-option="):
				tmpOptList.append(opt)
				continue

			if len(tmpOptList) > 0:
				vmCfgWin = vmObj.getVmInfo().vmCfgWin
				vmCfgWin.appDict[pluginName].cfgOptList = pluginObj.mergeCfgOptList(self.param, vmCfgWin, tmpOptList)
				vmObj.setVmCfgWin(vmCfgWin)
				tmpOptList = []

			if opt.startswith("desktop-option="):
				vmCfgWin = vmObj.getVmInfo().vmCfgWin
				ret = vmCfgWin.appDict[pluginName].cfgOptList
				ret = CfgOptUtil.mergeCfgOptWithSubKeyValue(ret, [opt], "desktop-option=")
				vmCfgWin.appDict[pluginName].cfgOptList = ret
				vmObj.setVmCfgWin(vmCfgWin)

		if len(tmpOptList) > 0:
			vmCfgWin = vmObj.getVmInfo().vmCfgWin
			vmCfgWin.appDict[pluginName].cfgOptList = pluginObj.mergeCfgOptList(self.param, vmCfgWin, tmpOptList)
			vmObj.setVmCfgWin(vmCfgWin)
			tmpOptList = []

