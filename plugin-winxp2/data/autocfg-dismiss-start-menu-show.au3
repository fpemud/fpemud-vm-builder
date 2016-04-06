#include <GuiButton.au3>

; start menu will show automatically, close it
$hStartButton = ControlGetHandle("[CLASS:Shell_TrayWnd]", "", "[CLASS:Button; INSTANCE:1]")
While 1
	If BitAND(_GUICtrlButton_GetState($hStartButton), $BST_PUSHED) Then
		Send("{ESC}")		; close start menu
		Exit
	EndIf
	Sleep(50)
WEnd
