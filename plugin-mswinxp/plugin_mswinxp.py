#!/usr/bin/python
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
from fvm_util import FvmUtil
from fvm_util import WinDiskMountPoint
from fvm_util import WinRegistry
from fvm_util import CfgOptUtil
from fvm_vm_fqemu import FvmVmFqemuConfigHardware
from fvm_plugin import FvmPlugin
from fvm_plugin import FvmWorkFullControl
from fvm_plugin import FvmWorkOnLineExec


class PluginObject(FvmPlugin):

    def __init__(self, dataDir):
        self.dataDir = dataDir

    def getOsNames(self):
        return [
            "Microsoft.Windows.XP.Professional.SP3.X86.zh_CN",
            "Microsoft.Windows.XP.Professional.SP1.X86_64.zh_CN",
        ]

    def getVmCfgHw(self, param, optList):
        """minimal requirement:
             128M mem, 1.5G disk
           pci slot allcation:
             slot 0x04:        graphics adapter
             slot 0x05:        sound adapter
             slot 0x06:        network adapter
             slot 0x07:        balloon device
             slot 0x08:        vdi-port device"""

        osName = optList[0][3:]

        vmCfgHw = FvmVmFqemuConfigHardware()
        vmCfgHw.qemuVmType = "pc"
        vmCfgHw.cpuArch = FvmUtil.getWinArch(osName)
        vmCfgHw.cpuNumber = 1
        vmCfgHw.memorySize = 1024                # fixme

        if FvmUtil.getWinArch(osName) == "x86":
            vmCfgHw.mainDiskInterface = "virtio-blk"
        elif FvmUtil.getWinArch(osName) == "amd64":
            vmCfgHw.mainDiskInterface = "ide"        # winxp amd64 has no virtio block device driver
        else:
            assert False
        vmCfgHw.mainDiskFormat = "raw-sparse"
        vmCfgHw.mainDiskSize = 30 * 1024            # fixme

        vmCfgHw.graphicsAdapterInterface = "qxl"        # fixme
        vmCfgHw.graphicsAdapterPciSlot = 0x04

        vmCfgHw.soundAdapterInterface = "ac97"            # fixme
        vmCfgHw.soundAdapterPciSlot = 0x05

        vmCfgHw.networkAdapterInterface = "virtio"        # fixme
        vmCfgHw.networkAdapterPciSlot = 0x06

        vmCfgHw.balloonDeviceSupport = True            # fixme
        vmCfgHw.balloonDevicePciSlot = 0x07

        vmCfgHw.vdiPortDeviceSupport = True            # fixme
        vmCfgHw.vdiPortDevicePciSlot = 0x08

        vmCfgHw.shareDirectoryNumber = 0
        vmCfgHw.shareDirectoryHotplugSupport = False
        vmCfgHw.shareUsbNumber = 0
        vmCfgHw.shareUsbHotplugSupport = False
        vmCfgHw.shareScsiNumber = 0
        vmCfgHw.shareScsiHotplugSupport = False

        return vmCfgHw

    def doSetup(self, param, vmInfo, optList):
        # parse optList
        osName = None
        for opt in optList:
            if opt.startswith("os="):
                osName = opt[3:]
            else:
                raise Exception("invalid option: %s" % (opt))

        # check vmCfg
        self._checkVmCfg(vmInfo, osName)

        # generate and return FvmWork object list
        workList = []

        work = OsSetupWork(self.dataDir, osName)
        workList.append(work)

        work = BasicPrepareWork(self.dataDir, osName)
        workList.append(work)

        work = DriverInstallWork(self.dataDir, osName)
        workList.append(work)

        work = DriverUpdateWork(self.dataDir, osName)
        workList.append(work)

        return workList

    def doInitialConfigure(self, param, vmInfo):
        self._checkOsPlugin(vmInfo)
        osName = FvmUtil.getVmOsName(vmInfo)

        workList = []

        work = FvmWorkOnLineExec()
        work.setWorkName("Enable auto update")
        work.setExecFileInfo(os.path.join(self.dataDir, "autocfg-enable-auto-update.au3"))
        workList.append(work)

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure input method")
        work.setExecFileInfo(os.path.join(self.dataDir, "autocfg-init-input-method.au3"))
        workList.append(work)

        work = FvmWorkOnLineExec()
        work.setWorkName("Update windows installer")
        work.addFile(os.path.join(self.dataDir, "WindowsXP-KB942288-v3-x86.exe"), True)
        work.setExecFileInfo(os.path.join(self.dataDir, "autocfg-update-windows-installer.au3"))
        workList.append(work)

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure Windows Media Player 9")
        work.setExecFileInfo(os.path.join(self.dataDir, "autocfg-init-wmp9.au3"))
        work.setReqList(["noNetwork"])
        workList.append(work)

        work = FvmWorkOnLineExec()
        work.setWorkName("Install Internet Explorer 8")
        if osName.endswith(".X86.zh_CN"):
            work.addFile(os.path.join(self.dataDir, "IE8-WindowsXP-x86-CHS.exe"), True)
        else:
            assert False
        work.setExecFileInfo(os.path.join(self.dataDir, "autocfg-init-ie8.au3"))
        work.setReqList(["noNetwork", "rebootAndShutdown"])                    # noNetwork can quicken the installation
        # IE8 setup program needs rebooting
        workList.append(work)

        return workList

    def doPauseAutoShowWindow(self, param):
        assert False

    def doResumeAutoShowWindow(self, param):
        assert False

    def _checkVmCfg(self, vmInfo, osName):
        if FvmUtil.getWinArch(osName) != vmInfo.vmCfgHw.cpuArch:
            raise Exception("unmatch Windows architecture and CPU architecture")

        if vmInfo.vmCfgHw.memorySize < 128:
            raise Exception("require at least 128MB memory")

        if vmInfo.vmCfgHw.mainDiskSize < 1500:
            raise Exception("require at least 1.5GB main disk size")

    def _checkOsPlugin(self, vmInfo):
        if vmInfo.vmCfgWin.os.pluginName != "winxp":
            raise Exception("virtual machine is not created by plugin winxp")

    def _doJobSetScreenResolution(self, opt, value):
        resList = ["800x600", "832x624", "960x640", "1024x600", "1024x768", "1152x864", "1152x870", "1280x720", "1280x760",
                   "1280x768", "1280x800", "1280x960", "1280x1024", "1360x768", "1366x768", "1400x1050", "1440x900", "1600x900",
                   "1600x1200", "1680x1050", "1920x1080", "1920x1200", "1920x1440", "2048x1536", "2560x1440", "2560x1600",
                   "2560x2048", "2800x2100", "3200x2400"]
        if value not in resList:
            raise Exception("invalid option \"%s\", the specified screen-resolution value is invalid" % (opt))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure screen resolution")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-screen-resolution.au3"), [value])
        return work

    def _doJobSetExplorerView(self, opt, value):
        viewList = ["default", "thumbnail", "title", "icon", "list", "detail"]
        if value not in viewList:
            raise Exception("invalid option \"%s\", the speicified view is invalid" % (opt))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure explorer view")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-explorer-view.au3"), [value])
        return work

    def _doJobSetExplorerOption(self, value):
        optList = ["file-ext:show", "file-ext:hide", "hidden-file:show", "hidden-file:hide", "extra-tip:show", "extra-tip:hide"]
        valueList = value.split(";")

        o = FvmUtil.notInList(valueList, optList)
        if o is not None:
            raise Exception("invalid option \"%s\"" % (o))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure explorer option")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-explorer-option.au3"), valueList)
        return work

    def _doJobSetExplorerSearchOption(self, value):
        optList = ["balloon-prompt:on", "balloon-prompt:off", "auto-completion:on", "auto-completion:off",
                   "animation:on", "animation:off", "indexing:on", "indexing:off"]
        valueList = value.split(";")

        o = FvmUtil.notInList(valueList, optList)
        if o is not None:
            raise Exception("invalid option \"%s\"" % (o))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure explorer search option")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-explorer-search-option.au3"), valueList)
        return work

    def _doJobSetDesktopTheme(self, value):
        work = FvmWorkOnLineExec()
        work.setWorkName("Configure desktop theme")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-desktop-theme.au3"), [value])
        return work

    def _doJobSetDesktopPerformance(self, value):
        if value != "effect" and value != "speed":
            raise Exception("invalid option value \"%s\", must be \"effect|speed\"" % (value))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure desktop performance")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-desktop-performance.au3"), [value])
        return work

    def _doJobSetDesktopOption(self, value):
        optList = ["sort-icon:on", "sort-icon:off"]
        valueList = value.split(";")

        o = FvmUtil.notInList(valueList, optList)
        if o is not None:
            raise Exception("invalid option \"%s\"" % (o))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure desktop option")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-desktop-option.au3"), valueList)
        return work

    def _doJobSetStartMenuOption(self, value):
        optList = ["style:winxp", "style:classic", "auto-hide:on", "auto-hide:off", "inactive-tray-icon:show", "inactive-tray-icon:hide",
                   "group-task:on", "group-task:off", "quick-bar:on", "quick-bar:off", "balloon-tips:on", "balloon-tips:off"]
        valueList = value.split(";")

        o = FvmUtil.notInList(valueList, optList)
        if o is not None:
            raise Exception("invalid option \"%s\"" % (o))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure start menu option")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-start-menu-option.au3"), valueList)
        return work

    def _doJobSetIeMainPage(self, value):
        work = FvmWorkOnLineExec()
        work.setWorkName("Configure Internet Explorer main page")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-ie-main-page.au3"), [value])
        return work

    def _doJobSetWmpOption(self, value):
        optList = ["minimize-to-taskbar:on", "minimize-to-taskbar:off"]
        valueList = value.split(";")

        o = FvmUtil.notInList(valueList, optList)
        if o is not None:
            raise Exception("invalid option \"%s\"" % (o))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure Windows Media Player")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-wmp-option.au3"), [value])
        return work

    def _doJobSetControlPanelStyle(self, value):
        if value != "category" and value != "classic":
            raise Exception("invalid option value \"%s\", must be \"category|classic\"" % (value))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure explorer search option")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-control-panel-style.au3"), [value])
        return work

    def _doJobSetErrorReport(self, value):
        if value != "enable" and value != "disable":
            raise Exception("invalid option value \"%s\", must be \"enable|disable\"" % (value))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure explorer search option")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-error-report.au3"), [value])
        return work

    def _doJobSetTaskmgrOption(self, value):
        optList = ["auto-start:on", "auto-start:off", "hide-when-minimized:on", "hide-when-minimized:off"]
        valueList = value.split(";")

        o = FvmUtil.notInList(valueList, optList)
        if o is not None:
            raise Exception("invalid option \"%s\"" % (o))

        work = FvmWorkOnLineExec()
        work.setWorkName("Configure Task Manager")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-set-taskmgr-option.au3"), valueList)
        return work

    def _doJobInstallPatch(self, osName, value):
        workList = []
        for vi in value.split(";"):
            if vi == "wmp11":
                work = FvmWorkOnLineExec()
                work.setWorkName("Install Windows Media Player 11")
                if osName.endswith(".X86.zh_CN"):
                    work.addFile(os.path.join(self.dataDir, "wmp11-windowsxp-x86-ZH-CN.exe"), True)
                else:
                    assert False
                work.setExecFileInfo(os.path.join(self.dataDir, "cfg-install-wmp11.au3"))
                work.setReqList(["noNetwork"])
            elif vi == "flash-player":
                work = FvmWorkOnLineExec()
                work.setWorkName("Install Flash Player")
                work.addFile(os.path.join(self.dataDir, "install_flash_player.exe"), True)
                work.addFile(os.path.join(self.dataDir, "install_flash_player_ax.exe"), True)
                work.setExecFileInfo(os.path.join(self.dataDir, "cfg-install-flash-player.au3"))
                work.setReqList(["noNetwork"])
            elif vi == "jre":
                work = FvmWorkOnLineExec()
                work.setWorkName("Install JRE")
                work.addFile(os.path.join(self.dataDir, "jre-7u17-windows-i586.exe"), True)
                work.addFile(os.path.join(self.dataDir, "jre-7u17-windows-x64.exe"), True)
                work.setExecFileInfo(os.path.join(self.dataDir, "cfg-install-jre.au3"))
                work.setReqList(["noNetwork"])
            elif vi == "dot-net-framework":
                assert False
            elif vi == "directx":
                assert False
            else:
                raise Exception("invalid patch \"%s\"" % (vi))
            workList.append(work)

        return workList

    def _doJobAddDesktopShortcut(self, value):
        rPosition = ""
        rName = ""
        rTarget = ""
        rAccelerator = ""
        for vi in value.split(";"):
            if vi == "position:desktop":
                rPosition = "desktop"
            elif vi == "position:quick-launch-bar":
                assert False
