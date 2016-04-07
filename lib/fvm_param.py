#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os


class FvmParam:

    def __init__(self):
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.pwd = os.getcwd()

        self.libDir = "/usr/lib/fpemud-vmake"
        self.tmpDir = ""

        self.macOuiBr = "00:50:00"
        self.macOuiVm = "00:50:01"

        self.spicePortStart = 5910
        self.spicePortEnd = 5999
