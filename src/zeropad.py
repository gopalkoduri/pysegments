#!/usr/bin/env python
#NOT USED ANYMORE!

from os import listdir, rename
import sys


folder = sys.argv[1]+"/"

for oldName in listdir(folder):
	if oldName[-4:] == ".sig":
		parts = oldName.strip(".sig").split("_")
		newName = folder+"%s%003d%s" %(parts[0]+"_", int(parts[1]), ".sig")
		print newName
		rename(folder+oldName, newName)
