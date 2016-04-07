#!/usr/bin/python
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import re
import shutil
import subprocess

class PluginObject:

	def __init__(self, dataDir):
		self.dataDir = dataDir

	def getUsage(self):
		"""returns string list"""

		ret = ""
		ret += "Valid options:\n"
		ret += "  explorer-show-file-ext\n"
		ret += "  explorer-hide-file-ext\n"
		return ret

	def doConfig(self, vmObj, vmTmpDir, pluginOptionStr, infoPrinter):
		"""do OS config operation"""

		# checking
		if vmObj.getConfig().gInfo.createPlugin != "win7":
			raise Exception("the specified virtual machine is not type Windows 7")

		# prepare parameter
		self.vmObj = vmObj
		self.tmpDir = vmTmpDir
		self.jobList = self._parsePluginOptionStr(pluginOptionStr)
		self.osName = self._parseCreatePluginOptionStr(vmObj.getConfig().gInfo.createPluginOptStr)
		self.infoPrinter = infoPrinter

		# show setup infomation
		self.infoPrinter.printInfo(">> Config paramenter:")
		self.infoPrinter.printInfo("     OS: ?")
		self.infoPrinter.printInfo("")

		# install driver
		if True:
			# prepare driver usb disk
			self.infoPrinter.printInfo(">> Preparing device driver USB image...")
			usbFile = self._createDriverUsb()
			self.vmObj.setLocalUsbImage(usbFile)

			# set RunOnce registry entry
			self.infoPrinter.printInfo(">> Setting RunOnce registry entry...")
			vbsFile = os.path.join(self.tmpDir, "temp.vbs")
			regFile = os.path.join(self.tmpDir, "temp.reg")
			FvmUtil.createRunOnceFiles(regFile, vbsFile, "D:\\install_driver.bat", 60)
			FvmUtil.convertToWinFile(vbsFile)
			FvmUtil.shell('/usr/bin/virt-copy-in -a \"%s\" \"%s\" /'%(vmObj.getMainDiskImage(), vbsFile), "stdout")
			FvmUtil.shell('/usr/bin/virt-win-reg --merge \"%s\" \"%s\"'%(vmObj.getMainDiskImage(), regFile), "stdout")
