$ThemeName = $CmdLine[1]	; THEME_NAME

;=====================================================================================================

Run("control.exe desk.cpl")
WinWaitActive("显示 属性")

ControlCommand("显示 属性", "", "[CLASS:ComboBox; INSTANCE:1]", "SelectString", $ThemeName)

Send("{ENTER}")						; press button "OK"
WinWaitClose("显示 属性")
