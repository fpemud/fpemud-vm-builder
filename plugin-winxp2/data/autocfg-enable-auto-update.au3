#include <FvmUtil.au3>

Send("#{PAUSE}")					; system properties shortcut: win-pause/break 
_FvmWinWaitAndActivate("系统属性")

Send("{RIGHT 5}")					; goto "auto update" tab
Send("!u")
ControlCommand("系统属性", "", "[CLASS:ComboBox, INSTANCE:2]", "SelectString", "0:00")

Send("{ENTER}")						; press button "OK"
WinWaitClose("系统属性")
