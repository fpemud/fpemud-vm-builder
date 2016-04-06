#include <FvmUtil.au3>

Run("install_flash_player.exe")

WinWaitActive("Adobe Flash Player 11.7 安装程序")

ControlCommand("Adobe Flash Player 11.7 安装程序", "", "[CLASS:Button; INSTANCE:5]", "Check")		; accept license
;_FvmControlWaitEnable("Adobe Flash Player 11.7 安装程序", "", "[CLASS:Button; TEXT:安装]")		; no effect, don't know why
Sleep(1000)
ControlClick("Adobe Flash Player 11.7 安装程序", "", "[CLASS:Button; TEXT:安装]")

_FvmControlWaitEnable("Adobe Flash Player 11.7 安装程序", "", "[CLASS:Button; TEXT:完成]")
ControlCommand("Adobe Flash Player 11.7 安装程序", "", "[CLASS:Button; INSTANCE:12]", "Check")		; don't check for update
ControlClick("Adobe Flash Player 11.7 安装程序", "", "[CLASS:Button; TEXT:完成]")

WinWaitClose("Adobe Flash Player 11.7 安装程序")
