#include <WINAPI.au3>

Run("control.exe")
WinWaitActive("控制面板")

$hCtrl = ControlGetHandle("控制面板", "", "[CLASS:SysListView32; INSTANCE:1]")
If $hCtrl <> "" And ControlCommand("控制面板", "", _WINAPI_GetDlgCtrlID($hCtrl), "IsVisible") Then
	$curStyle = "classic"
Else
	$curStyle = "category"
EndIf

If $curStyle <> $CmdLine[1] Then
	Sleep(500)					; wait for the pop-down animation in the left panel
	Opt("MouseCoordMode", 2)
	MouseClick("left", 60, 145, 1, 0)		; switch style
EndIf

Send("!{F4}")
WinWaitClose("控制面板")
