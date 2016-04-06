#include <GuiMenu.au3>
#include <FvmUtil.au3>

For $i = 1 to $CmdLine[0]
	If $CmdLine[$i] == "auto-start:on" Then
		RegWrite("HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "Taskmgr", "REG_SZ", "start /min C:\WINDOWS\system32\taskmgr.exe")
	EndIf

	If $CmdLine[$i] == "auto-start:off" Then
		RegDelete("HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run", "Taskmgr")
	EndIf

	If $CmdLine[$i] == "hide-when-minimized:on" Or $CmdLine[1] == "hide-when-minimized:off" Then
		Run("C:\WINDOWS\system32\taskmgr.exe")
		WinWaitActive("Windows 任务管理器")

		$hMenu = _GUICtrlMenu_GetMenu(WinGetHandle("Windows 任务管理器"))	; get root menu
		$hMenu = _GUICtrlMenu_GetItemSubMenu($hMenu, 1)				; goto "options" menu
		$bChecked = _GUICtrlMenu_GetItemChecked($hMenu, 2, True)		; get the check state of "hide when minimized" menu

		; click "hide when minimized" menu
		If $CmdLine[$i] == "hide-when-minimized:on" And Not $bChecked Then
			WinMenuSelectItem("Windows 任务管理器", "", "选项(&O)", "最小化时隐藏(&H)")
		EndIf

		If $CmdLine[$i] == "hide-when-minimized:off" And $bChecked Then
			WinMenuSelectItem("Windows 任务管理器", "", "选项(&O)", "最小化时隐藏(&H)")
		EndIf

		WinClose("Windows 任务管理器")
		WinWaitClose("系统属性")
	EndIf
Next


