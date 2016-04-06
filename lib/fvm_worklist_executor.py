#!/usr/bin/python2
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import shutil
from fvm_util import FvmUtil
from fvm_util import WinDiskMountPoint
from fvm_util import WinRegistry
from fvm_plugin import FvmWorkFullControl
from fvm_plugin import FvmWorkOffLineFree
from fvm_plugin import FvmWorkOffLineModifyRegistry
from fvm_plugin import FvmWorkOffLineInjectFile
from fvm_plugin import FvmWorkOffLineInitDesktopBackup
from fvm_plugin import FvmWorkOffLineOperateDesktopBackup
from fvm_plugin import FvmWorkOnLineFree
from fvm_plugin import FvmWorkOnLineExec

class FvmWorkListExecutor:

	def __init__(self, param, vmObj, infoPrinter):
		self.param = param
		self.vmObj = vmObj
		self.infoPrinter = infoPrinter

	def executeWorkList(self, workList):
		self._checkWorkList(workList)

		i = 0
		while i < len(workList):
			w = workList[i]
			if isinstance(w, FvmWorkFullControl):
				workCount = self._executeWorkFullControl(workList, i)
			elif self._isWorkOffLine(w):
				workCount = self._executeWorkListOffLine(workList, i)
			elif self._isWorkOnLine(w):
				workCount = self._executeWorkListOnLine(workList, i)
			else:
				assert False
			i = i + workCount

	def _checkWorkList(self, workList):
		for w in workList:
			assert w.workName is not None

			if isinstance(w, FvmWorkFullControl):
				pass
			elif isinstance(w, FvmWorkOffLineFree):
				pass
			elif isinstance(w, FvmWorkOffLineModifyRegistry):
				pass
			elif isinstance(w, FvmWorkOffLineInjectFile):
				pass
			elif isinstance(w, FvmWorkOffLineInitDesktopBackup):
				assert w.desktopBackupObj is not None
			elif isinstance(w, FvmWorkOffLineOperateDesktopBackup):
				assert w.desktopBackupObj is not None
			elif isinstance(w, FvmWorkOnLineFree):
				execFile, argList = w.getCmdLine()
				reqList = w.getReqList()
				assert execFile is not None
				assert isinstance(argList, list)
				assert isinstance(reqList, list)
			elif isinstance(w, FvmWorkOnLineExec):
				assert w.execFile is not None
				assert isinstance(w.argList, list)
				assert isinstance(w.reqList, list)
			else:
				assert False

	def _executeWorkFullControl(self, workList, startIndex):

		self.infoPrinter.printInfo(">> %s"%(workList[startIndex].workName))
		self.infoPrinter.incIndent()

		w = workList[startIndex]
		w.doWork(self.param, self.vmObj, self.infoPrinter)

		self.infoPrinter.decIndent()
		self._resetVmEnvironment()
		return 1

	def _executeWorkListOffLine(self, workList, startIndex):

		self.infoPrinter.printInfo(">> Doing off-line operation...")
		self.infoPrinter.incIndent()

		workCount = 0
		mptObj = WinDiskMountPoint(self.param, self.vmObj.getMainDiskImage(), self._getWinLang())
		try:
			winreg = WinRegistry(self.param, mptObj.getMountDir())

			i = 0
			while (startIndex + i) < len(workList):
				w = workList[startIndex + i]
				if not self._isWorkOffLine(w):
					break

				self.infoPrinter.printInfo(">> %s"%(workList[startIndex + i].workName))

				if isinstance(w, FvmWorkOffLineFree):
					w.operateMainDisk(self.param, mptObj.getMountDir())
				elif isinstance(w, FvmWorkOffLineModifyRegistry):
					if w.op == "addOrModify":
						winreg.addOrModify(w.key, w.name, w.valueType, w.value)
					elif w.op == "delete":
						winreg.delete(w.key, w.name)
					else:
						assert False
				elif isinstance(w, FvmWorkOffLineInjectFile):
					mptObj.addFile(w.filename, w.dstDir, w.isBinary)
				elif isinstance(w, FvmWorkOffLineInitDesktopBackup):
					w.desktopBackupObj.initBackup(self.param, mptObj.getMountDir())
				elif isinstance(w, FvmWorkOffLineOperateDesktopBackup):
					w.desktopBackupObj.syncBackup(self.param, mptObj.getMountDir())
					for itemName, state in w.itemStateList:
						w.desktopBackupObj.setItemState(itemName, state)
				else:
					assert False

				i = i + 1

			# get workCount
			workCount = i
			assert workCount > 0
		finally:
			mptObj.umount()

		self.infoPrinter.decIndent()
		self._resetVmEnvironment()
		return workCount

	def _executeWorkListOnLine(self, workList, startIndex):
		"""usb.img directory structure:
		     [usb.img]
		       |--config.ini
			   |--autoit
			        |--autoit files
			   |--work1
			        |--_do_work.bat
			        |--xxxx.au3
			   |--work2
			        |--_do_work.bat
			        |--xxxx.au3
			        |--other files
			   |--work3
			        |--_do_work.bat
			        |--xxxx.bat
			        |--other files
			   |--work4
			        |--_do_work.bat
			        |--xxxx.exe

		   config.ini format:
		     [config]
		     winLang = "xxxx"
		     reqList = "xx1 xx2"

		     [boot]
		     bootNo = 1
		     bootInfo = "xxxx"
		     shutdownFlag = false"""

		self.infoPrinter.printInfo(">> Doing on-line operation...")
		self.infoPrinter.incIndent()

		# prepare usb disk
		usbFile = os.path.join(self.param.tmpDir, "usb.img")
		FvmUtil.createWinUsbImg(usbFile, 1024, "ntfs")
		mptObj = WinDiskMountPoint(self.param, usbFile, self._getWinLang())

		# copy files to usb disk
		batFileList = []
		reqList = None
		workCount = 0
		try:
			mptObj.addAutoIt()
			mptObj.addSevenZip()

			# process work
			i = 0
			while (startIndex + i) < len(workList):
				w = workList[startIndex + i]
				if not self._isWorkOnLine(w):
					break
				if self._mergeReqList(reqList, w) is None:
					break

				# create work-dir
				workDir = "work%d"%(i)
				mptObj.mkdir(workDir)

				if isinstance(w, FvmWorkOnLineFree):
					# fill usb disk
					absWorkDir = os.path.join(mptObj.getMountDir(), workDir)
					w.fillUsbDataDir(self.param, absWorkDir)

					# generate _do_work.bat
					(execFile, argList) = w.getCmdLine()
					tmpf = self._generateTmpDoWorkBatFile(execFile, argList)
					mptObj.addTmpFile(tmpf, workDir, False)

				elif isinstance(w, FvmWorkOnLineExec):
					# fill usb disk
					for fname, isBinary in w.fileList:
						mptObj.addFile(fname, workDir, isBinary)
					for fname, isBinary in w.tmpFileList:
						mptObj.addTmpFile(fname, workDir, isBinary)
					for fname in w.zipFileList:
						d = os.path.join(workDir, os.path.splitext(os.path.basename(fname))[0])
						mptObj.mkdir(d)
						mptObj.addZipFile(fname, d)
					if True:
						isBinary = w.execFile.endswith(".exe")
						mptObj.addFile(w.execFile, workDir, isBinary)

					# generate _do_work.bat
					tmpf = self._generateTmpDoWorkBatFile(os.path.basename(w.execFile), w.argList)
					mptObj.addTmpFile(tmpf, workDir, False)

				else:
					assert False

				reqList = self._mergeReqList(reqList, w)
				batFileList.append("%s\\_do_work.bat"%(os.path.basename(workDir)))
				i = i + 1

			# get workCount
			workCount = i
			assert workCount > 0

			# add config.ini
			tmpf = self._generateTmpConfigIniFile(reqList)
			mptObj.addTmpFile(tmpf, "", False)
		finally:
			mptObj.umount()

		for i in range(0, workCount):
			self.infoPrinter.printInfo(">> %s"%(workList[startIndex + i].workName))

		# pre-run virtual machine
		cdromf = self._getCdromFileFromReqList(reqList)
		if cdromf is not None:
			self.vmObj.setLocalCdromImage(cdromf)
		self.vmObj.setLocalUsbImage(usbFile)
		if "noNetwork" in reqList:
			self.vmObj.setNetworkStatus("none")
		elif "network" not in reqList:
			self.vmObj.setNetworkStatus("isolate")

		# run virtual machine
		FvmUtil.winPauseAutoActivity(self.param, self.vmObj.getMainDiskImage(), self._getWinLang())
		self._createAndInjectStartupFile(batFileList, (cdromf is not None))
		self.vmObj.run()
		FvmUtil.winResumeAutoActivity(self.param, self.vmObj.getMainDiskImage(), self._getWinLang())

		self.infoPrinter.decIndent()
		self._resetVmEnvironment()
		return workCount

	def _isWorkOffLine(self, w):
		if isinstance(w, FvmWorkOffLineFree):
			return True
		elif isinstance(w, FvmWorkOffLineModifyRegistry):
			return True
		elif isinstance(w, FvmWorkOffLineInjectFile):
			return True
		elif isinstance(w, FvmWorkOffLineInitDesktopBackup):
			return True
		elif isinstance(w, FvmWorkOffLineOperateDesktopBackup):
			return True
		else:
			return False

	def _isWorkOnLine(self, w):
		return isinstance(w, FvmWorkOnLineFree) or isinstance(w, FvmWorkOnLineExec)

	def _generateTmpConfigIniFile(self, reqList):

		shutdownFlag = "true"
		if "rebootAndShutdown" in reqList:
			shutdownFlag = "false"

		buf = ''
		buf += '[config]\n'
		buf += 'reqList=%s\n'%(" ".join(reqList))
		buf += 'winLang=%s\n'%(self._getWinLang())
		buf += '\n'
		buf += '[boot]\n'
		buf += 'bootNo=0\n'						# startup.bat will increase it in every boot process
		buf += 'bootInfo=\n'
		buf += 'shutdownFlag=%s\n'%(shutdownFlag)
		buf += '\n'

		tmpf = os.path.join(self.param.tmpDir, "config.ini")
		FvmUtil.writeFile(tmpf, buf)
		return tmpf

	def _generateTmpDoWorkBatFile(self, execFile, argList):
		"""execFile and argList should be windows path"""

		assert not FvmUtil.isWinAbsPath(execFile)

		buf = ''
		buf += '@echo off\n'
		buf += 'setlocal enabledelayedexpansion\n'
		buf += '\n'
		if execFile.endswith(".au3"):
			buf += '"..\\autoit\\autoit3.exe" "%s"'%(execFile)
		elif execFile.endswith(".bat"):
			buf += 'call "%s"'%(execFile)
		elif execFile.endswith(".exe"):
			buf += '"%s"'%(execFile)
		else:
			assert False
		for a in argList:
			buf += ' "%s"'%(a)
		buf += '\n'
		buf += 'goto :eof\n'
		buf += '\n'

		tmpf = os.path.join(self.param.tmpDir, "_do_work.bat")
		FvmUtil.writeFile(tmpf, buf)
		return tmpf

	def _createAndInjectStartupFile(self, batFileList, hasCdrom):
		"""windows path elements in batFileList is relative to usb disk drive root directory"""

		# create startup file in tmpDir
		tmpf = os.path.join(self.param.tmpDir, "startup.bat")
		nbuf = ""
		if True:
			lineList = FvmUtil.readFile(os.path.join(self.param.dataDir, "startup.bat.in")).split("\n")
			tmplBegin = lineList.index("@@execute_template@@")
			tmplEnd = lineList.index("@@execute_template_end@@")

			nbuf += "\n".join(lineList[:tmplBegin]) + "\n"
			tmplBuf = "\n".join(lineList[tmplBegin+1:tmplEnd]) + "\n"
			for vsi in batFileList:
				ntbuf = tmplBuf
				ntbuf = ntbuf.replace("@@execName@@", vsi)
				ntbuf = ntbuf.replace("@@execWorkDir@@", FvmUtil.winDirname(vsi))
				ntbuf = ntbuf.replace("@@execFile@@", vsi)
				nbuf += ntbuf
			nbuf += "\n".join(lineList[tmplEnd+1:])

		if hasCdrom:
			nbuf = nbuf.replace("@@driverLetter@@", "E:")
		else:
			nbuf = nbuf.replace("@@driverLetter@@", "D:")
		FvmUtil.writeFile(tmpf, nbuf)

		# inject startup file
		mptObj = WinDiskMountPoint(self.param, self.vmObj.getMainDiskImage(), self._getWinLang())
		try:
			startupDir = FvmUtil.getWinDir("startup", self._getWinLang(), FvmUtil.getWinUser())
			mptObj.addTmpFile(tmpf, startupDir, False)
		finally:
			mptObj.umount()

		# inject startup file
