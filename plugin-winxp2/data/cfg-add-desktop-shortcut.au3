#include <WINAPI.au3>
#include <FvmUtil.au3>

Send("#e")
WinWaitActive("我的电脑")

Send("{UP}")
Send("{UP}")			; move to desktop item
Sleep(3000)			; wait for directory refresh

Send("!f")
Send("w")
Send("s")
WinWaitActive("创建快捷方式")

Send($CmdLine[3])		; input "target"
Send("!n")
WinWaitActive("选择程序标题")

Send($CmdLine[2])		; input "name"
Send("{ENTER}")
WinWaitClose("选择程序标题")

WinClose("桌面")
WinWaitClose("桌面")
