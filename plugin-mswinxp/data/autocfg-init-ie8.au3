#include <FvmUtil.au3>

If _FvmGetBootNo() == 1 Then
	Run("IE8-WindowsXP-x86-CHS.exe")

	WinWaitActive("正在提取文件")

	WinWaitActive("安装 Windows Internet Explorer 8")
	Send("!o")
	ControlClick("安装 Windows Internet Explorer 8", "", "[CLASS:Button; TEXT:下一步(&N) >]")

	WinWaitActive("安装 Windows Internet Explorer 8", "请阅读许可条款")
	Send("!a")

	WinWaitActive("安装 Windows Internet Explorer 8", "获取最新的更新")
	Send("{ENTER}")

	WinWaitActive("安装 Windows Internet Explorer 8", "Internet Explorer 安装已完成")
	Send("!l")

	WinWaitActive("安装 Windows Internet Explorer 8", "确实要稍后重新启动?")
	Send("!y")
	WinWaitClose("安装 Windows Internet Explorer 8", "确实要稍后重新启动?")

	WinWaitClose("安装 Windows Internet Explorer 8")
Else
	Run("C:\Program Files\Internet Explorer\IEXPLORE.EXE")

	WinWaitActive("设置 Windows Internet Explorer")
	Send("!n")

	Sleep(500)								; window use graph not text, so sleep have to be used
	;WinWaitActive("设置 Windows Internet Explorer", "打开建议网站")
	Send("!o")
	Send("!n")

	Sleep(500)								; window use graph not text, so sleep have to be used
	;WinWaitActive("设置 Windows Internet Explorer", "选择您的设置")
	Send("!u")
	Send("!f")

	WinWaitClose("设置 Windows Internet Explorer")

	RegWrite("HKEY_CURRENT_USER\Software\Microsoft\Internet Explorer\Main", "AlwaysShowMenus", "REG_DWORD", 0)
	RegWrite("HKEY_CURRENT_USER\Software\Microsoft\Internet Explorer\LinksBar", "Enabled", "REG_DWORD", 0)
	RegWrite("HKEY_CURRENT_USER\Software\Microsoft\Internet Explorer\Main", "NotifyDownloadComplete", "REG_SZ", "no")

	; disable warn-dialog "close all tabs"
	RegWrite("HKEY_CURRENT_USER\Software\Microsoft\Internet Explorer\TabbedBrowsing", "WarnOnClose", "REG_DWORD", 0)

	_FvmSetShutdownFlag()
EndIf
