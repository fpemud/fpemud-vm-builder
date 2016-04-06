#include <FvmUtil.au3>

Run("WindowsXP-KB942288-v3-x86.exe")

WinWaitActive("软件更新安装向导")
Send("!n")

WinWaitActive("软件更新安装向导", "许可协议")
Send("!a")
Send("!n")

WinWaitActive("软件更新安装向导", "您已成功完成")
Send("!d")
ControlClick("软件更新安装向导", "", "[CLASS:Button; TEXT:完成]")

WinWaitClose("软件更新安装向导")
