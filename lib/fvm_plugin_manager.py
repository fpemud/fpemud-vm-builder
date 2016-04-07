#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import sys

class FvmPluginManager:
	"""There're 2 types of plugin: os-plugin, app-plugin"""

    def __init__(self, param):
		self.param = param

	def getPluginList(self, pluginType):
		"""Returns plugin name list"""

		assert pluginType == "os" or pluginType == "app"

		ret = []
		for pName in os.listdir(self.param.pluginDir):
			pDir = os.path.join(self.param.pluginDir, pName)
			if os.path.exists(os.path.join(pDir, "%s_plugin_%s.py"%(pluginType, self._moduleName(pName)))):
				ret.append(pName)
		return ret

	def getPluginObjByType(self, pluginType, pluginName):
		"""Returns None when not found"""

		assert pluginType == "os" or pluginType == "app"

		pDir = os.path.join(self.param.pluginDir, pluginName)
		pDataDir = os.path.join(self.param.pluginDataDir, pluginName)

		if not os.path.exists(os.path.join(pDir, "%s_plugin_%s.py"%(pluginType, self._moduleName(pluginName)))):
			return None

		tmp = sys.path
		sys.path.append(pDir)
		exec "import %s_plugin_%s"%(pluginType, self._moduleName(pluginName))
		exec "ret = %s_plugin_%s.PluginObject(\"%s\")"%(pluginType, self._moduleName(pluginName), pDataDir)
		sys.path = tmp

		return ret

	def getPluginObj(self, pluginName):
		"""Returns None when not found"""

		pDir = os.path.join(self.param.pluginDir, pluginName)
		pDataDir = os.path.join(self.param.pluginDataDir, pluginName)

		if os.path.exists(os.path.join(pDir, "os_plugin_%s.py"%(self._moduleName(pluginName)))):
			pluginType = "os"
		elif os.path.exists(os.path.join(pDir, "app_plugin_%s.py"%(self._moduleName(pluginName)))):
			pluginType = "app"
		else:
			return None

		tmp = sys.path
		sys.path.append(pDir)
		exec "import %s_plugin_%s"%(pluginType, self._moduleName(pluginName))
		exec "ret = %s_plugin_%s.PluginObject(\"%s\")"%(pluginType, self._moduleName(pluginName), pDataDir)
		sys.path = tmp

		return ret

	def _moduleName(self, pluginName):
		return pluginName.replace("-", "_")
