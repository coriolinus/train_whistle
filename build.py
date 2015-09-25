"""
Tool to build the train whistle mod.

Not required, but handy for work on the mod. The basic process is this:

 1. If the git status isn't clean, throw the current stuff into the stash
 2. Get the current version from info.json for the zip name
 3. Zip the current working directory into name_version.zip, in the containing directory
 4. Unstash to restore the directory status. 
"""

import subprocess
import json

def stash():
	pass
	
def unstash():
	pass
	
def form_name():
	pass
	
def makezip(name):
	pass

if __name__ == '__main__':
	import argparse
	
	parser = argparse.ArgumentParser()
	
	args = parser.parse_args()
	
	stashed = stash()
	makezip(form_name())
	if stashed:
		unstash()