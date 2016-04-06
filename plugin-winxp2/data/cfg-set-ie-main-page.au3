Run("control.exe inetcpl.cpl")
WinWaitActive("Internet 属性")

If $CmdLine[1] == "default" Then
	Send("!f")
ElseIf $CmdLine[1] == "blank" Then
	Send("!b")
Else
	ControlSetText("Internet 属性", "", "[CLASS:Edit; INSTANCE:1]", $CmdLine[1])
EndIf

ControlClick("Internet 属性", "", "[CLASS:Button; TEXT:确定]")
WinWaitClose("Internet 属性")
