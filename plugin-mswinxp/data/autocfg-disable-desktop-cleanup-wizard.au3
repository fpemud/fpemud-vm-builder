#include <FvmUtil.au3>

Run("control.exe desk.cpl")
_FvmWinWaitAndActivate("显示 属性")

ControlCommand("显示 属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")		; goto "desktop" tab
Sleep(1000)											; needed, don't know why

ControlClick("显示 属性", "", "[CLASS:Button; TEXT:自定义桌面(&D)...]")

WinWaitActive("桌面项目")
ControlCommand("桌面项目", "", "[CLASS:Button; TEXT:每 60 天运行桌面清理向导(&U)]", "UnCheck")
ControlClick("桌面项目", "", "[CLASS:Button; TEXT:确定]")
WinWaitClose("桌面项目")

ControlClick("显示 属性", "", "[CLASS:Button; TEXT:确定]")
Sleep(1000)											; wait for the new cfg to be applied
