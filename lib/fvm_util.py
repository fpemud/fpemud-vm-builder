#!/usr/bin/python2
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import re
import shutil
import subprocess
import fcntl
import select
import time
import struct
import socket
import hivex
import ConfigParser

class FvmUtil:

	@staticmethod
	def getSysctl(name):
		msg = FvmUtil.shell("/sbin/sysctl -n %s"%(name), "stdout")
		return msg.rstrip('\n')

	@staticmethod
	def setSysctl(name, value):
		return

	@staticmethod
	def getCpuNumber():
		"""returns cpu number"""
		return int(FvmUtil.shell("/usr/bin/grep -c ^processor /proc/cpuinfo", "stdout"))

	@staticmethod
	def getArch():
		"""returns arch"""
		ret = FvmUtil.shell("/usr/bin/uname -m", "stdout")
		ret = ret.rstrip('\n')
		if ret == "x86_64":
			return "amd64"
		else:
			return ret

	@staticmethod
	def getMemorySize():
		"""returns physical memory size, in MB"""
		return int(FvmUtil.shell("/usr/bin/grep \"^MemTotal:\" /proc/meminfo | grep -oE \"[0-9]+\"", "stdout")) / 1024

	@staticmethod
	def copyToDir(srcFilename, dstdir, mode=None):
		"""Copy file to specified directory, and set file mode if required"""

		if not os.path.isdir(dstdir):
			os.makedirs(dstdir)
		fdst = os.path.join(dstdir, os.path.basename(srcFilename))
		shutil.copy(srcFilename, fdst)
		if mode is not None:
			FvmUtil.shell("/usr/bin/chmod " + mode + " \"" + fdst + "\"")

	@staticmethod
	def copyToFile(srcFilename, dstFilename, mode=None):
		"""Copy file to specified filename, and set file mode if required"""

		if not os.path.isdir(os.path.dirname(dstFilename)):
			os.makedirs(os.path.dirname(dstFilename))
		shutil.copy(srcFilename, dstFilename)
		if mode is not None:
			FvmUtil.shell("/usr/bin/chmod " + mode + " \"" + dstFilename + "\"")

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
			FvmUtil.shell("/usr/bin/chmod " + mode + " \"" + filename + "\"")

	@staticmethod
	def createFile(filename, size, mode=None):
		"""Create a sparse file, in bytes"""

		if os.path.exists(filename):
			FvmUtil.forceDelete(filename)

		f = open(filename, 'ab')
		f.truncate(size)
		f.close()
		if mode is not None:
			FvmUtil.shell("/usr/bin/chmod " + mode + " \"" + filename + "\"")

	@staticmethod
	def forceDelete(filename):
		if os.path.islink(filename):
			os.remove(filename)
		elif os.path.isdir(filename):
			shutil.rmtree(filename)
		elif os.path.exists(filename):
			os.remove(filename)

	@staticmethod
	def deleteDirContent(dirname):
		shutil.rmtree(dirname)
		os.mkdir(dirname)

	@staticmethod
	def forceSymlink(source, link_name):
		if os.path.exists(link_name):
			os.remove(link_name)
		os.symlink(source, link_name)

	@staticmethod
	def mkDirAndClear(dirname):
		FvmUtil.forceDelete(dirname)
		os.mkdir(dirname)

	@staticmethod
	def touchFile(filename):
		assert not os.path.exists(filename)
		f = open(filename, 'w')
		f.close()

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
				raise Exception("Executing shell command \"%s\" failed, return code %d, output %s"%(cmd, proc.returncode, out))
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
				raise Exception("Executing shell command \"%s\" failed, return code %d, output %s"%(cmd, proc.returncode, out))
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
	def ipMaskToLen(mask):
		"""255.255.255.0 -> 24"""

		netmask = 0
		netmasks = mask.split('.')
		for i in range(0,len(netmasks)):
			netmask *= 256
			netmask += int(netmasks[i])
		return 32 - (netmask ^ 0xFFFFFFFF).bit_length()

	@staticmethod
	def getFreeSocketPort(portType, portStart, portEnd):
		if portType == "tcp":
			sType = socket.SOCK_STREAM
		elif portType == "udp":
			assert False
		else:
			assert False

		for port in range(portStart, portEnd+1):
			s = socket.socket(socket.AF_INET, sType)
			try:
				s.bind((('', port)))
				return port
			except socket.error:
				continue
			finally:
				s.close()
		raise Exception("No valid %s port in [%d,%d]."%(portType, portStart, portEnd))

	@staticmethod
	def isSocketPortBusy(portType, port):
		assert portType == "tcp" or portType == "udp"
		retcode, stdout = FvmUtil.shell("/usr/bin/fuser -n %s %d"%(portType, port), "retcode+stdout")
		return (retcode == 0)

	@staticmethod
	def isPathBusy(path):
		retcode, stdout = FvmUtil.shell('/usr/bin/fuser "%s"'%(path), "retcode+stdout")
		return (retcode == 0)

	@staticmethod
	def fuseUnmountSafe(mountPoint):
		"""FUSE mountpoint may remains busy after all operations for a while, because FUSE daemon needs to do sync operation"""

		while True:
			r, s = FvmUtil.shell('/usr/bin/fusermount -u "%s"'%(mountPoint), "retcode+stdout")
			if r == 0:
				break
			time.sleep(0.5)

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
	def createWinUsbImg(usbFile, size, fsType):
		assert fsType == "ntfs"

		partitionFile = FvmUtil.shell("/usr/bin/mktemp", "stdout").replace("\n", "")
		FvmUtil.createFile(usbFile, size * 1024 * 1024)
		try:
			FvmUtil.shellInteractive('/sbin/fdisk "%s"'%(usbFile), "n\np\n\n\n\nt\n7\nw", "stdout")		# create one NTFS primary partition (system id: 7)

			ret = FvmUtil.shell('/sbin/fdisk -l "%s"'%(usbFile), "stdout")
			m = re.search("([0-9]+) +([0-9]+) +[^ ]+ +7", ret, re.M)				# Start(%d), End(%d), Blocks, Id(7)
			if m is None:
				raise Exception("createWinUsbImg failed, fdisk failed")
			startSector = int(m.group(1))
			offset = int(m.group(1)) * 512
			size = (int(m.group(2)) - int(m.group(1))) * 512

			FvmUtil.shell('/usr/bin/fuseloop -O "%d" -S "%d" "%s" "%s"'%(offset, size, usbFile, partitionFile))
			try:
				FvmUtil.shell('/sbin/mkfs.ntfs -F -Q -s 512 -p %d "%s"'%(startSector, partitionFile), "stdout")
			finally:
				FvmUtil.fuseUnmountSafe(partitionFile)
		except:
			FvmUtil.forceDelete(usbFile)
		finally:
			FvmUtil.forceDelete(partitionFile)

