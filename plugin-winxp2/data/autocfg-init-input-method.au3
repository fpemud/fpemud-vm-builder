#include <GuiTreeView.au3>
#include <FvmUtil.au3>

Run("control.exe intl.cpl")

_FvmWinWaitAndActivate("区域和语言选项")
ControlCommand("区域和语言选项", "", "[CLASS:SysTabControl32; INSTANCE:1]", "TabRight", "")	; goto "language" tab
ControlClick("区域和语言选项", "", "[CLASS:Button; TEXT:详细信息(&D)...]")

WinWaitActive("文字服务和输入语言")

Send("!b")					; dimiss lanuage bar
WinWaitActive("语言栏设置")
Send("!d")
Send("{ENTER}")
WinWaitClose("语言栏设置")

$hWnd = ControlGetHandle("文字服务和输入语言", "", "[CLASS:SysTreeView32; INSTANCE:1]")

$hItem = _GUICtrlTreeView_FindItem($hWnd, "微软拼音输入法3.0版")
_GUICtrlTreeView_SelectItem($hWnd, $hItem)
Send("!r")

$hItem = _GUICtrlTreeView_FindItem($hWnd, "中文 (简体) - 智能 ABC")
_GUICtrlTreeView_SelectItem($hWnd, $hItem)
Send("!r")

$hItem = _GUICtrlTreeView_FindItem($hWnd, "中文(简体) - 全拼")
_GUICtrlTreeView_SelectItem($hWnd, $hItem)
Send("!r")

$hItem = _GUICtrlTreeView_FindItem($hWnd, "中文(简体) - 郑码")
_GUICtrlTreeView_SelectItem($hWnd, $hItem)
Send("!r")

ControlClick("文字服务和输入语言", "", "[CLASS:Button; TEXT:确定]")
WinWaitClose("文字服务和输入语言")

ControlClick("区域和语言选项", "", "[CLASS:Button; TEXT:确定]")
WinWaitClose("区域和语言选项")
