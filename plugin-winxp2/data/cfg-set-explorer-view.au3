#include <GuiTreeView.au3>

Send("#e")
WinWaitActive("我的电脑")

If $CmdLine[1] == "default" Then
EndIf
If $CmdLine[1] == "detail" Then
	Send("!v")			; menu "View"
	Send("d")			; menu "Detail"
EndIf

Send("!t")			; menu "Tool"
Send("o")			; menu "Folder Option"
WinWaitActive("文件夹选项")

ControlCommand("文件夹选项", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")
$hWnd = ControlGetHandle("文件夹选项", "", "[CLASS:SysTreeView32; INSTANCE:1]")

If $CmdLine[1] == "default" Then
EndIf
If $CmdLine[1] == "detail" Then
	ControlClick("文件夹选项", "", "[CLASS:Button; TEXT:应用到所有文件夹(&L)]")
	WinWaitActive("文件夹视图")
	Send("{ENTER}")
	WinWaitClose("文件夹视图")

	; check this item
	$hItem = _GUICtrlTreeView_FindItem($hWnd, "不缓存缩略图")
	If _GUICtrlTreeView_GetImageIndex($hWnd, $hItem) <> 0 Then
		_GUICtrlTreeView_ClickItem($hWnd, $hItem)
	EndIf

	; un-check this item
	$hItem = _GUICtrlTreeView_FindItem($hWnd, "记住每个文件夹的视图设置")
	If _GUICtrlTreeView_GetImageIndex($hWnd, $hItem) <> 1 Then
		_GUICtrlTreeView_ClickItem($hWnd, $hItem)
	EndIf
EndIf

ControlClick("文件夹选项", "", "[CLASS:Button; TEXT:确定]")
WinWaitClose("文件夹选项")

Send("!{F4}")
WinWaitClose("我的电脑")