#                rPosition = "quick-launch"
            elif vi.startswith("name:"):
                rName = vi[5:]
            elif vi.startswith("target:"):
                rTarget = vi[7:]
            elif vi.startswith("accelerator:"):
                rAccelerator = vi[12:0]
            else:
                assert False

        if rPosition == "":
            raise Exception("Invalid position value")
        if rName == "":
            raise Exception("Invalid name value")
        if rTarget == "":
            raise Exception("Invalid target value")

        work = FvmWorkOnLineExec()
        work.setWorkName("Add Desktop Shortcut")
        work.setExecFileInfo(os.path.join(self.dataDir, "cfg-add-desktop-shortcut.au3"), [rPosition, rName, rTarget, rAccelerator])
        return work

    def _doJobCheckVirus(self):
        work = FvmWorkOnLineExec()
        work.setWorkName("Check virus")
        work.addZipFile(os.path.join(self.dataDir, "baidusd.zip"))
        work.setExecFileInfo(os.path.join(self.dataDir, "exec-check-virus.au3"))
        work.setReqList(["network"])
        return work


class OsSetupWork(FvmWorkFullControl):

    def __init__(self, dataDir, osName):
        self.workName = "Setup %s" % (osName)
        self.dataDir = dataDir
        self.osName = osName

    def doWork(self, param, vmObj, infoPrinter):
        """do OS setup operation"""

        # prepare parameter
        self.param = param
        self.vmObj = vmObj

        # prepare setup cd
        cdromFile = self._getFile(self.osName, "iso")
        self.vmObj.setLocalCdromImage(cdromFile)

        # prepare assistant floppy
        floppyFile = self._createAssistantFloppy()
        self.vmObj.setLocalFloppyImage(floppyFile)

        # run virtual machine
        self.vmObj.setBootOrder(["cdrom", "mainDisk"])
        self.vmObj.run()

    def _createAssistantFloppy(self):

        # create floppy file
        floppyFile = os.path.join(self.param.tmpDir, "floppy.img")
        FvmUtil.createFormattedFloppy(floppyFile)

        # add autounattend script
        uatFile = os.path.join(self.param.tmpDir, "winnt.sif")
        self._generateUnattendXmlScript(uatFile)
        FvmUtil.copyToFloppy(floppyFile, uatFile)

        return floppyFile

    def _generateUnattendXmlScript(self, uatFile):

        # read template
        uatTemplateFile = self._getFile(self.osName, "autounattend")
        buf = FvmUtil.readFile(uatTemplateFile)

        # replace content
        buf = buf.replace("@@timezone@@", self._getTimezone())
        buf = buf.replace("@@serial_id@@", self._getSerial())
        buf = buf.replace("@@x_resolution@@", "1024")
        buf = buf.replace("@@y_resolution@@", "768")
        buf = buf.replace("@@country_code@@", "86")
        buf = buf.replace("@@area_code@@", "00")
        buf = buf.replace("@@dialing@@", "Tone")
        buf = buf.replace("@@language_group@@", "10")
        buf = buf.replace("@@language@@", "00000804")

        # write file
        FvmUtil.writeFile(uatFile, buf)

    def _getTimezone(self):
        if FvmUtil.getWinLang(self.osName) == "en_US":
            return "85"
        elif FvmUtil.getWinLang(self.osName) == "zh_CN":
            return "85"
        elif FvmUtil.getWinLang(self.osName) == "zh_TW":
            return "85"
        else:
            assert False

    def _getSerial(self):
        serialFile = self._getFile(self.osName, "serial")
        buf = FvmUtil.readFile(serialFile)
        return buf.split("\n")[0]

    def _getFile(self, osName, ftype):
        if osName == "Microsoft.Windows.XP.Professional.SP3.X86.zh_CN":
            if ftype == "iso":
                return os.path.join(self.dataDir, "winxp_sp3.iso")
            elif ftype == "serial":
                return os.path.join(self.dataDir, "winxp_sp3_serial.txt")
            elif ftype == "autounattend":
                return os.path.join(self.dataDir, "winnt.sif.in")
            else:
                assert False
        assert False


