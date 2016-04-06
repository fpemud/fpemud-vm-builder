Run("wmp11-windowsxp-x86-ZH-CN.exe")

WinWaitActive("Windows Media Player 11")						; uncompress files

WinWaitActive("Windows Media Player 11", "验证您的 Windows 副本")
Send("!v")										; press "verify" button

WinWaitActive("Windows Media Player 11", "感谢您选择 Windows Media Player 11")
Send("!a")
WinWaitActive("Windows Media Player 11", "是否要继续?")
Send("{ENTER}")

WinWaitActive("Windows Media Player 11", "欢迎使用 Windows Media Player 11")
Send("!e")										; select rapid setting
Send("!f")										; press "finish" button

WinWaitActive("Windows Media Player")
Sleep(10000)										; wait for the demo animation
Send("!{F4}")
WinWaitClose("Windows Media Player")