#			os.remove(regFile)
#			os.remove(vbsFile)

			# run virtual machine
			self.infoPrinter.printInfo(">> Booting virtual machine again, installing drivers...")
			self.vmObj.run(forSetup=True)
			self.vmObj.setLocalUsbImage("")

		# final job
		self.infoPrinter = None
		self.osName = ""
		self.tmpDir = ""
		self.vmObj = None

	def _parsePluginOptionStr(self, pluginOptionStr):
		m = re.search(r"^os=(\S+)$", pluginOptionStr)
		if m is None:
			raise Exception("invalid plugin option, no \"os\" option")
		osName = m.group(1)
		return osName

	def _parseCreatePluginOptionStr(self, pluginOptionStr):
		m = re.search(r"^os=(\S+)$", pluginOptionStr)
		if m is None:
			raise Exception("invalid plugin option, no \"os\" option")
		osName = m.group(1)
		return osName

	class _OsInfo:
		ostype = ""
		patch = ""
		arch = ""
		lang = ""

	def _getOsInfo(self, osName):
		ret = self._OsInfo()

		if ".Ultimate." in osName:
			ret.ostype = "Ultimate"
		else:
			assert False

		if ".X86." in osName:
			ret.arch = "X86"
		elif ".X86_64." in osName:
			ret.arch = "X86_64"
		else:
			assert False

		if osName.endswith(".zh_CN"):
			ret.lang = "zh_CN"
		else:
			assert False

		if ".SP1." in osName:
			ret.patch = "SP1"
		elif ".SP2." in osName:
			ret.patch = "SP2"
		elif ".SP3." in osName:
			ret.patch = "SP3"
		else:
			ret.patch = ""

		return ret

	def _getFile(self, osName, ftype): 
		if osName == "Microsoft.Windows.7.Ultimate.SP1.X86.zh_CN":
			if ftype == "iso":
				return os.path.join(self.dataDir, "cn_windows_7_ultimate_with_sp1_x86_dvd_u_677486.iso")
			else:
				assert False

		if osName == "Microsoft.Windows.7.Ultimate.SP1.X86_64.zh_CN":
			if ftype == "iso":	
				return os.path.join(self.dataDir, "cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso")
			else:
				assert False
		
		assert False

	def _createDriverUsb(self):
		"""note: directory 'usbImgMountPoint' can only be operated by command and with some restriction after mount"""

		# create usb file
		usbFile = os.path.join(self.tmpDir, "usb.img")
		FvmUtil.createFile(usbFile, 200 * 1024 * 1024)	# 200MiB
		FvmUtil.shell('/usr/bin/virt-format --format=raw --partition=mbr --filesystem=ntfs -a \"%s\"'%(usbFile), "stdout")
		FvmUtil.shellInteractive("/sbin/fdisk \"%s\""%(usbFile), "t\n7\nw", "stdout")	# change partition's system id to NTFS(7)

		# mount usb file
		mountPoint = os.path.join(self.tmpDir, "usbImgMountPoint")
		os.mkdir(mountPoint)
		FvmUtil.shell('/usr/bin/guestmount -a \"%s\" -m /dev/sda1 \"%s\"'%(usbFile, mountPoint), "stdout")

		try:
			# add autoit3
			autoitDir = os.path.join(mountPoint, "autoit")
			FvmUtil.shell('/bin/mkdir \"%s\"'%(autoitDir), "stdout")
			FvmUtil.shell('/usr/bin/unzip \"%s\" -d \"%s\"'%(os.path.join(self.dataDir, "autoit3.zip"), autoitDir), "stdout")

			# add paraDrvIso
			drvDir = os.path.join(mountPoint, "driver")
			FvmUtil.shell('/bin/mkdir \"%s\"'%(drvDir), "stdout")
			FvmUtil.shell('/usr/bin/7z x \"%s\" -o\"%s\"'%(os.path.join(self.dataDir, "virtio-win-0.1-52.iso"), drvDir), "stdout")

			# add devcon.exe
			FvmUtil.shell('/bin/cp \"%s\" \"%s\"'%(os.path.join(self.dataDir, "devcon.exe"), mountPoint))

			# add spice-guest-tools.exe
			FvmUtil.shell('/bin/cp \"%s\" \"%s\"'%(os.path.join(self.dataDir, "spice-guest-tools-0.52.exe"), mountPoint))

			# add autoinst-spice-guest-tools.au3
			tmpf = os.path.join(self.tmpDir, "autoinst-spice-guest-tools.au3")
			shutil.copy(os.path.join(self.dataDir, "autoinst-spice-guest-tools.au3"), tmpf)
			FvmUtil.convertToWinFile(tmpf)
			FvmUtil.shell('/bin/cp \"%s\" \"%s\"'%(tmpf, mountPoint))
			os.remove(tmpf)

			# add install_driver.bat
			tmpf = os.path.join(self.tmpDir, "install_driver.bat")
			self._generateInstallDriverBat(os.path.join(mountPoint, tmpf))
			FvmUtil.convertToWinFile(tmpf)
			FvmUtil.shell('/bin/cp \"%s\" \"%s\"'%(tmpf, mountPoint))
			os.remove(tmpf)

			# add autorun.inf, to dismiss the AutoPlay dialog
			tmpf = os.path.join(self.tmpDir, "autorun.inf")
			FvmUtil.createAutoRunInfFile(tmpf)
			FvmUtil.convertToWinFile(tmpf)
			FvmUtil.shell('/bin/cp \"%s\" \"%s\"'%(tmpf, mountPoint))
			os.remove(tmpf)
		finally:
			# unmount usb file
			FvmUtil.shell('/usr/bin/fusermount -u \"%s\"'%(mountPoint))

		return usbFile

	def _getArch(self):
		osInfo = self._getOsInfo(self.osName)
		if osInfo.arch == "X86":
			return "x86"
		elif osInfo.arch == "X86_64":
			return "amd64"
		else:
			assert False

	def _getLang(self):
		osInfo = self._getOsInfo(self.osName)
		if osInfo.lang == "en_US":
			return "en-us"
		elif osInfo.lang == "zh_CN":
			return "zh-cn"
		elif osInfo.lang == "zh_TW":
			return "zh-tw"
		else:
			assert False

	def _getTimezone(self):
		osInfo = self._getOsInfo(self.osName)
		if osInfo.lang == "en_US":
			return "Pacific Standard Time"
		elif osInfo.lang == "zh_CN":
			return "China Standard Time"
		elif osInfo.lang == "zh_TW":
			return "Taipei Standard Time"
		else:
			assert False

	def _generateInstallDriverBat(self, batFile):

		# read template
		batTemplateFile = os.path.join(self.dataDir, "install_driver.bat")
		buf = FvmUtil.readFile(batTemplateFile)

		# replace content
		buf = buf.replace("@@arch@@", self._getArch())

		# write file
		FvmUtil.writeFile(batFile, buf)

