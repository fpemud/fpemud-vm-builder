#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import sys
sys.path.append('../lib')
from fvm_util import FvmUtil

class Test:

	def main(self):
		FvmUtil.createWinUsbImg("abc.img", 1024, "ntfs")

t = Test()
t.main()
