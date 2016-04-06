#!/usr/bin/python2
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import shutil
from fvm_util import FvmUtil
from fvm_util import InfoPrinter
from fvm_util import CfgOptUtil
from fvm_param import FvmConfigBasic
from fvm_param import FvmConfigWin
from fvm_plugin import FvmPluginOs
from fvm_plugin import FvmPluginApp
from fvm_plugin import FvmWorkFullControl
from fvm_plugin import FvmWorkOffLineInitDesktopBackup
from fvm_plugin import FvmWorkOffLineOperateDesktopBackup
from fvm_plugin_manager import FvmPluginManager
from fvm_worklist_executor import FvmWorkListExecutor
from fvm_vm_builder import FvmVmBuilder
from fvm_vm_object import FvmVmObject

class MainImpl:

    def __init__(self, param, args):
		self.param = param
		self.args = args
		self.pluginManager = FvmPluginManager(self.param)
		self.infoPrinter = InfoPrinter()

	def main(self):
		if self.args.op == "list":
			self.doList()
			return 0

		if self.args.op == "create":
			self.doCreate()
			return 0

		if self.args.op == "install":
			self.doInstall()
			return 0

		if self.args.op == "uninstall":
			self.doUninstall()
			return 0

		if self.args.op == "configure":
			pObj = self.pluginManager.getPluginObj(self.args.plugin)
			if pObj is None:
				raise Exception("failed to load os-plugin %s or app-plugin %s."%(self.args.plugin, self.args.plugin))

			if isinstance(pObj, FvmPluginOs):
				self.doOsConfigure(pObj)
			elif isinstance(pObj, FvmPluginApp):
				self.doAppConfigure(pObj)
			else:
				assert False

			return 0

		if self.args.op == "execute":
			self.doExecute()
			return 0

		if self.args.op == "modify":
			self.doModify()
			return 0

		if self.args.op == "recreate":
			self.doReCreate()
			return 0

		return 1

	def doList(self):
		for pluginName in self.pluginManager.getPluginList("os"):
			self._printPluginUsage("os", pluginName)
		for pluginName in self.pluginManager.getPluginList("app"):
			self._printPluginUsage("app", pluginName)

	def doCreate(self):
		"""create new virtual machine and do an unattended os setup"""

		self.args.vmdir = os.path.abspath(self.args.vmdir)

		pObj = self.pluginManager.getPluginObjByType("os", self.args.plugin)
		if pObj is None:
			raise Exception("failed to load os-plugin %s."%(self.args.plugin))

		if os.path.exists(self.args.vmdir):
			raise Exception("target virtual machine directory already exists")

		try:
			# create virt-machine
			self.infoPrinter.printInfo("Creating virtual machine in directory \"%s\"..."%(self.args.vmdir))
			self.infoPrinter.incIndent()

			vmCfgBasic = self._getVmCfgBasicByArgs(self.args)
			vmCfgHw = pObj.getVmCfgHw(self.param, self.args.popt)				# fixme: should return hardware spec
			vmCfgBasic.checkValid()
			vmCfgHw.checkValid()
			self._printVmInfo(self.infoPrinter, vmCfgBasic, vmCfgHw)

			vb = FvmVmBuilder(self.param)
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

	def doInstall(self):
		"""do an unattended application installation"""

		self.args.vmdir = os.path.abspath(self.args.vmdir)

		pObj = self.pluginManager.getPluginObjByType("app", self.args.plugin)
		if pObj is None:
			raise Exception("failed to load app-plugin %s."%(self.args.plugin))

		if not os.path.exists(self.args.vmdir):
			raise Exception("target virtual machine directory does not exist")

		# install application
		self.infoPrinter.printInfo("Installing application \"%s\"..."%(pObj.getAppName()))
		self.infoPrinter.incIndent()

		vmObj = FvmVmObject(self.param, self.args.vmdir)
		self.param.tmpDir = os.path.join(self.args.vmdir, "temp")
		try:
			if vmObj.isLocked():
				raise Exception("the specified virtual machine is operating by other program")
			vmObj.lock()

			if self.args.plugin in vmObj.getVmInfo().vmCfgWin.appDict:
				raise Exception("the specified application has already been installed")

			# get install work list
			FvmUtil.mkDirAndClear(self.param.tmpDir)
			workList = pObj.doInstall(self.param, vmObj.getVmInfo(), self.args.popt)

			# get init desktop backup work
			desktopBackup = pObj.getDesktopItemBackup(self.param, vmObj.getVmInfo(), self.args.popt)
			if desktopBackup is not None:
				work = FvmWorkOffLineInitDesktopBackup()
				work.setWorkName("Initialize desktop item backup")
				work.setDesktopBackup(desktopBackup)
				workList.append(work)

			# execute work list
			vmObj.setShowUi(self.args.showui)
			wlExec = FvmWorkListExecutor(self.param, vmObj, self.infoPrinter)
			wlExec.executeWorkList(workList)

			# recording app info
			self._changeVmCfgWinForAppInstall(vmObj, self.args.plugin, self.args.popt)
		finally:
			if not self.args.keep:
				FvmUtil.forceDelete(self.param.tmpDir)
				self.param.tmpDir = ""
			vmObj.unlock()

		self.infoPrinter.decIndent()
		self.infoPrinter.printInfo("Complete!")

	def doUninstall(self):
		"""do an unattended application un-installation"""

		self.args.vmdir = os.path.abspath(self.args.vmdir)

		pObj = self.pluginManager.getPluginObjByType("app", self.args.plugin)
		if pObj is None:
			raise Exception("failed to load app-plugin %s."%(self.args.plugin))

		if not os.path.exists(self.args.vmdir):
			raise Exception("target virtual machine directory does not exist")

		# install application
		self.infoPrinter.printInfo("Uninstalling application \"%s\"..."%(pObj.getAppName()))
		self.infoPrinter.incIndent()

		vmObj = FvmVmObject(self.param, self.args.vmdir)
		self.param.tmpDir = os.path.join(self.args.vmdir, "temp")
		try:
			if vmObj.isLocked():
				raise Exception("the specified virtual machine is operating by other program")
			vmObj.lock()

			if self.args.plugin not in vmObj.getVmInfo().vmCfgWin.appDict:
				raise Exception("the specified application has not been installed")

			FvmUtil.mkDirAndClear(self.param.tmpDir)
			work = pObj.doUninstall(self.param, vmObj.getVmInfo(), self.args.popt)

			vmObj.setShowUi(self.args.showui)
			wlExec = FvmWorkListExecutor(self.param, vmObj, self.infoPrinter)
			wlExec.executeWorkList([work])
			self._changeVmCfgWinForAppUninstall(vmObj, self.args.plugin)
		finally:
			if not self.args.keep:
				FvmUtil.forceDelete(self.param.tmpDir)
				self.param.tmpDir = ""
			vmObj.unlock()

		self.infoPrinter.decIndent()
		self.infoPrinter.printInfo("Complete!")

	def doOsConfigure(self, pObj):
		"""make change to a virtual machine"""

		self.args.vmdir = os.path.abspath(self.args.vmdir)

		if not os.path.exists(self.args.vmdir):
			raise Exception("target virtual machine directory does not exist")

		# open vmObj and run configuration operation
		self.infoPrinter.printInfo("Doing os-configure operation...")
		self.infoPrinter.incIndent()

		vmObj = FvmVmObject(self.param, self.args.vmdir)
		self.param.tmpDir = os.path.join(self.args.vmdir, "temp")
		try:
			if vmObj.isLocked():
				raise Exception("the specified virtual machine is being used by other program")
			vmObj.lock()

			FvmUtil.mkDirAndClear(self.param.tmpDir)

			if len(self.args.popt) > 0:
				workList = pObj.doConfigure(self.param, vmObj.getVmInfo(), self.args.popt)
				vmObj.setShowUi(self.args.showui)
				wlExec = FvmWorkListExecutor(self.param, vmObj, self.infoPrinter)
				wlExec.executeWorkList(workList)
				self._changeVmCfgWinForOsConfigure(vmObj, pObj, self.args.popt)
		finally:
			if not self.args.keep:
				FvmUtil.forceDelete(self.param.tmpDir)
				self.param.tmpDir = ""
			vmObj.unlock()

		self.infoPrinter.decIndent()
		self.infoPrinter.printInfo("Done!")

	def doAppConfigure(self, pObj):
		"""make change to a virtual machine"""

		self.args.vmdir = os.path.abspath(self.args.vmdir)

		if not os.path.exists(self.args.vmdir):
			raise Exception("target virtual machine directory does not exist")

		# open vmObj and run configuration operation
		self.infoPrinter.printInfo("Doing app-configure operation...")
		self.infoPrinter.incIndent()

		vmObj = FvmVmObject(self.param, self.args.vmdir)
		self.param.tmpDir = os.path.join(self.args.vmdir, "temp")
		try:
			if vmObj.isLocked():
				raise Exception("the specified virtual machine is being used by other program")
			vmObj.lock()

			if self.args.plugin not in vmObj.getVmInfo().vmCfgWin.appDict:
				raise Exception("the specified application has not been installed")

			FvmUtil.mkDirAndClear(self.param.tmpDir)

			if len(self.args.popt) > 0:
				workList = self._getAppCfgWorkList(vmObj, pObj, self.args.plugin, self.args.popt)
				vmObj.setShowUi(self.args.showui)
				wlExec = FvmWorkListExecutor(self.param, vmObj, self.infoPrinter)
				wlExec.executeWorkList(workList)
				self._changeVmCfgWinForAppConfigure(vmObj, pObj, self.args.plugin, self.args.popt)
		finally:
			if not self.args.keep:
				FvmUtil.forceDelete(self.param.tmpDir)
				self.param.tmpDir = ""
			vmObj.unlock()

		self.infoPrinter.decIndent()
		self.infoPrinter.printInfo("Done!")

	def doExecute(self):
		"""execute operation on a virtual machine"""

		self.args.vmdir = os.path.abspath(self.args.vmdir)

		pObj = self.pluginManager.getPluginObj(self.args.plugin)
		if pObj is None:
			raise Exception("failed to load os-plugin %s or app-plugin %s."%(self.args.plugin, self.args.plugin))

		if not os.path.exists(self.args.vmdir):
			raise Exception("target virtual machine directory does not exist")

		# open vmObj and run configuration operation
		self.infoPrinter.printInfo("Doing %s-execute operation..."%(self._getPluginType(pObj)))
		self.infoPrinter.incIndent()

		vmObj = FvmVmObject(self.param, self.args.vmdir)
		self.param.tmpDir = os.path.join(self.args.vmdir, "temp")
		try:
			if vmObj.isLocked():
				raise Exception("the specified virtual machine is being used other program")
			vmObj.lock()

			FvmUtil.mkDirAndClear(self.param.tmpDir)
			workList = pObj.doExecute(self.param, vmObj.getVmInfo(), self.args.popt)

			vmObj.setShowUi(self.args.showui)
			wlExec = FvmWorkListExecutor(self.param, vmObj, self.infoPrinter)
			wlExec.executeWorkList(workList)
		finally:
			if not self.args.keep:
				FvmUtil.forceDelete(self.param.tmpDir)
				self.param.tmpDir = ""
			vmObj.unlock()

		self.infoPrinter.decIndent()
		self.infoPrinter.printInfo("Done!")

	def doReCreate(self):
		"""re-create virtual machine"""

		self.args.vmdir = os.path.abspath(self.args.vmdir)
		if not os.path.exists(self.args.vmdir):
			raise Exception("target virtual machine directory does not exist")

		vmDir = self.args.vmdir
		bakDir = vmDir + ".bak"

		# get virtual machine config
		self.infoPrinter.printInfo("Get virtual machine configuration...")

		oriCfgBasic = FvmVmObject(self.param, vmDir).getVmInfo().vmCfgBasic
		oriCfgHw = FvmVmObject(self.param, vmDir).getVmInfo().vmCfgHw
		oriCfgWin = FvmVmObject(self.param, vmDir).getVmInfo().vmCfgWin

		# check plugins
		if self.pluginManager.getPluginObjByType("os", oriCfgWin.os.pluginName) is None:
			raise Exception("failed to load os-plugin %s."%(oriCfgWin.os.pluginName))
		for k in oriCfgWin.appDict:
			if self.pluginManager.getPluginObjByType("app", k) is None:
				raise Exception("failed to load app-plugin %s."%(k))

		# backup virtual machine
		self.infoPrinter.printInfo("Backup virtual machine to directory \"%s\"..."%(bakDir))
		try:
			os.rename(vmDir, bakDir)
		except OSError:
			raise Exception("can not backup virtual machine")

		# create new virtual machine with the original plugin option
		self.infoPrinter.printInfo("Create virtual machine with the original plugin option...")
		self.infoPrinter.incIndent()

		vb = FvmVmBuilder(self.param)
		vb.createVm(self.args.vmdir, oriCfgBasic, oriCfgHw)
		FvmUtil.copyToDir(os.path.join(bakDir, "element.ini"), vmDir)		# don't lose extra info in element.ini

		self.infoPrinter.decIndent()
		self.infoPrinter.printInfo("Complete!")

		# re-play all the config operations
		self.infoPrinter.printInfo("Replay all the operations...")
		self.infoPrinter.incIndent()

		vmObj = FvmVmObject(self.param, self.args.vmdir)
		wlExec = FvmWorkListExecutor(self.param, vmObj, self.infoPrinter)
		self.param.tmpDir = os.path.join(self.args.vmdir, "temp")
		try:
			vmObj.lock()
			vmObj.setShowUi(self.args.showui)

			FvmUtil.mkDirAndClear(self.param.tmpDir)

			# re-play os-setup and os-configure
			if True:
				pObj = self.pluginManager.getPluginObjByType("os", oriCfgWin.os.pluginName)
				assert pObj is not None

				# execute os setup work
				workList = pObj.doSetup(self.param, vmObj.getVmInfo(), oriCfgWin.os.setupOptList)
				for w in workList:
					assert isinstance(w, FvmWorkFullControl)
				wlExec.executeWorkList(workList)
				assert not vmObj.getSetupMode()
				self._changeVmCfgWinForOsSetup(vmObj, oriCfgWin.os.pluginName, oriCfgWin.os.setupOptList)

				# execute initial configure work
				workList = pObj.doInitialConfigure(self.param, vmObj.getVmInfo())
				wlExec.executeWorkList(workList)

				# execute configure work
				if len(oriCfgWin.os.cfgOptList) > 0:
					workList = pObj.doConfigure(self.param, vmObj.getVmInfo(), oriCfgWin.os.cfgOptList)
					wlExec.executeWorkList(workList)
					self._changeVmCfgWinForOsConfigure(vmObj, pObj, oriCfgWin.os.setupOptList)

			# re-play app-install and app-configure
			for k,v in oriCfgWin.appDict.items():
				pObj = self.pluginManager.getPluginObjByType("app", k)
				assert pObj is not None

				# execute app install work
				workList = pObj.doInstall(self.param, vmObj.getVmInfo(), v.installOptList)
				desktopBackup = pObj.getDesktopItemBackup(self.param, vmObj.getVmInfo(), v.installOptList)
				if desktopBackup is not None:
					work = FvmWorkOffLineInitDesktopBackup()
					work.setWorkName("Initialize desktop item backup")
					work.setDesktopBackup(desktopBackup)
					workList.append(work)
				wlExec.executeWorkList(workList)
				self._changeVmCfgWinForAppInstall(vmObj, k, v.installOptList)

				# execute app configure work
				if len(v.cfgOptList) > 0:
					workList = self._getAppCfgWorkList(vmObj, pObj, k, v.cfgOptList)
					wlExec.executeWorkList(workList)
					self._changeVmCfgWinForAppConfigure(vmObj, pObj, k, v.cfgOptList)
		finally:
			if not self.args.keep:
				FvmUtil.forceDelete(self.param.tmpDir)
				self.param.tmpDir = ""
			vmObj.unlock()

		self.infoPrinter.decIndent()
		self.infoPrinter.printInfo("Complete!")

		# delete backup
#		self.infoPrinter.printInfo("Delete backup...")
#		shutil.rmtree(bakDir)

	def doModify(self):
		"""modify a virtual machine's configuration"""

		raise Exception("Not implemented!")

	def _printPluginUsage(self, pluginType, pluginName):
		print "%s-plugin: %s"%(pluginType, pluginName)
		pObj = self.pluginManager.getPluginObjByType(pluginType, pluginName)
		for line in pObj.getUsage().split("\n"):
			print "  %s"%(line)

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

	def _getPluginType(self, pObj):
		if isinstance(pObj, FvmPluginOs):
			return "os"
		elif isinstance(pObj, FvmPluginApp):
			return "app"
		else:
			assert False

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

