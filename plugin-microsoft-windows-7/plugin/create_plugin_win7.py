#!/usr/bin/python
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import re
import subprocess

class PluginObject:

	def __init__(self, dataDir):
		self.dataDir = dataDir

	def getUsage(self):
		"""returns string list"""

		ret = ""
		ret += "Valid options:\n"
		ret += "  os=Microsoft.Windows.7.Ultimate.SP1.X86.zh_CN\n"
		ret += "  os=Microsoft.Windows.7.Ultimate.SP1.X86_64.zh_CN\n"
		return ret

	def fillVmCfg(self, vmCfg, pluginOptionStr):
		"""minimal requirement: 1G mem, 25G disk"""

		osName = self._parsePluginOptionStr(pluginOptionStr)
		osInfo = self._getOsInfo(osName)

		if osInfo.arch == "X86":
			vmCfg.hwInfo.cpuArch = "x86"
		elif osInfo.arch == "X86_64":
			vmCfg.hwInfo.cpuArch = "amd64"
		else:
                        assert False

		vmCfg.hwInfo.cpuNumber = 1
		vmCfg.hwInfo.memorySize = 1 * 1024
		vmCfg.hwInfo.mainDiskInterface = "virtio-blk"
		vmCfg.hwInfo.mainDiskFormat = "raw-sparse"
		vmCfg.hwInfo.mainDiskSize = 25 * 1000
		vmCfg.hwInfo.shareDirectoryNumber = 0
		vmCfg.hwInfo.shareUsbNumber = 0
		vmCfg.hwInfo.shareScsiNumber = 0
		vmCfg.hwInfo.supportShareDirectoryHotplug = False
		vmCfg.hwInfo.supportShareUsbHotplug = False
		vmCfg.hwInfo.supportShareScsiHotplug = False

	def doSetup(self, vmObj, vmTmpDir, pluginOptionStr, infoPrinter):
		"""do OS setup operation"""

		# prepare parameter
		self.vmObj = vmObj
		self.tmpDir = vmTmpDir
		self.osName = self._parsePluginOptionStr(pluginOptionStr)
		self.infoPrinter = infoPrinter

		# check vmCfg
		self._checkVmCfg()

		# show setup infomation
		self.infoPrinter.printInfo(">> Setup paramenter:")
		self.infoPrinter.printInfo("     OS: %s"%(self.osName))
		self.infoPrinter.printInfo("")

		# setup OS
		if True:
			# prepare setup cd
			self.infoPrinter.printInfo(">> Preparing setup CD image...")
			cdromFile = self._getFile(self.osName, "iso")
			self.vmObj.setLocalCdromImage(cdromFile)

			# prepare assistant floppy
			self.infoPrinter.printInfo(">> Preparing assistant floppy disk image...")
			floppyFile = self._createAssistantFloppy()
			self.vmObj.setLocalFloppyImage(floppyFile)

			# run virtual machine
			self.infoPrinter.printInfo(">> Booting virtual machine, running setup...")
			self.vmObj.run(forSetup=True)
			self.vmObj.setLocalFloppyImage("")
			self.vmObj.setLocalCdromImage("")

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
			FvmUtil.shell('/usr/bin/virt-copy-in -a \"%s\" \"%s\" /'%(vmObj.getMainDiskImage(), vbsFile), "stdout")
			FvmUtil.shell('/usr/bin/virt-win-reg --merge \"%s\" \"%s\"'%(vmObj.getMainDiskImage(), regFile), "stdout")
			os.remove(regFile)
			os.remove(vbsFile)

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

	def _checkVmCfg(self):
		osInfo = self._getOsInfo(self.osName)
		vmCfg = self.vmObj.getConfig()

		if osInfo.arch == "X86":
			if vmCfg.hwInfo.cpuArch != "x86":
				raise Exception("can not install an Windows X86 version on architecture %s"%(vmCfg.hwInfo.cpuArch))
		elif osInfo.arch == "X86_64":
			if vmCfg.hwInfo.cpuArch != "amd64":
				raise Exception("can not install an Windows X86_64 version on architecture %s"%(vmCfg.hwInfo.cpuArch))
		else:
                        assert False

		if vmCfg.hwInfo.memorySize < 1024:
			raise Exception("require at least 1GB memory")

		if vmCfg.hwInfo.mainDiskSize < 16000:
			raise Exception("require at least 16GB main disk size")

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
			elif ftype == "serial":
				return os.path.join(self.dataDir, "cn_windows_7_ultimate_with_sp1_serial.txt")
			elif ftype == "autounattend":
				return os.path.join(self.dataDir, "autounattend.xml.in")
			else:
				assert False

		if osName == "Microsoft.Windows.7.Ultimate.SP1.X86_64.zh_CN":
			if ftype == "iso":	
				return os.path.join(self.dataDir, "cn_windows_7_ultimate_with_sp1_x64_dvd_u_677408.iso")
			elif ftype == "serial":
				return os.path.join(self.dataDir, "cn_windows_7_ultimate_with_sp1_serial.txt")
			elif ftype == "autounattend":
				return os.path.join(self.dataDir, "autounattend.xml.in")
			else:
				assert False
		
		assert False

	def _createAssistantFloppy(self):
	
		# create floppy file
		floppyFile = os.path.join(self.tmpDir, "floppy.img")
		FvmUtil.createFormattedFloppy(floppyFile)

		# add autounattend script
		uatFile = os.path.join(self.tmpDir, "autounattend.xml")
		self._generateUnattendXmlScript(uatFile)
		FvmUtil.copyToFloppy(floppyFile, uatFile)

		return floppyFile

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
			FvmUtil.shell('/bin/cp \"%s\" \"%s\"'%(os.path.join(self.dataDir, "autoinst-spice-guest-tools.au3"), mountPoint))

			# add install_driver.bat
			tmpf = os.path.join(self.tmpDir, "install_driver.bat")
			self._generateInstallDriverBat(os.path.join(mountPoint, tmpf))
			FvmUtil.shell('/bin/cp \"%s\" \"%s\"'%(tmpf, mountPoint))
			os.remove(tmpf)

			# add autorun.inf, to dismiss the AutoPlay dialog
			tmpf = os.path.join(self.tmpDir, "autorun.inf")
			FvmUtil.createAutoRunInfFile(tmpf)
			FvmUtil.shell('/bin/cp \"%s\" \"%s\"'%(tmpf, mountPoint))
			os.remove(tmpf)
		finally:
			# unmount usb file
			FvmUtil.shell('/usr/bin/fusermount -u \"%s\"'%(mountPoint))

		return usbFile

	def _generateUnattendXmlScript(self, uatFile):

		# read template
		uatTemplateFile = self._getFile(self.osName, "autounattend")
		buf = FvmUtil.readFile(uatTemplateFile)

		# replace content
		buf = buf.replace("@@arch@@", self._getArch())
		buf = buf.replace("@@lang@@", self._getLang())
		buf = buf.replace("@@username@@", "A")
		buf = buf.replace("@@password@@", "")
		buf = buf.replace("@@serial_id@@", self._getSerial())
		buf = buf.replace("@@timezone@@", self._getTimezone())

		# write file
		FvmUtil.writeFile(uatFile, buf)

	def _getSerial(self):
		serialFile = self._getFile(self.osName, "serial")
		buf = FvmUtil.readFile(serialFile)
		return buf.split("\n")[0]

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
	def createFormattedFloppy(floppyfile):
		"""create a 1.44M floppy disk with DOS format"""
	
		FvmUtil.createFile(floppyfile, 1440 * 1024)
		FvmUtil.shell('/sbin/mkfs.msdos \"%s\"'%(floppyfile), "stdout")

	@staticmethod
	def copyToFloppy(floppyfile, srcfile):
		"""can not deal with wildcards"""

		FvmUtil.shell('/usr/bin/mcopy -i \"%s\" \"%s\" ::'%(floppyfile, srcfile), "stdout")

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
		buf = ""
		buf += "[AutoRun]\r\n"
		buf += "UseAutoPlay=0"
		if command is not None:
			buf += "open=\"%s\"\r\n"%(command)
		buf += "\r\n"
		buf += "[Content]\r\n"
		buf += "MusicFiles=false\r\n"
		buf += "PictureFiles=false\r\n"
		buf += "VideoFiles=false\r\n"
		FvmUtil.writeFile(infFile, buf)
