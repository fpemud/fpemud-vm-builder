#include <FvmUtil.au3>

; install jre
Run("jre-7u17-windows-i586.exe")

WinWaitActive("[CLASS:#32770]")						; can not use window title, don't know why
ControlClick("[CLASS:#32770]", "", "[CLASS:Button; TEXT:安装(&I) >]")

WinWaitActive("Java 安装 - 完成")
ControlClick("Java 安装 - 完成", "", "[CLASS:Button; TEXT:关闭(&C)]")

WinWaitClose("Java 安装 - 完成")

; configure jre
Sleep(10 * 1000)							; update tab won't come up until waiting

Run("control.exe javacpl.cpl")
WinWaitActive("Java 控制面板")

Send("{RIGHT}")								; go to update tab
Sleep(1000)

Send("{TAB 2}")								; go to auto-check-update radio
Send("{SPACE}")

WinWaitActive("Java Update - 警告")
Send("{TAB}")								; go to don't check button
Send("{SPACE}")
WinWaitClose("Java Update - 警告")

Send("{ENTER}")								; press OK button
WinWaitClose("Java 控制面板")