#		FvmUtil.shell('/usr/bin/virt-format --format=raw --partition=mbr --filesystem=ntfs -a "%s"'%(usbFile), "stdout")
#		FvmUtil.shellInteractive('/sbin/fdisk "%s"'%(usbFile), "t\n7\nw", "stdout")	# change partition's system id to NTFS(7)

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
			if i == 2:
				# like "d:\abc"
				return path[:i+1]
			else:
				return path[:i]

	@staticmethod
	def getWinDir(dirType, lang, username=None):
		"""returns path relative to main disk mount point"""

		if username is None:
			username = FvmUtil.getWinUser("cur")

		if dirType == "desktop":
			if lang == "zh_CN":
				return "Documents and Settings/%s/桌面"%(username)
			else:
				return "Documents and Settings/%s/Desktop"%(username)
		elif dirType == "startup":
			if lang == "zh_CN":
				return "Documents and Settings/%s/「开始」菜单/程序/启动"%(username)
			else:
				return "Documents and Settings/%s/Startup Menu/Program/Startup"%(username)
		elif dirType == "quickLaunch":
				return "Documents and Settings/%s/Application Data/Microsoft/Internet Explorer/Quick Launch"%(username)
		else:
			assert False

	@staticmethod
	def getWinUser(userType="cur"):
		if userType == "cur":
			return "Administrator"
		elif userType == "default":
			return "Default User"
		elif userType == "all":
			return "All Users"
		elif userType == "admin":
			return "Administrator"
		else:
			assert False

	@staticmethod
	def getVmOsName(vmInfo):
		osName = None
		for opt in vmInfo.vmCfgWin.os.setupOptList:
			if opt.startswith("os="):
				osName = opt[3:]
		assert osName is not None
		return osName

	@staticmethod
	def getWinLang(osName):
		if osName.endswith(".zh_CN"):
			return "zh_CN"
		else:
			assert False

	@staticmethod
	def getWinArch(osName):
		if ".X86." in osName:
			return "x86"
		elif ".X86_64." in osName:
			return "amd64"
		else:
			assert False

	@staticmethod
	def convertBufToWin(buf, winLang):
		buf = buf.replace("\n", "\r\n")
		if winLang == "zh_CN":
			buf = buf.decode('utf-8').encode('gb2312')
		elif winLang == "zh_TW":
			buf = buf.decode('utf-8').encode('big5')
		return buf

	@staticmethod
	def isWinAbsPath(winPath):
		return winPath[0].isalpha() and winPath[1] == ":" and winPath[2] == "\\"

	@staticmethod
	def winPathToUnixPath(winPath):
		assert FvmUtil.isWinAbsPath(winPath)
		assert winPath[0] == "C" or winPath[0] == "c"
		path = winPath[3:]
		path = path.replace("\\", "/")
		return path

	@staticmethod
	def winPauseAutoActivity(param, mainDiskImage, winLang):
		mptObj = WinDiskMountPoint(param, mainDiskImage, winLang)
		try:
			winreg = WinRegistry(param, mptObj.getMountDir())

			# make backup dir
			backupDir = os.path.join(mptObj.getMountDir(), "BackupAutoShowWindow")
			os.mkdir(backupDir)

			# assert nothing in HKLM/.../RunOnce and HKLM/.../RunOnceEx
			if winreg.exists("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce"):
				assert len(winreg.getValueNameList("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce")) == 0
			if winreg.exists("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnceEx"):
				assert len(winreg.getValueNameList("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnceEx")) == 0

			# backup startup folder if needed
			while True:
				startupDir = os.path.join(mptObj.getMountDir(), FvmUtil.getWinDir("startup", winLang, FvmUtil.getWinUser("cur")))
				if len(os.listdir(startupDir)) == 0 or os.listdir(startupDir) == ["desktop.ini"]:
					break
				startupBakDir = os.path.join(backupDir, "startup")
				os.mkdir(startupBakDir)
				FvmUtil.shell('/usr/bin/cp "%s"/* "%s"'%(startupDir, startupBakDir))		# failed to use /bin/mv, don't know why
				FvmUtil.shell('/usr/bin/unlink "%s"/*'%(startupDir))
				break

			# backup HKLM/.../Run
			if True:
				hklmRunBakFile = os.path.join(backupDir, "hklm_run.reg")
				winreg.exportFile(hklmRunBakFile, "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run")
				winreg.delete("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", "*")

			# backup HKCU/.../Run
			if True:
				hkcuRunBakFile = os.path.join(backupDir, "hkcu_run.reg")
				hasCtfmon = winreg.exists("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", "ctfmon.exe")
				winreg.exportFile(hkcuRunBakFile, "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run")
				winreg.delete("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", "*")
				if hasCtfmon:
					winreg.addOrModify("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", "ctfmon.exe", "REG_SZ", "C:\\WINDOWS\\system32\\ctfmon.exe")

			# backup balloon tips status
			if True:
				value = winreg.getValue("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "EnableBalloonTips", "REG_DWORD")
				if value is not None:
					FvmUtil.shell('/usr/bin/echo "%s" > "%s"'%(value, "EnableBalloonTips"))
				winreg.addOrModify("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "EnableBalloonTips", "REG_DWORD", 0)
		finally:
			mptObj.umount()

	@staticmethod
	def winResumeAutoActivity(param, mainDiskImage, winLang):
		mptObj = WinDiskMountPoint(param, mainDiskImage, winLang)
		try:
			winreg = WinRegistry(param, mptObj.getMountDir())
			backupDir = os.path.join(mptObj.getMountDir(), "BackupAutoShowWindow")

			# resume balloon tips status
			if True:
				if not os.path.exists("EnableBalloonTips"):
					winreg.delete("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "EnableBalloonTips")
				else:
					value = FvmUtil.readFile("EnableBalloonTips")
					winreg.addOrModify("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "EnableBalloonTips", "REG_DWORD", value)

			# resume startup folder if needed
			startupBakDir = os.path.join(backupDir, "startup")
			if os.path.exists(startupBakDir):
				startupDir = os.path.join(mptObj.getMountDir(), FvmUtil.getWinDir("startup", winLang, FvmUtil.getWinUser("cur")))
				desktopIniFile = os.path.join(startupBakDir, "desktop.ini")
				if os.path.exists(desktopIniFile):
					FvmUtil.shell('/usr/bin/unlink "%s"'%(desktopIniFile))
				FvmUtil.shell('/usr/bin/cp "%s"/* "%s"'%(startupBakDir, startupDir))

			# resume HKLM/.../Run
			hklmRunBakFile = os.path.join(backupDir, "hklm_run.reg")
			winreg.importFile(hklmRunBakFile)

			# resume HKCU/.../Run
			hkcuRunBakFile = os.path.join(backupDir, "hkcu_run.reg")
			winreg.importFile(hkcuRunBakFile)

			# remove backupDir
			shutil.rmtree(backupDir)
		finally:
			mptObj.umount()

	@staticmethod
	def loadKernelModule(modname):
		"""Loads a kernel module."""

		FvmUtil.shell("/sbin/modprobe %s"%(modname))

	@staticmethod
	def notInList(srcList, dstList):
		"""Returns the first item in srcList is not in dstList, returns None if no item found."""

		for item in srcList:
			if item not in dstList:
				return item
		return None

	@staticmethod
	def initLog(filename):
		FvmUtil.forceDelete(filename)
		FvmUtil.writeFile(filename, "")

	@staticmethod
	def printLog(filename, msg):
		f = open(filename, 'a')
		if msg != "":
			f.write(time.strftime("%Y-%m-%d %H:%M:%S  ", time.localtime()))
			f.write(msg)
			f.write("\n")
		else:
			f.write("\n")
		f.close()

class WinDiskMountPoint:

	def __init__(self, param, diskFile, winLang):
		"""note: directory 'mountPoint' can only be operated by command and with some restriction after mount"""

		self.param = param
		self.diskFile = diskFile
		self.partitionFile = os.path.join(self.param.tmpDir, "partitionFile")
		self.mountPoint = os.path.join(self.param.tmpDir, "mountPoint")
		self.winLang = winLang

		ret = FvmUtil.shell('/sbin/fdisk -l "%s"'%(self.diskFile), "stdout")
		m = re.search("([0-9]+) +([0-9]+) +[^ ]+ +7", ret, re.M)				# Start(%d), End(%d), Blocks, Id(7)
		if m is None:
			raise Exception("fdisk failed")
		offset = int(m.group(1)) * 512
		size = (int(m.group(2)) - int(m.group(1))) * 512

		try:
			FvmUtil.touchFile(self.partitionFile)
			os.mkdir(self.mountPoint)

			FvmUtil.shell('/usr/bin/fuseloop -O "%d" -S "%d" "%s" "%s"'%(offset, size, self.diskFile, self.partitionFile))
			FvmUtil.shell('/usr/bin/ntfs-3g "%s" "%s" -o no_def_opts,silent'%(self.partitionFile, self.mountPoint))
		except:
			FvmUtil.shell('/usr/bin/fusermount -u "%s"'%(self.mountPoint), "retcode+stdout")
			FvmUtil.forceDelete(self.mountPoint)
			FvmUtil.shell('/usr/bin/fusermount -u "%s"'%(self.partitionFile), "retcode+stdout")
			FvmUtil.forceDelete(self.partitionFile)

	def umount(self):
		FvmUtil.fuseUnmountSafe(self.mountPoint)
		os.rmdir(self.mountPoint)
		FvmUtil.fuseUnmountSafe(self.partitionFile)
		os.remove(self.partitionFile)

	def getMountDir(self):
		return self.mountPoint

	def addAutoIt(self):
		autoitDir = os.path.join(self.mountPoint, "autoit")
		FvmUtil.shell('/usr/bin/mkdir "%s"'%(autoitDir), "stdout")
		FvmUtil.shell('/usr/bin/unzip "%s" -d "%s"'%(os.path.join(self.param.dataDir, "autoit3.zip"), autoitDir), "stdout")
		self.addFile(os.path.join(self.param.dataDir, "FvmUtil.au3"), os.path.join("autoit", "Include"), False)

	def addSevenZip(self):
		dstDir = os.path.join(self.mountPoint, "7zip")
		FvmUtil.shell('/usr/bin/mkdir "%s"'%(dstDir), "stdout")
		FvmUtil.shell('/usr/bin/unzip "%s" -d "%s"'%(os.path.join(self.param.dataDir, "7z920.zip"), dstDir), "stdout")

	def mkdir(self, dstDir):
		"""dstDir is relative to mountPoint"""

		assert not os.path.isabs(dstDir)

		dstDir = os.path.join(self.mountPoint, dstDir)
		FvmUtil.shell('/usr/bin/mkdir "%s"'%(dstDir))

	def addFile(self, srcFile, dstDir, isBinary):
		"""don't support wildcard
		   dstDir is relative to mountPoint"""

		assert not os.path.isabs(dstDir)
		assert os.path.basename(srcFile) != "_tmpfile"

		dstDir = os.path.join(self.mountPoint, dstDir)
		if isBinary:
			FvmUtil.shell('/usr/bin/cp "%s" "%s"'%(srcFile, dstDir))
		else:
			# read and convert the srcFile to a temp file
			buf = FvmUtil.readFile(srcFile)
			buf = FvmUtil.convertBufToWin(buf, self.winLang)
			tmpf = os.path.join(self.param.tmpDir, "_tmpfile")
			FvmUtil.writeFile(tmpf, buf)

			# copy and delete the temp file
			FvmUtil.shell('/usr/bin/cp "%s" "%s"'%(tmpf, os.path.join(dstDir, os.path.basename(srcFile))))
			os.remove(tmpf)

	def addTmpFile(self, tmpf, dstDir, isBinary):
		"""don't support wildcard
		   dstDir is relative to mountPoint"""

		self.addFile(tmpf, dstDir, isBinary)
		os.remove(tmpf)

	def addZipFile(self, srcFile, dstDir):
		"""don't support wildcard
		   dstDir is relative to mountPoint"""

		assert not os.path.isabs(dstDir)

		dstDir = os.path.join(self.mountPoint, dstDir)
		FvmUtil.shell('/usr/bin/unzip "%s" -d "%s"'%(srcFile, dstDir), "stdout")

class WinRegistry:
	"""we can't use hivexregedit because it treat REG_SZ and REG_EXPAND_SZ the same, don't know why it implements like this"""

	valueTypeList = ["", "REG_SZ", "REG_EXPAND_SZ", "REG_BINARY", "REG_DWORD", "REG_DWORD_BIG_ENDIAN",
	                 "REG_LINK", "REG_FULL_RESOURCE_DESCRIPTOR", "REG_RESOURCE_REQUIREMENTS_LIST",
	                 "REG_QWORD"]

	def __init__(self, param, mountPoint):
		self.param = param
		self.mDir = mountPoint

	def addOrModify(self, key, valueName, valueType, value):
		hivefile, key = self._mapPathToHive(self._processKey(key))

		h = hivex.Hivex(hivefile, write=True)
		try:
			node = self._getNodeEnsure(h, key)

			# check type
			while True:
				try:
					val = h.node_get_value(node, valueName)		# raise exception when not found
				except:
					break
				valtype = h.value_type(val)[0]
				assert valueType == self.valueTypeList[valtype]
				break

			# construct val structure
			val = self._valueToRegVal(valueType, value)
			v = { "key": valueName, "t": val[0], "value": val[1] }
			h.node_set_value(node, v)
			h.commit(hivefile)
		finally:
			del h

	def delete(self, key, valueName=None):
		"""if valueName == None, then delete the key
		   if valueName == "*", then delete all the values in key"""

		hivefile, key = self._mapPathToHive(self._processKey(key))

		h = hivex.Hivex(hivefile, write=True)
		try:
			if valueName is None:
				# delete key
				node = self._getNode(h, key)
				assert node is not None
				assert node != h.root()

				h.node_delete_child(node)
			else:
				# delete value
				node = self._getNode(h, key)
				assert node is not None

				values = []
				for i in h.node_values(node):
					if valueName == "*" or valueName == h.value_key(i):
						continue
					val = h.value_value(i)
					v = { "key": h.value_key(i), "t": val[0], "value": val[1] }
					values.append(v)
				h.node_set_values(node, values)

			h.commit(hivefile)
		finally:
			del h

	def exists(self, key, valueName=None):
		hivefile, key = self._mapPathToHive(self._processKey(key))

		h = hivex.Hivex(hivefile, write=False)
		try:
			node = self._getNode(h, key)
			if node is None:
				return False

			if valueName is not None:
				try:
					h.node_get_value(node, valueName)		# raise exception when not found
				except:
					return False

			return True
		finally:
			del h

	def getValue(self, key, valueName, valueType=None):
		"""Returns None if not exist"""

		hivefile, key = self._mapPathToHive(self._processKey(key))

		h = hivex.Hivex(hivefile, write=False)
		try:
			node = self._getNode(h, key)
			if node is None:
				return None

			val = None
			try:
				val = h.node_get_value(node, valueName)
			except:
				return None

			print "debug: getValue " + str(val)

			val = h.value_value(val)

			print "debug2: getValue " + str(val)

			vType, value = self._regValToValue(val)
			if valueType is not None:
				assert valueType == vType

			print "debug3: getValue " + valueType + " " + value

			return value
		finally:
			del h

	def getValueNameList(self, key):
		hivefile, key = self._mapPathToHive(self._processKey(key))

		h = hivex.Hivex(hivefile, write=False)
		try:
			node = self._getNode(h, key)
			assert node is not None

			ret = []
			for i in h.node_values(node):
				ret.append(h.value_key(i))
			return ret
		finally:
			del h

	def exportFile(self, filename, key, valueName=None):
		orikey = key
		hivefile, key = self._mapPathToHive(self._processKey(key))

		h = hivex.Hivex(hivefile, write=False)
		try:
			node = self._getNode(h, key)
			assert node is not None

			cfg = ConfigParser.SafeConfigParser()
			c = 0
			for i in h.node_values(node):
				if valueName is not None and h.value_key(i) != valueName:
					continue
				val = h.value_value(i)
				valueType, value = self._regValToValue(val)

				cfg.add_section("item%d"%(c))
				cfg.set("item%d"%(c), "key", orikey)
				cfg.set("item%d"%(c), "valueName", h.value_key(i))
				cfg.set("item%d"%(c), "valueType", valueType)
				cfg.set("item%d"%(c), "value", value)
				c = c + 1

			cfg.write(open(filename, "w"))					# fixme: file with delimiter '\n' in windows disk
		finally:
			del h

	def importFile(self, filename):
		cfg = ConfigParser.SafeConfigParser()
		cfg.read(filename)
		for secName in cfg.sections():
			key = cfg.get(secName, "key")
			valueName = cfg.get(secName, "valueName")
			valueType = cfg.get(secName, "valueType")
			value = cfg.get(secName, "value")
			self.addOrModify(key, valueName, valueType, value)

	def _processKey(self, key):
		if key.startswith("HKLM\\"):
			return key
		if key.startswith("HKEY_LOCAL_MACHINE\\"):
			return key.replace("HKEY_LOCAL_MACHINE\\", "HKLM\\", 1)

		if key.startswith("HKCU\\"):
			return key.replace("HKCU\\", "HKU\\%s\\"%(FvmUtil.getWinUser()), 1)
		if key.startswith("HKEY_CURRENT_USER\\"):
			return key.replace("HKEY_CURRENT_USER\\", "HKU\\%s\\"%(FvmUtil.getWinUser()), 1)

		assert False

	def _valueToRegVal(self, valueType, value):
		"""returns (valTypeId, val)"""

		typeId = self.valueTypeList.index(valueType)
		if valueType == "REG_DWORD":
			assert isinstance(value, int)
			val = struct.pack("<I", value)
		elif valueType == "REG_SZ":
			assert isinstance(value, str)
			val = value.encode("utf_16_le")
		elif valueType == "REG_EXPAND_SZ":
			assert isinstance(value, str)
			val = value.encode("utf_16_le")
		else:
			assert False

		return (typeId, val)

	def _regValToValue(self, val):
		"""returns (valueType, value)"""

		valueType = self.valueTypeList[val[0]]
		if valueType == "REG_DWORD":
			value = struct.unpack("<I", val[1])[0]
		elif valueType == "REG_SZ":
			value = val[1].decode("utf_16_le")
		elif valueType == "REG_EXPAND_SZ":
			value = val[1].decode("utf_16_le")
		else:
			assert False

		return (valueType, value)

	def _mapPathToHive(self, key):
		"""Copied from /usr/bin/virt-win-reg, only support windows NT currently"""

		hivefile = None
		k = None

		if key.startswith("HKLM\\SAM\\"):
			hivefile = "WINDOWS/system32/config/sam"
			k = key.replace("HKLM\\SAM\\", "", 1)
		if key.startswith("HKLM\\SECURITY\\"):
			hivefile = "WINDOWS/system32/config/security"
			k = key.replace("HKLM\\SECURITY\\", "", 1)
		if key.startswith("HKLM\\SOFTWARE\\"):
			hivefile = "WINDOWS/system32/config/software"
			k = key.replace("HKLM\\SOFTWARE\\", "", 1)
		if key.startswith("HKLM\\SYSTEM\\"):
			hivefile = "WINDOWS/system32/config/system"
			k = key.replace("HKLM\\SYSTEM\\", "", 1)
		if key.startswith("HKLM\\.DEFAULT\\"):
			hivefile = "WINDOWS/system32/config/default"
			k = key.replace("HKLM\\.DEFAULT\\", "", 1)

#		if key.startswith("HKU\\LocalSystem\\")):
#			sid = "S-1-5-18"
#			hivefile = self._lookupPipOfUserSid($sid) + "/NTUSER.DAT";
#		if key.startswith("HKU\\LocalService\\")):
#			sid = "S-1-5-19"
#			hivefile = self._lookupPipOfUserSid($sid) + "/NTUSER.DAT";
#		if key.startswith("HKU\\NetworkService\\")):
#			sid = "S-1-5-20"
#			hivefile = self._lookupPipOfUserSid($sid) + "/NTUSER.DAT";
#
#		m = re.search("^HKU\\(S-1-5-[0-9]+)\\", key)
#		if m:
#			sid = m.group(1)
#			hivefile = self._lookupPipOfUserSid(sid) + "/NTUSER.DAT";

		m = re.search("^HKU\\\\(.*?)\\\\", key)
		if m:
			uname = m.group(1)
			if os.path.isdir(os.path.join(self.mDir, "Users", uname)):
				hivefile = os.path.join("Users", uname, "NTUSER.DAT")
			elif os.path.isdir(os.path.join(self.mDir, "Documents and Settings", uname)):
				hivefile = os.path.join("Documents and Settings", uname, "NTUSER.DAT")
			else:
				assert False
			k = key.replace(m.group(0), "", 1)

		assert hivefile is not None
		assert k is not None
		return (os.path.join(self.mDir, hivefile), k)

	def _getNodeEnsure(self, h, nodePath):
		"""Get or create node, always return a valid node"""

		node = h.root()
		for i in nodePath.split("\\"):
			node2 = h.node_get_child(node, i)
			if node2 is not None:
				node = node2
			else:
				node = h.node_add_child(node, i)
		return node

	def _getNode(self, h, nodePath):
		"""Get node, returns None if not found"""

		node = h.root()
		for i in nodePath.split("\\"):
			node = h.node_get_child(node, i)
			if node is None:
				return None
		return node

class WinDesktopItemBackup:
	class _ItemInfoFile:
		filename = None			# str

	class _ItemInfoRegistry:
		key = None				# str
		valueName = None		# str | None

	def __init__(self, appPluginName):
		self.appPluginName = appPluginName
		self.itemInfoDict = dict()
		self.itemStateDict = dict()

		self.param = None
		self.mainDiskDir = None
		self.backupDir = None

	def addItemInfo(self, itemName, itemType, *args):
		assert self.mainDiskDir is None

		itemInfo = None
		if itemType == "file":
			assert len(args) == 1
			assert not os.path.isabs(args[0])
			itemInfo = self._ItemInfoFile()
			itemInfo.filename = args[0]
		elif itemType == "registry":
			assert len(args) == 2
			itemInfo = self._ItemInfoRegistry()
			itemInfo.key = args[0]
			itemInfo.valueName = args[1]
		else:
			assert False

		if itemName in self.itemInfoDict:
			self.itemInfoDict[itemName].append(itemInfo)
		else:
			self.itemInfoDict[itemName] = [itemInfo]

	def getItemNameList(self):
		return self.itemInfoDict.keys()

	def initBackup(self, param, mainDiskDir):
		self.param = param
		self.mainDiskDir = mainDiskDir
		self.backupDir = os.path.join(self.mainDiskDir, "DesktopBackup", self.appPluginName)
		winreg = WinRegistry(self.param, self.mainDiskDir)

		if not os.path.exists(os.path.join(mainDiskDir, "DesktopBackup")):
			os.mkdir(os.path.join(mainDiskDir, "DesktopBackup"))

		FvmUtil.mkDirAndClear(self.backupDir)
		for i in self.itemInfoDict:
			itemDir = os.path.join(self.backupDir, i)
			os.mkdir(itemDir)

			for jc in range(0, len(self.itemInfoDict[i])):
				j = self.itemInfoDict[i][jc]
				if isinstance(j, self._ItemInfoFile):
					fname = os.path.join(self.mainDiskDir, j.filename)
					assert os.path.exists(fname)
					FvmUtil.shell('/usr/bin/cp "%s" "%s"'%(fname, itemDir))		# failed to use /bin/mv, don't know why
					FvmUtil.shell('/usr/bin/unlink "%s"'%(fname))
				elif isinstance(j, self._ItemInfoRegistry):
					fname = os.path.join(itemDir, "%d.reg"%(jc))
					winreg.exportFile(fname, j.key, j.valueName)
					winreg.delete(j.key, j.valueName)
				else:
					assert False
			self.itemStateDict[i] = False

	def syncBackup(self, param, mainDiskDir):
		self.param = param
		self.mainDiskDir = mainDiskDir
		self.backupDir = os.path.join(self.mainDiskDir, "DesktopBackup", self.appPluginName)
		winreg = WinRegistry(self.param, self.mainDiskDir)

		for i in self.itemInfoDict:
			itemDir = os.path.join(self.backupDir, i)
			assert os.path.exists(itemDir)

			s = True
			for j in self.itemInfoDict[i]:
				if isinstance(j, self._ItemInfoFile):
					fname = os.path.join(self.mainDiskDir, j.filename)
					s = s and os.path.exists(fname)
				elif isinstance(j, self._ItemInfoRegistry):
					s = s and winreg.exists(j.key, j.valueName)
				else:
					assert False
			self.itemStateDict[i] = s

	def getItemState(self, itemName):
		assert self.mainDiskDir is not None
		return self.itemStateDict[itemName]

	def setItemState(self, itemName, state):
		assert self.mainDiskDir is not None

		winreg = WinRegistry(self.param, self.mainDiskDir)
		i = itemName
		itemDir = os.path.join(self.backupDir, i)
		for jc in range(0, len(self.itemInfoDict[i])):
			j = self.itemInfoDict[i][jc]
			if isinstance(j, self._ItemInfoFile):
				fname = os.path.join(self.mainDiskDir, j.filename)
				if state:
					FvmUtil.shell('/usr/bin/cp "%s" "%s"'%(os.path.join(itemDir, os.path.basename(fname)), fname))
				else:
					FvmUtil.shell('/usr/bin/unlink "%s"'%(fname))
			elif isinstance(j, self._ItemInfoRegistry):
				if state:
					fname = os.path.join(itemDir, "%d.reg"%(jc))
					winreg.importFile(fname)
				else:
					winreg.delete(j.key, j.valueName)
			else:
				assert False
		self.itemStateDict[i] = state

class InfoPrinter:

	GOOD = '\033[32;01m'
	WARN = '\033[33;01m'
	BAD = '\033[31;01m'
	NORMAL = '\033[0m'
	BOLD = '\033[0;01m'
	UNDER = '\033[4m'

	def __init__(self):
		self.logFileList = []
		self.indent = 0

	def addLogFile(self, logFile):
		assert logFile not in self.logFileList
		self.logFileList.append(logFile)

	def incIndent(self):
		self.indent = self.indent + 1

	def decIndent(self):
		assert self.indent > 0
		self.indent = self.indent - 1

	def printInfo(self, s):
		line = ""
		line += self.GOOD + "*" + self.NORMAL + " "
		line += "\t" * self.indent
		line += s
		print line

class PopenStdio:
	def __init__(self, proc, logFile=None):
		assert proc.stdin is not None
		assert proc.stdout is not None

		self.proc = proc
		fl = fcntl.fcntl(proc.stdout.fileno(), fcntl.F_GETFL)  
		fcntl.fcntl(proc.stdout.fileno(), fcntl.F_SETFL, fl | os.O_NONBLOCK)  

		if logFile is not None:
			self.logf = open(logFile, "a")

		self.readBuf = ""

	def read(self):
		assert self.proc is not None

		self._read()
		ret = self.readBuf
		self.readBuf = ""
		return ret

	def write(self, msg):
		assert self.proc is not None

		self._read()
		self._write(msg)

	def close(self):
		"""this function can be omitted if no logFile specified"""

		self.readBuf = ""
		if self.logf is not None:
			self.logf.close()
			self.logf = None
		self.proc = None

	def _read(self):
		infds_c,outfds_c,errfds_c = select.select([self.proc.stdout,],[],[],0.1)
		if len(infds_c) > 0:
			msg = self.proc.stdout.read()
			if self.logf is not None:
				self.logf.write(msg)
				self.logf.flush()
			self.readBuf += msg

	def _write(self, msg):
		if self.logf is not None:
			self.logf.write(msg)
			self.logf.flush()
		self.proc.stdin.write(msg)

class CfgOptUtil:

	@staticmethod
	def getOptInOptList(optList, prefix):
		for ni in optList:
			if ni.startswith(prefix):
				return ni
		return None

	@staticmethod
	def mergeCfgOpt(srcList, newList, prefix):
		"""Add or replace option, support multiple 'preifx' in 'newList'."""

		retList = list(srcList)
		for ni in newList:
			if not ni.startswith(prefix):
				continue

			found = False
			for i in range(0, len(retList)):
				if retList[i].startswith(prefix):
					retList[i] = ni
					found = True
					break
			if not found:
				retList.append(ni)

		return retList

	@staticmethod
	def mergeCfgOptWithSubValue(srcList, newList, prefix):
		"""Add or modify value of option, support multiple 'preifx' in 'newList'."""

		retList = list(srcList)
		for ni in newList:
			if not ni.startswith(prefix):
				continue

			found = False
			for i in range(0, len(retList)):
				if retList[i].startswith(prefix):
					sValues = retList[i][len(prefix):].split(";")
					nValues = ni[len(prefix):].split(";")
					rValues = list(set(sValues + nValues))
					retList[i] = "%s%s"%(prefix, ";".join(rValues))
					found = True
			if not found:
				retList.append(ni)

		return retList

	@staticmethod
	def mergeCfgOptWithSubKeyValue(srcList, newList, prefix):
		"""Add or modify key-value of option, support multiple 'preifx' in 'newList'."""

		retList = list(srcList)
		for ni in newList:
			if not ni.startswith(prefix):
				continue

			found = False
			for i in range(0, len(retList)):
				if retList[i].startswith(prefix):
					sKv = CfgOptUtil._valuePairListToDict(retList[i][len(prefix):].split(";"))
					nKv = CfgOptUtil._valuePairListToDict(ni[len(prefix):].split(";"))
					rKv = dict(sKv.items() + nKv.items())
					retList[i] = "%s%s"%(prefix, ";".join(CfgOptUtil._dictToValuePairList(rKv)))
					found = True
			if not found:
				retList.append(ni)

		return retList

	@staticmethod
	def mergeCfgOptWithKeyAdd(srcList, newList, prefix):
		"""Add a new key, support multiple 'preifx' in 'newList'."""

		retList = list(srcList)
		for ni in newList:
			if not ni.startswith(prefix):
				continue

			if ni not in retList:
				retList.append(ni)

		return retList

	@staticmethod
	def _valuePairListToDict(valuePairList):
		ret = dict()
		for vp in valuePairList:
			ret[vp.split(":")[0]] = vp.split(":")[1]
		return ret

	@staticmethod
	def _dictToValuePairList(theDict):
		ret = []
		for k, v in theDict.items():
			assert ":" not in k and ":" not in v
			ret.append("%s:%s"%(k, v))
		return ret


