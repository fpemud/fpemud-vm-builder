#include <FvmUtil.au3>

Run("control.exe desk.cpl")
_FvmWinWaitAndActivate("显示 属性")

ControlCommand("显示 属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")
ControlCommand("显示 属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")		; goto "screen saver" tab
Sleep(1000)											; needed, don't know why

ControlCommand("显示 属性", "", "[CLASS:ComboBox; INSTANCE:1]", "SelectString", "(无)")

Send("{ENTER}")											; press OK button
Sleep(1000)											; wait for the new cfg to be applied
