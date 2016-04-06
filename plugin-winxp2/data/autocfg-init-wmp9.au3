#include <FvmUtil.au3>

Run("C:\Program Files\Windows Media Player\wmplayer.exe")

WinWaitActive("Windows Media Player 9 系列")
Send("{ENTER}")

WinWaitActive("Windows Media Player 9 系列", "选择您的隐私选项")
Send("{ENTER}")

WinWaitActive("Windows Media Player 9 系列", "自定义安装选项")
Send("{ENTER}")

_FvmWinWaitAndActivate("Windows Media Player")
WinClose("Windows Media Player")
;Send("!{F4}")
WinWaitClose("Windows Media Player")

RegWrite("HKEY_CURRENT_USER\SOFTWARE\Microsoft\MediaPlayer\Preferences", "ShowMinimizeDialog", "REG_DWORD", 0)
