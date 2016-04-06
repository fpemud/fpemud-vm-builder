#include <GuiTreeView.au3>

Send("#e")
WinWaitActive("我的电脑")

Send("!t")			; menu "Tool"
Send("o")			; menu "Folder Option"
WinWaitActive("文件夹选项")

ControlCommand("文件夹选项", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")
WinWaitActive("文件夹选项", "文件夹视图")

$hWnd = ControlGetHandle("文件夹选项", "", "[CLASS:SysTreeView32; INSTANCE:1]")
For $i = 1 to $CmdLine[0]
	If $CmdLine[$i] == "file-ext:show" Then
		; un-check this item
		$hItem = _GUICtrlTreeView_FindItem($hWnd, "隐藏已知文件类型的扩展名")
		If _GUICtrlTreeView_GetImageIndex($hWnd, $hItem) <> 1 Then
			_GUICtrlTreeView_ClickItem($hWnd, $hItem)
		EndIf
	EndIf
	If $CmdLine[$i] == "file-ext:hide" Then
		; check this item
		$hItem = _GUICtrlTreeView_FindItem($hWnd, "隐藏已知文件类型的扩展名")
		If _GUICtrlTreeView_GetImageIndex($hWnd, $hItem) <> 0 Then
			_GUICtrlTreeView_ClickItem($hWnd, $hItem)
		EndIf
	EndIf
	If $CmdLine[$i] == "hidden-file:show" Then
		$hItem = _GUICtrlTreeView_FindItem($hWnd, "显示所有文件和文件夹")
		_GUICtrlTreeView_ClickItem($hWnd, $hItem)
	EndIf
	If $CmdLine[$i] == "hidden-file:hide" Then
		$hItem = _GUICtrlTreeView_FindItem($hWnd, "不显示隐藏的文件和文件夹")
		_GUICtrlTreeView_ClickItem($hWnd, $hItem)
	EndIf
	If $CmdLine[$i] == "extra-tip:show" Then
		; check this item
		$hItem = _GUICtrlTreeView_FindItem($hWnd, "鼠标指向文件夹和桌面项时显示提示信息")
		If _GUICtrlTreeView_GetImageIndex($hWnd, $hItem) <> 0 Then
			_GUICtrlTreeView_ClickItem($hWnd, $hItem)
		EndIf
	EndIf
	If $CmdLine[$i] == "extra-tip:hide" Then
		; un-check this item
		$hItem = _GUICtrlTreeView_FindItem($hWnd, "鼠标指向文件夹和桌面项时显示提示信息")
		If _GUICtrlTreeView_GetImageIndex($hWnd, $hItem) <> 1 Then
			_GUICtrlTreeView_ClickItem($hWnd, $hItem)
		EndIf
	EndIf
Next

ControlClick("文件夹选项", "", "[CLASS:Button; TEXT:确定]")
WinWaitClose("文件夹选项")

WinClose("我的电脑")
WinWaitClose("我的电脑")
