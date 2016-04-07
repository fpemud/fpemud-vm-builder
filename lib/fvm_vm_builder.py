#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import shutil
from xml.dom import minidom
from fvm_util import FvmUtil
from fvm_param import FvmConfigWin

class FvmVmBuilder:

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

			vmCfgWin = FvmConfigWin()
			vmCfgWin.writeToDisk(os.path.join(vmDir, "fqemu.win"))

			FvmUtil.touchFile(os.path.join(vmDir, "setup.mode"))
		except:
			if os.path.exists(vmDir):
				shutil.rmtree(vmDir)
			raise