class BasicPrepareWork(FvmWorkFullControl):

    def __init__(self, dataDir, osName):
        self.workName = "Basic preparation"
        self.dataDir = dataDir
        self.osName = osName

    def doWork(self, param, vmObj, infoPrinter):
        """do driver update operation"""

        # prepare parameter
        self.param = param
        self.vmObj = vmObj

        # do preparation configuration in main disk image
        mptObj = WinDiskMountPoint(self.param, self.vmObj.getMainDiskImage(), FvmUtil.getWinLang(self.osName))
        try:
            winreg = WinRegistry(self.param, mptObj.getMountDir())

            # add sleep.exe, needed by delay code in startup.bat
            mptObj.addFile(os.path.join(self.dataDir, "sleep.exe"), "WINDOWS/system32", True)

            # Dismiss screen check, so it won't disturb us
            winreg.addOrModify("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\DontShowMeThisDialogAgain",
                               "ScreenCheck", "REG_SZ", "no")

            # Dismiss balloon tips, so it won't disturb us
            winreg.addOrModify("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced",
                               "EnableBalloonTips", "REG_DWORD", 0)

            # Disable "AutoPlay & AutoRun", they will disturb some config's autoit script
            winreg.addOrModify("HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\policies\\Explorer",
                               "NoDriveTypeAutoRun", "REG_DWORD", 0xff)
        finally:
            mptObj.umount()

        # boot with usb disk, so it can be the first hardware device recognized
        usbFile = os.path.join(self.param.tmpDir, "usb.img")
        if True:
            FvmUtil.createWinUsbImg(usbFile, 300, "ntfs")

            mptObj = WinDiskMountPoint(self.param, usbFile, FvmUtil.getWinLang(self.osName))
            try:
                mptObj.addAutoIt()

                # dismiss start menu show, so it won't disturb us
                mptObj.addFile(os.path.join(self.dataDir, "autocfg-dismiss-start-menu-show.au3"), "", False)

                # disable swapfile and snapshot as early as possible
                mptObj.addFile(os.path.join(self.dataDir, "autocfg-disable-swapfile.au3"), "", False)
                mptObj.addFile(os.path.join(self.dataDir, "autocfg-disable-snapshot.au3"), "", False)

                # disable anti-virus check, so it won't disturb us
                mptObj.addFile(os.path.join(self.dataDir, "autocfg-disable-antivirues-check.au3"), "", False)

                # disable screen saver, so it won't disturb us in future
                mptObj.addFile(os.path.join(self.dataDir, "autocfg-disable-screensaver.au3"), "", False)

                # disable desktop cleanup wizard
                mptObj.addFile(os.path.join(self.dataDir, "autocfg-disable-desktop-cleanup-wizard.au3"), "", False)

                # dismiss explore xp, so it won't disturb us
                # it can't be dismissed by directly modify the registry, don't know why
                mptObj.addFile(os.path.join(self.dataDir, "autocfg-dismiss-explore-winxp.au3"), "", False)
            finally:
                mptObj.umount()
        self.vmObj.setLocalUsbImage(usbFile)

        # create and inject startup file
        sFileList = ["autocfg-dismiss-start-menu-show.au3",
                     "autocfg-disable-swapfile.au3",
                     "autocfg-disable-snapshot.au3",
                     "autocfg-disable-antivirues-check.au3",
                     "autocfg-disable-screensaver.au3",
                     "autocfg-disable-desktop-cleanup-wizard.au3",
                     "autocfg-dismiss-explore-winxp.au3"]
        msf = MyStartupFile(self.param, self.osName, sFileList)
        msf.injectTo(self.vmObj.getMainDiskImage())

        # run virtual machine
        # this boot will also dimiss the start menu show, so it won't disturb us in future
        self.vmObj.run()