#		startupDir = FvmUtil.getWinDir("startup", self._getWinLang(), FvmUtil.getWinUser())
#		FvmUtil.shell('/usr/bin/virt-copy-in -a "%s" "%s" "/%s"'%(self.vmObj.getMainDiskImage(), tmpf, startupDir), "stdout")
#
#		# remove startup file in tmpDir
#		os.remove(tmpf)

	def _mergeReqList(self, curReqList, newWork):
		"""Returns None when fail"""

		if isinstance(newWork, FvmWorkOnLineFree):
			newReqList = newWork.getReqList()
		elif isinstance(newWork, FvmWorkOnLineExec):
			newReqList = newWork.reqList
		else:
			assert False

		# special case: first time merge, always success
		if curReqList is None:
			return newReqList

		# prepare for merge check
		if "network" in curReqList:
			curNetworkStatus = "network"
		elif "isolatedNetwork" in curReqList:
			curNetworkStatus = "isolatedNetwork"
		elif "noNetwork" in curReqList:
			curNetworkStatus = "noNetwork"
		else:
			curNetworkStatus = ""

		if "network" in newReqList:
			newNetworkStatus = "network"
		elif "isolatedNetwork" in newReqList:
			newNetworkStatus = "isolatedNetwork"
		elif "noNetwork" in newReqList:
			newNetworkStatus = "noNetwork"
		else:
			newNetworkStatus = ""

		curCdrom = self._getCdromFileFromReqList(curReqList)
		newCdrom = self._getCdromFileFromReqList(newReqList)

		# do merge check
		if curNetworkStatus != "" and newNetworkStatus != "" and curNetworkStatus != newNetworkStatus:
			return None
		if "shutdown" in curReqList:
			return None
		if "rebootAndShutdown" in curReqList or "rebootAndShutdown" in newReqList:
			return None
		if curCdrom is not None and newCdrom is not None and curCdrom != newCdrom:
			return None

		# do merge
		retReqList = list(curReqList)
		if curNetworkStatus == "" and newNetworkStatus != "":
			retReqList.append(newNetworkStatus)
		if "shutdown" in newReqList:
			retReqList.append("shutdown")
		if "rebootAndShutdown" in newReqList:
			retReqList.append("rebootAndShutdown")
		if curCdrom is None and newCdrom is not None:
			retReqList.append("cdrom=%s"%(newCdrom))

		return retReqList

	def _getCdromFileFromReqList(self, reqList):
		for r in reqList:
			if r.startswith("cdrom="):
				return r[6:]
		return None

	def _getWinLang(self):
		for o in self.vmObj.getVmInfo().vmCfgWin.os.setupOptList:
			if o.startswith("os="):
				osName = o[3:]
				return FvmUtil.getWinLang(osName)
		assert False

	def _resetVmEnvironment(self):
		self.vmObj.setLocalFakeHarddisk("")
		self.vmObj.setLocalFloppyImage("")
		self.vmObj.setLocalUsbImage("")
		self.vmObj.setLocalCdromImage("")
		self.vmObj.setBootOrder(None)
		self.vmObj.setNetworkStatus("")
		FvmUtil.deleteDirContent(self.param.tmpDir)

