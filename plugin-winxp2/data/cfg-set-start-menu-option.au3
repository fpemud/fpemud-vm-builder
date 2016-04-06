Run("RunDLL32.EXE shell32.dll,Options_RunDLL 1")
WinWaitActive("任务栏和「开始」菜单属性")

For $i = 1 to $CmdLine[0]
	If $CmdLine[$i] == "style:winxp" Then
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")
		Send("!s")
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabLeft", "")
	EndIf
	If $CmdLine[$i] == "style:classic" Then
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")
		Send("!m")
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabLeft", "")
	EndIf

	If $CmdLine[$i] == "auto-hide:on" Then
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:Button; TEXT:自动隐藏任务栏(&L)]", "Check", "")
	EndIf
	If $CmdLine[$i] == "auto-hide:off" Then
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:Button; TEXT:自动隐藏任务栏(&L)]", "UnCheck", "")
	EndIf

	If $CmdLine[$i] == "inactive-tray-icon:show" Then
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:Button; TEXT:隐藏不活动的图标(&H)]", "Check", "")
	EndIf
	If $CmdLine[$i] == "inactive-tray-icon:hide" Then
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:Button; TEXT:隐藏不活动的图标(&H)]", "UnCheck", "")
	EndIf

	If $CmdLine[$i] == "group-task:on" Then
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:Button; TEXT:分组相似任务栏按钮(&G)]", "Check", "")
	EndIf
	If $CmdLine[$i] == "group-task:off" Then
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:Button; TEXT:分组相似任务栏按钮(&G)]", "UnCheck", "")
	EndIf

	If $CmdLine[$i] == "quick-bar:on" Then
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:Button; TEXT:显示快速启动(&Q)]", "Check", "")
	EndIf
	If $CmdLine[$i] == "quick-bar:off" Then
		ControlCommand("任务栏和「开始」菜单属性", "", "[CLASS:Button; TEXT:显示快速启动(&Q)]", "UnCheck", "")
	EndIf

	; In fact they don't need the configure window
	If $CmdLine[$i] == "balloon-tips:on" Then
		RegWrite("HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "EnableBalloonTips", "REG_DWORD", 1)
	EndIf
	If $CmdLine[$i] == "balloon-tips:off" Then
		RegWrite("HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "EnableBalloonTips", "REG_DWORD", 0)
	EndIf
Next

ControlClick("任务栏和「开始」菜单属性", "", "[CLASS:Button; TEXT:确定]")
WinWaitClose("任务栏和「开始」菜单属性")