class DriverInstallWork(FvmWorkFullControl):

    def __init__(self, dataDir, osName):
        self.workName = "Install drivers"
        self.dataDir = dataDir
        self.osName = osName

    def doWork(self, param, vmObj, infoPrinter):
        """do driver install operation"""

        # prepare parameter
        self.param = param
        self.vmObj = vmObj

        mptObj = WinDiskMountPoint(self.param, self.vmObj.getMainDiskImage(), FvmUtil.getWinLang(self.osName))
        try:
            winreg = WinRegistry(self.param, mptObj.getMountDir())

            # Add drivers
            mptObj.mkdir("Drivers")
            self._addParaDriver(mptObj, "Drivers")
            self._addQxlDriver(mptObj, "Drivers")
            self._addVdagent(mptObj, "Drivers")

            # Configure driver installation options
            winreg.addOrModify("HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion",
                               "DevicePath", "REG_EXPAND_SZ", "%SystemRoot%\\inf;C:\\Drivers")
            winreg.addOrModify("HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching",
                               "DontPromptForWindowsUpdate", "REG_DWORD", 1)
            winreg.addOrModify("HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching",
                               "DontSearchWindowsUpdate", "REG_DWORD", 1)
            winreg.addOrModify("HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching",
                               "DontSearchFloppies", "REG_DWORD", 1)
            winreg.addOrModify("HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching",
                               "DontSearchCD", "REG_DWORD", 1)
        finally:
            mptObj.umount()

    def _addParaDriver(self, mptObj, dstDir):
        drvDir = os.path.join(self.param.tmpDir, "virtio")
        FvmUtil.shell('/bin/mkdir "%s"' % (drvDir), "stdout")
        FvmUtil.shell('/usr/bin/7z x "%s" -o"%s"' % (os.path.join(self.dataDir, "virtio-win-0.1-52.iso"), drvDir), "stdout")

        if FvmUtil.getWinArch(self.osName) == "x86":
            drvSubDir = os.path.join(drvDir, "XP", "X86")
            for f in os.listdir(drvSubDir):
                mptObj.addFile(os.path.join(drvSubDir, f), dstDir, True)
            drvSubDir = os.path.join(drvDir, "WXP", "X86")
            for f in os.listdir(drvSubDir):
                mptObj.addFile(os.path.join(drvSubDir, f), dstDir, True)
        elif FvmUtil.getWinArch(self.osName) == "amd64":
            drvSubDir = os.path.join(drvDir, "XP", "AMD64")
            for f in os.listdir(drvSubDir):
                mptObj.addFile(os.path.join(drvSubDir, f), dstDir, True)
        else:
            assert False

    def _addQxlDriver(self, mptObj, dstDir):
        drvDir = os.path.join(self.param.tmpDir, "qxl")
        FvmUtil.shell('/bin/mkdir "%s"' % (drvDir), "stdout")
        FvmUtil.shell('/usr/bin/unzip "%s" -d "%s"' % (os.path.join(self.dataDir, "qxl_xp_x86.zip"), drvDir), "stdout")

        drvSubDir = os.path.join(drvDir, "xp", "x86")
        for f in os.listdir(drvSubDir):
            mptObj.addFile(os.path.join(drvSubDir, f), dstDir, True)

    def _addVdagent(self, mptObj, dstDir):
        drvDir = os.path.join(self.param.tmpDir, "vdagent")
        FvmUtil.shell('/bin/mkdir "%s"' % (drvDir), "stdout")
        FvmUtil.shell('/usr/bin/unzip "%s" -d "%s"' % (os.path.join(self.dataDir, "vdagent-win32_20111124.zip"), drvDir), "stdout")

        if FvmUtil.getWinArch(self.osName) == "x86":
            drvSubDir = os.path.join(drvDir, "vdagent_x86")
        elif FvmUtil.getWinArch(self.osName) == "amd64":
            drvSubDir = os.path.join(drvDir, "vdagent_x64")
        else:
            assert False

        for f in os.listdir(drvSubDir):
            mptObj.addFile(os.path.join(drvSubDir, f), dstDir, True)


