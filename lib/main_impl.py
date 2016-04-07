#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import sys
from fvm_util import FvmUtil
from fvm_util import InfoPrinter
from fvm_plugin import FvmWorkFullControl
from fvm_worklist_executor import FvmWorkListExecutor
from fvm_vm_fqemu import FvmVmFqemuBuilder
from fvm_vm_fqemu import FvmVmFqemuObject
from fvm_vm_fqemu import FvmVmFqemuConfigBasic


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
            self.infoPrinter.printInfo("Creating virtual machine in directory \"%s\"..." % (self.args.vmdir))
            self.infoPrinter.incIndent()

            vmCfgBasic = self._getVmCfgBasicByArgs(self.args)
            vmCfgHw = pObj.getVmCfgHw(self.param, self.args.popt)                # fixme: should return hardware spec
            vmCfgBasic.checkValid()
            vmCfgHw.checkValid()

            vb = FvmVmFqemuBuilder(self.param)
            vb.createVm(self.args.vmdir, vmCfgBasic, vmCfgHw)

            self.infoPrinter.decIndent()
            self.infoPrinter.printInfo("Complete!")

            # open vmObj and run os setup
            self.infoPrinter.printInfo("Doing \"%s\" setup..." % (pObj.getOsName()))
            self.infoPrinter.incIndent()

            vmObj = FvmVmFqemuObject(self.param, self.args.vmdir)
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
                    obj = None
                    exec("import plugin_%s" % (pluginName))
                    exec("obj = plugin_%s.PluginObject(\"%s\")" % (pluginName, pDataDir))
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
        ret = FvmVmFqemuConfigBasic()
        ret.name = os.path.basename(args.vmdir)
        ret.title = os.path.basename(args.title)
        ret.description = args.description
        return ret

    def _changeVmCfgWinForOsSetup(self, vmObj, pluginName, optList):
        vmCfgWin = vmObj.getVmInfo().vmCfgWin
        vmCfgWin.os.pluginName = pluginName
        vmCfgWin.os.setupOptList = optList
        vmObj.setVmCfgWin(vmCfgWin)
