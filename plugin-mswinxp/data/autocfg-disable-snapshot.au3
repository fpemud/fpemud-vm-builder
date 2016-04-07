#include <FvmUtil.au3>

Send("#{PAUSE}")					; system properties shortcut: win-pause/break 
_FvmWinWaitAndActivate("系统属性")

Send("{RIGHT 4}")
Send("!t")						; turn off system restore 
Send("{ENTER}")						; press OK button

WinWaitActive("系统还原")				; confirm dialog
Send("{ENTER}")