class FvmUtil:
	@staticmethod
	def createFile(filename, size, mode=None):
		"""Create a sparse file, in bytes"""

		assert not os.path.exists(filename)

		f = open(filename, 'ab')
		f.truncate(size)
		f.close()
		if mode is not None:
			FvmUtil.shell("/bin/chmod " + mode + " \"" + filename + "\"")

	@staticmethod
	def readFile(filename):
		"""Read file, returns the whold content"""

		f = open(filename, 'r')
		buf = f.read()
		f.close()
		return buf

	@staticmethod
	def writeFile(filename, buf, mode=None):
		"""Write buffer to file"""

		f = open(filename, 'w')
		f.write(buf)
		f.close()
		if mode is not None:
			FvmUtil.shell("/bin/chmod " + mode + " \"" + filename + "\"")

	@staticmethod
	def shell(cmd, flags=""):
		"""Execute shell command"""

		assert cmd.startswith("/")

		# Execute shell command, throws exception when failed
		if flags == "":
			retcode = subprocess.Popen(cmd, shell = True).wait()
			if retcode != 0:
				raise Exception("Executing shell command \"%s\" failed, return code %d"%(cmd, retcode))
			return

		# Execute shell command, throws exception when failed, returns stdout+stderr
		if flags == "stdout":
			proc = subprocess.Popen(cmd,
									shell = True,
									stdout = subprocess.PIPE,
									stderr = subprocess.STDOUT)
			out = proc.communicate()[0]
			if proc.returncode != 0:
				raise Exception("Executing shell command \"%s\" failed, return code %d"%(cmd, proc.returncode))
			return out

		# Execute shell command, returns (returncode,stdout+stderr)
		if flags == "retcode+stdout":
			proc = subprocess.Popen(cmd,
									shell = True,
									stdout = subprocess.PIPE,
									stderr = subprocess.STDOUT)
			out = proc.communicate()[0]
			return (proc.returncode, out)

		assert False

	@staticmethod
	def shellInteractive(cmd, strInput, flags=""):
		"""Execute shell command with input interaction"""

		assert cmd.startswith("/")

		# Execute shell command, throws exception when failed
		if flags == "":
			proc = subprocess.Popen(cmd,
									shell = True,
									stdin = subprocess.PIPE)
			proc.communicate(strInput)
			if proc.returncode != 0:
				raise Exception("Executing shell command \"%s\" failed, return code %d"%(cmd, proc.returncode))
			return

		# Execute shell command, throws exception when failed, returns stdout+stderr
		if flags == "stdout":
			proc = subprocess.Popen(cmd,
									shell = True,
									stdin = subprocess.PIPE,
									stdout = subprocess.PIPE,
									stderr = subprocess.STDOUT)
			out = proc.communicate(strInput)[0]
			if proc.returncode != 0:
				raise Exception("Executing shell command \"%s\" failed, return code %d"%(cmd, proc.returncode))
			return out

		# Execute shell command, returns (returncode,stdout+stderr)
		if flags == "retcode+stdout":
			proc = subprocess.Popen(cmd,
									shell = True,
									stdin = subprocess.PIPE,
									stdout = subprocess.PIPE,
									stderr = subprocess.STDOUT)
			out = proc.communicate(strInput)[0]
			return (proc.returncode, out)

		assert False

	@staticmethod
	def createRunOnceFiles(regFile, vbsFile, command, delaySec):
		"""vbsFile's basename must equal to the one in guest machine
		   vbsFile should be run with cscript.exe in guest machine"""

		# create delayed run VBS script
		buf = ""
		buf += "Wscript.Echo \"Waiting %d seconds\"\n"%(delaySec)
		buf += "Wscript.Sleep(%d * 1000)\n"%(delaySec)
		buf += "\n"
		buf += "Wscript.Echo \"Run command: %s\"\n"%(command)
		buf += "set objShell = CreateObject(\"WScript.Shell\")\n"
		buf += "objShell.CurrentDirectory = \"%s\"\n"%(FvmUtil.winDirname(command))
		buf += "objShell.Run \"%s\", bWaitOnReturn=true\n"%(command)
		buf += "Wscript.Sleep(120 * 1000)\n"						# autoit returns immediately, this behavior sucks
		buf += "\n"
		buf += "Wscript.Echo \"Delete self\"\n"
		buf += "CreateObject(\"Scripting.FileSystemObject\").DeleteFile WScript.ScriptFullName\n"
		buf += "Wscript.Sleep(1000)\n"
		buf += "\n"
		buf += "Wscript.Echo \"Shutdown\"\n"
		buf += "CreateObject(\"WScript.Shell\").Run \"shutdown /s\", bWaitOnReturn=false\n"
		buf += "Wscript.Sleep(1000)\n"
		buf += "\n"
		FvmUtil.writeFile(vbsFile, buf)

		# create reg file
		buf = ""
		buf += "[HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce]\n"
		buf += "\"temp\"=\"cscript.exe C:\\\\%s\"\n"%(FvmUtil.winBasename(vbsFile))
		FvmUtil.writeFile(regFile, buf)

	@staticmethod
	def createAutoRunInfFile(infFile, command=None):
		"""This file is used by windows, so use \n"""

		buf = ""
		buf += "[AutoRun]\n"
		buf += "UseAutoPlay=0"
		if command is not None:
			buf += "open=\"%s\"\n"%(command)
		buf += "\n"
		buf += "[Content]\n"
		buf += "MusicFiles=false\n"
		buf += "PictureFiles=false\n"
		buf += "VideoFiles=false\n"
		FvmUtil.writeFile(infFile, buf)

	@staticmethod
	def winBasename(path):
		i = path.rfind("\\")
		if i == -1:
			return path
		else:
			return path[i+1:]

	@staticmethod
	def winDirname(path):
		i = path.rfind("\\")
		if i == -1:
			return ""
		else:
			return path[:i]
