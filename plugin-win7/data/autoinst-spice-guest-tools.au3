#RequireAdmin

Run("spice-guest-tools-0.52.exe")

WinWaitActive("SPICE Guest Tools Installer", "Welcome to the SPICE Guest Tools Setup Wizard")
Send("{ENTER}")

WinWaitActive("SPICE Guest Tools Installer", "License Agreement")
Send("{ENTER}")

WinWaitActive("SPICE Guest Tools Installer", "Completing the SPICE Guest Tools Setup Wizard")
Send("{ENTER}")

WinWaitClose("SPICE Guest Tools Installer")
