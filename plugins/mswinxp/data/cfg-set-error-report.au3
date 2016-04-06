$OpType = $CmdLine[1]		; enable|disable

;=====================================================================================================

Send("#{PAUSE}")					; system properties shortcut: win-pause/break 
WinWaitActive("系统属性")

Send("{RIGHT 3}")					; goto "advanced" tab
Send("!r")						; press "error report" button
WinWaitActive("错误汇报")

If $OpType == "enable" Then
	Send("!e")					; select "enable error report" radio buttone
Else
	Send("!s")					; select "disable error report" radio button
EndIf

Send("{ENTER}")						; press button "OK"
WinWaitClose("错误汇报")

Send("{ENTER}")
WinWaitClose("系统属性")
