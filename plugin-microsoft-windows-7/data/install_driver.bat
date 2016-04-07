"autoit\autoit3.exe" autoinst-spice-guest-tools.au3

@rem "the driver can only be installed by temporarily installing a non-exist device"

rem devcon install "win7\@@arch@@\BALLOON.inf" "PCI\VEN_1AF4&DEV_1002&SUBSYS_00051AF4&REV_00"
rem devcon remove "PCI\VEN_1AF4&DEV_1002&SUBSYS_00051AF4&REV_00"

rem devcon install "win7\@@arch@@\VIOSCSI.inf" "PCI\VEN_1AF4&DEV_1004&SUBSYS_00000000"
rem devcon remove "PCI\VEN_1AF4&DEV_1004&SUBSYS_00000000"
