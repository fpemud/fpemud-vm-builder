Run("control.exe wscui.cpl")
WinWaitActive("Windows 安全中心")

Send("!e")
WinWaitActive("建议")

Send("!i")
Send("{ENTER}")
WinWaitClose("建议")

Send("!{F4}")
WinWaitClose("Windows 安全中心")
