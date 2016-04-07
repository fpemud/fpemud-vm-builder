#include <FvmUtil.au3>

Send("#{PAUSE}")					; system properties shortcut: win-pause/break 
_FvmWinWaitAndActivate("系统属性")

Send("{RIGHT 3}")					; goto "advanced" tab
Send("!s")						; press "setting" button in "performance" frame
WinWaitActive("性能选项")

Send("{TAB 4}")						; goto "visual effect" tab from current focus
Send("{RIGHT 1}")					; goto "advanced" tab
Send("!c")						; select "change" button in "virtual memory" frame
WinWaitActive("虚拟内存")

Send("!n")						; press button "no swap file"
Send("!s")						; press button "set"

Send("{ENTER}")						; press button "OK"
WinWaitActive("系统控制面板小程序")			; reboot prompt
Send("{ENTER}")
WinWaitClose("系统控制面板小程序")

Send("{ENTER}")						; re-press button "OK"
WinWaitClose("虚拟内存")

Send("{ENTER}")						; press button "OK"
WinWaitActive("系统设置改变")				; reboot inquiry
Send("!n")
