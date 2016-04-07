#include <FvmUtil.au3>

Send("#{PAUSE}")					; system properties shortcut: win-pause/break 
WinWaitActive("系统属性")

Send("{RIGHT 3}")					; goto "advanced" tab
Send("!s")						; press "setting" button in "performance" frame
WinWaitActive("性能选项")

Send("{TAB 4}")						; goto "visual effect" tab from current focus
If $CmdLine[1] == "effect" Then
	Send("!b")					; select "for effect" radio button
Else
	Send("!p")					; select "for speed" radio button
EndIf

Send("{ENTER}")
WinWaitClose("性能选项")

Send("{ENTER}")
WinWaitClose("系统属性")
