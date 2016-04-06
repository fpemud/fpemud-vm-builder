#include <GuiSlider.au3>

$Resolution = $CmdLine[1]		; RESOLUTION

;=====================================================================================================

Run("control.exe desk.cpl")
WinWaitActive("显示 属性")

; goto "setting" tab
ControlCommand("显示 属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")
ControlCommand("显示 属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")
ControlCommand("显示 属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")
ControlCommand("显示 属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")
WinWaitActive("显示 属性", "屏幕分辨率(&S)")

; get current slider position
$hSlider = ControlGetHandle("显示 属性", "", "[CLASS:msctls_trackbar32; INSTANCE:1]")
$iPos = _GUICtrlSlider_GetPos($hSlider)

; move slider
If $Resolution == "800x600" Then
	$dPos = 0
ElseIf $Resolution == "832x624" Then
	$dPos = 1
ElseIf $Resolution == "960x640" Then
	$dPos = 2
ElseIf $Resolution == "1024x600" Then
	$dPos = 3
ElseIf $Resolution == "1024x768" Then
	$dPos = 4
ElseIf $Resolution == "1152x864" Then
	$dPos = 5
ElseIf $Resolution == "1152x870" Then
	$dPos = 6
ElseIf $Resolution == "1280x720" Then
	$dPos = 7
ElseIf $Resolution == "1280x760" Then
	$dPos = 8
ElseIf $Resolution == "1280x768" Then
	$dPos = 9
ElseIf $Resolution == "1280x800" Then
	$dPos = 10
ElseIf $Resolution == "1280x960" Then
	$dPos = 11
ElseIf $Resolution == "1280x1024" Then
	$dPos = 12
ElseIf $Resolution == "1360x768" Then
	$dPos = 13
ElseIf $Resolution == "1366x768" Then
	$dPos = 14
ElseIf $Resolution == "1400x1050" Then
	$dPos = 15
ElseIf $Resolution == "1440x900" Then
	$dPos = 16
ElseIf $Resolutio  == "1600x900" Then
	$dPos = 17
ElseIf $Resolution == "1600x1200" Then
	$dPos = 18
ElseIf $Resolution == "1680x1050" Then
	$dPos = 19
ElseIf $Resolution == "1920x1080" Then
	$dPos = 20
ElseIf $Resolution == "1920x1200" Then
	$dPos = 21
ElseIf $Resolution == "1920x1440" Then
	$dPos = 22
ElseIf $Resolution == "2048x1536" Then
	$dPos = 23
ElseIf $Resolution == "2560x1440" Then
	$dPos = 24
ElseIf $Resolution == "2560x1600" Then
	$dPos = 25
ElseIf $Resolution == "2560x2048" Then
	$dPos = 26
ElseIf $Resolution == "2800x2100" Then
	$dPos = 27
ElseIf $Resolution == "3200x2400" Then
	$dPos = 28
EndIf

If $iPos == $dPos Then
	Send("{ESC}")
	Exit
EndIf

ControlFocus("显示 属性", "", "[CLASS:msctls_trackbar32; INSTANCE:1]")
Send("{HOME}")
Send("{RIGHT " & $dPos & "}")
Send("{ENTER}")											; press OK button
WinWaitActive("监视器设置")
Send("!y")
WinWaitClose("监视器设置")
WinWaitClose("显示 属性")
