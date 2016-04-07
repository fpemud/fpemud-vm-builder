#include <WINAPI.au3>

Send("#e")
WinWaitActive("我的电脑")

Send("^f")
WinWaitActive("我的电脑", "您要查找什么?")

For $i = 1 to $CmdLine[0]
	ControlClick("我的电脑", "", "[CLASS:SA_Button; TEXT:改变首选项(&G)]")
	WinWaitActive("我的电脑", "您想怎样使用搜索助理")

	If $CmdLine[$i] == "balloon-prompt:on" Then
		$hCtrl = ControlGetHandle("我的电脑", "", "[CLASS:SA_Button; TEXT:显示气球提示(&P)]")
		If $hCtrl <> "" And ControlCommand("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl), "IsVisible") Then
			ControlClick("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl))
		Else
			ControlClick("我的电脑", "", "[CLASS:Button; TEXT:后退(&B)]")
		EndIf
		WinWaitActive("我的电脑", "您要查找什么?")
	EndIf
	If $CmdLine[$i] == "balloon-prompt:off" Then
		$hCtrl = ControlGetHandle("我的电脑", "", "[CLASS:SA_Button; TEXT:不要显示气球提示(&P)]")
		If $hCtrl <> "" And ControlCommand("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl), "IsVisible") Then
			ControlClick("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl))
		Else
			ControlClick("我的电脑", "", "[CLASS:Button; TEXT:后退(&B)]")
		EndIf
		WinWaitActive("我的电脑", "您要查找什么?")
	EndIf
	If $CmdLine[$i] == "auto-completion:on" Then
		$hCtrl = ControlGetHandle("我的电脑", "", "[CLASS:SA_Button; TEXT:启用自动完成(&O)]")
		If $hCtrl <> "" And ControlCommand("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl), "IsVisible") Then
			ControlClick("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl))
		Else
			ControlClick("我的电脑", "", "[CLASS:Button; TEXT:后退(&B)]")
		EndIf
		WinWaitActive("我的电脑", "您要查找什么?")
	EndIf
	If $CmdLine[$i] == "auto-completion:off" Then
		$hCtrl = ControlGetHandle("我的电脑", "", "[CLASS:SA_Button; TEXT:关闭自动完成(&O)]")
		If $hCtrl <> "" And ControlCommand("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl), "IsVisible") Then
			ControlClick("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl))
		Else
			ControlClick("我的电脑", "", "[CLASS:Button; TEXT:后退(&B)]")
		EndIf
		WinWaitActive("我的电脑", "您要查找什么?")
	EndIf
	If $CmdLine[$i] == "animation:on" Then
		$hCtrl = ControlGetHandle("我的电脑", "", "[CLASS:SA_Button; TEXT:使用动画屏幕角色(&S)]")
		If $hCtrl <> "" And ControlCommand("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl), "IsVisible") Then
			ControlClick("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl))
		Else
			ControlClick("我的电脑", "", "[CLASS:Button; TEXT:后退(&B)]")
		EndIf
		WinWaitActive("我的电脑", "您要查找什么?")
	EndIf
	If $CmdLine[$i] == "animation:off" Then
		$hCtrl = ControlGetHandle("我的电脑", "", "[CLASS:SA_Button; TEXT:不使用动画屏幕角色(&S)]")
		If $hCtrl <> "" And ControlCommand("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl), "IsVisible") Then
			ControlClick("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl))
		Else
			ControlClick("我的电脑", "", "[CLASS:Button; TEXT:后退(&B)]")
		EndIf
		WinWaitActive("我的电脑", "您要查找什么?")
	EndIf
	If $CmdLine[$i] == "indexing:on" Then
		$hCtrl = ControlGetHandle("我的电脑", "", "[CLASS:SA_Button; TEXT:使用制作索引服务(使本地搜索更快)(&I)]")
		If $hCtrl <> "" And ControlCommand("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl), "IsVisible") Then
			ControlClick("我的电脑", "", "[CLASS:SA_Button; TEXT:使用制作索引服务(使本地搜索更快)(&I)]")
			WinWaitActive("我的电脑", "制作索引服务")
			ControlClick("我的电脑", "", "[CLASS:SA_Button; TEXT:是的，启用制作索引服务(&Y)]")
			ControlClick("我的电脑", "", "[CLASS:Button; TEXT:确定]")
		Else
			ControlClick("我的电脑", "", "[CLASS:Button; TEXT:后退(&B)]")
		EndIf
		WinWaitActive("我的电脑", "您要查找什么?")
	EndIf
	If $CmdLine[$i] == "indexing:off" Then
		$hCtrl = ControlGetHandle("我的电脑", "", "[CLASS:SA_Button; TEXT:不使用制作索引服务(&I)]")
		If $hCtrl <> "" And ControlCommand("我的电脑", "", _WINAPI_GetDlgCtrlID($hCtrl), "IsVisible") Then
			ControlClick("我的电脑", "", "[CLASS:SA_Button; TEXT:不使用制作索引服务(&I)]")
			WinWaitActive("我的电脑", "制作索引服务")
			ControlClick("我的电脑", "", "[CLASS:SA_Button; TEXT:不，不要启用制作索引服务(&N)]")
			ControlClick("我的电脑", "", "[CLASS:Button; TEXT:确定]")
		Else
			ControlClick("我的电脑", "", "[CLASS:Button; TEXT:后退(&B)]")
		EndIf
		WinWaitActive("我的电脑", "您要查找什么?")
	EndIf
Next

Send("!{F4}")
WinWaitClose("搜索结果")

