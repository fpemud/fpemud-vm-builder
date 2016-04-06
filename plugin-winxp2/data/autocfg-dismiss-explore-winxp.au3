Run("C:\WINDOWS\system32\tourstart.exe")
WinWaitActive("简介 - Microsoft Internet Explorer")
Send("!{F4}")
WinWaitClose("简介 - Microsoft Internet Explorer")