class DriverUpdateWork(FvmWorkFullControl):

    def __init__(self, dataDir, osName):
        self.workName = "Update drivers"
        self.dataDir = dataDir
        self.osName = osName

    def doWork(self, param, vmObj, infoPrinter):
        """do driver update operation"""

        # prepare parameter
        self.param = param
        self.vmObj = vmObj

        # create assistant usb disk
        usbFile = os.path.join(self.param.tmpDir, "usb.img")
        if True:
            FvmUtil.createWinUsbImg(usbFile, 300, "ntfs")

            mptObj = WinDiskMountPoint(self.param, usbFile, FvmUtil.getWinLang(self.osName))
            try:
                mptObj.addAutoIt()
                mptObj.addFile(os.path.join(self.dataDir, "autocfg-update-driver.au3"), "", False)
                mptObj.addFile(os.path.join(self.dataDir, "autocfg-enable-vdagent.au3"), "", False)
            finally:
                mptObj.umount()
        self.vmObj.setLocalUsbImage(usbFile)

        # update virtio harddisk driver
        if self.vmObj.getVmInfo().vmCfgHw.mainDiskInterface != "ide":
            # create and inject startup file
            sFileList = ["autocfg-update-driver.au3",
                         "autocfg-enable-vdagent.au3"]
            msf = MyStartupFile(self.param, self.osName, sFileList)
            msf.injectTo(self.vmObj.getMainDiskImage())

            # run virtual machine
            self.vmObj.setLocalFakeHarddisk(self.vmObj.getVmInfo().vmCfgHw.mainDiskInterface)
            self.vmObj.run()
            self.vmObj.setLocalFakeHarddisk("")

        # update drivers
        if True:
            # create and inject startup.bat to disk-main.img
            sFileList = ["autocfg-update-driver.au3",            # VirtIO SCSI driver
                         "autocfg-update-driver.au3",            # VirtIO Balloon driver
                         "autocfg-update-driver.au3",            # VirtIO Serial driver
                         "autocfg-update-driver.au3"]            # Red Hat QXL GPU driver
            msf = MyStartupFile(self.param, self.osName, sFileList)
            msf.injectTo(self.vmObj.getMainDiskImage())

            # run virtual machine
            self.vmObj.setSetupMode(False)
            self.vmObj.setNetworkStatus("isolate")
            self.vmObj.run()
            self.vmObj.setNetworkStatus("")

        # update virtio network driver
        if self.vmObj.getVmInfo().vmCfgHw.networkAdapterInterface != "user":
            # create and inject startup.bat to disk-main.img
            sFileList = ["autocfg-update-driver.au3"]            # VirtIO Network driver
            msf = MyStartupFile(self.param, self.osName, sFileList)
            msf.injectTo(self.vmObj.getMainDiskImage())

            # run virtual machine
            self.vmObj.setNetworkStatus("virtio-dummy")
            self.vmObj.run()
            self.vmObj.setNetworkStatus("")


