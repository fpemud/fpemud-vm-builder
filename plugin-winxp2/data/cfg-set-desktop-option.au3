#include <GuiMenu.au3>

For $i = 1 to $CmdLine[0]
	If StringInStr($CmdLine[$i], "sort-icon:", 1) == 1 Then
;		ControlClick("[CLASS:Shell_TrayWnd]", "", "[CLASS:TrayNotifyWnd; INSTANCE:1]", "menu", 1, 0, 0)
;		WinWait("[CLASS:#32768]")								; wait for the popup menu
;		$hPopupWnd = WinGetHandle("[CLASS:#32768]")
;		$hPopupMenu = "0x" & Hex(_SendMessage($hPopupWnd, 0x01E1, 0, 0))			; send MN_GETHMENU(0x1e1) to $hPopupWnd to get menu handle
;
;		$tbItemId = _GUICtrlMenu_FindItem($hPopupMenu, "工具栏(T)")				; submenu of "Toolbar" is dynamically generated, so the submenu must be shown first
;													; argument of _GUICtrlMenu_FindItem doesn't need "&", -_-||
;		Send("{DOWN " & ($tbItemId + 1) & "}")							; fixme: should consider menu separater item here
;		Send("{RIGHT}")
;		$hSubMenu = _GUICtrlMenu_GetItemSubMenu($hPopupMenu, 0)
;		$wmpItemId = _GUICtrlMenu_FindItem($hSubMenu, "Windows Media Player")
;		$bChkRet = _GUICtrlMenu_GetItemChecked($hSubMenu, $wmpItemId)
;
;		If $CmdLine[$i] == "minimize-to-taskbar:on" And $bChkRet <> True Then
;			If $wmpItemId > 0 Then
;				Send("{DOWN " & $wmpItemId & "}")					; when submenu shows, there's already a selection, so no "+1" here
;			EndIf
;			Send("{ENTER}")
;		ElseIf $CmdLine[$i] == "minimize-to-taskbar:off" And $bChkRet <> False Then
;			If $wmpItemId > 0 Then
;				Send("{DOWN " & $wmpItemId & "}")					; same as above
;			EndIf
;			Send("{ENTER}")
;		Else
;			Send("{ESC}")									; dismiss the submenu
;			Send("{ESC}")									; dismiss the menu
;		EndIf
	EndIf
Next
