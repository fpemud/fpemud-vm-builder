#include <FvmUtil.au3>

_FvmWinWaitAndActivate("找到新的硬件向导")
Send("{ENTER}")
WinWaitActive("找到新的硬件向导", "完成找到新硬件向导")
Send("{ENTER}")
WinWaitClose("找到新的硬件向导")