class MyStartupFile:

    def __init__(self, param, osName, scriptFileList=[]):

        # create delayed run BAT file
        buf = ''
        buf += '@echo off\n'
        buf += 'setlocal enabledelayedexpansion\n'
        buf += '\n'

        buf += 'echo Waiting...\n'
        buf += ':loop1\n'
        buf += '    sleep 1\n'
        buf += '    if not exist "D:\\" (\n'
        buf += '        goto :loop1\n'
        buf += '    )\n'
        buf += '\n'

        buf += 'cd /d "D:\\"\n'
        for vsi in scriptFileList:
            buf += 'echo Executing script "%s"...\n' % (vsi)
            buf += '"autoit\\autoit3.exe" "%s"\n' % (vsi)
            buf += 'sleep 1\n'
            buf += '\n'

        buf += 'echo Shutting down...\n'
        buf += 'shutdown /s /t 5\n'
        buf += 'sleep 1\n'
        buf += '\n'

        buf += 'echo Deleting self...\n'
        buf += 'del /f "%~f0"\n'        # this line will cause a "file is missing" error, it's ok
        buf += '\n'

        # other operations
        self.param = param
        self.osName = osName
        self.buf = buf

    def injectTo(self, mainDiskImage):

        # write to tmp file
        tmpf = os.path.join(self.param.tmpDir, "startup.bat")
        FvmUtil.writeFile(tmpf, self.buf)

        # inject operation
        mptObj = WinDiskMountPoint(self.param, mainDiskImage, FvmUtil.getWinLang(self.osName))
        try:
            startupDir = FvmUtil.getWinDir("startup", FvmUtil.getWinLang(self.osName), FvmUtil.getWinUser())
            mptObj.addFile(tmpf, startupDir, False)
        finally:
            mptObj.umount()

        os.remove(tmpf)

        # inject operation
#        startupDir = FvmUtil.getWinDir("startup", FvmUtil.getWinLang(self.osName), FvmUtil.getWinUser())
#        FvmUtil.shell('/usr/bin/virt-copy-in -a "%s" "%s" "/%s"'%(mainDiskImage, tmpf, startupDir), "stdout")
#
#        os.remove(tmpf)
