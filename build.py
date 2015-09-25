"""\
Build the current project as a Factorio mod.

Not required, but handy for work on the mod. The basic process is this:

 1. If the git status isn't clean, throw the current stuff into the stash
 2. Get the current version from info.json for the zip name
 3. Zip the current working directory into name_version.zip, in the containing directory
 4. Unstash to restore the directory status. 
"""

import subprocess
import json
from zipfile import ZipFile, ZIP_DEFLATED
import os
import codecs
import sys

def git_is_clean():
	"""
	Return True if `git status` reports clean, otherwise False
	"""
	
	proc = subprocess.Popen(['git', 'status', '--porcelain'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = proc.communicate()
	success = proc.wait() == 0 # gets the return code, False on nonzero
	success = success and len(out) == 0 # false if any standard output
	success = success and len(err) == 0 # false if any standard error
	return success 

def stash():
	"""
	If the current working directory isn't clean as reported by `git status`, stash it and return True.
	
	Otherwise return False.
	"""
	need_unstash = not git_is_clean()
	if need_unstash:
		subprocess.check_call(['git', 'stash'])
		assert git_is_clean()
	
	return need_unstash
	
def unstash():
	subprocess.check_call(['git', 'stash', 'apply'])
	
def form_name(fn='info.json'):
	with file(fn, 'r') as fp:
		info = json.load(fp)
	return '_'.join([info['name'], info['version']])
	
def get_default_path():
	"""\
	Returns the system default path for Factorio mods. 
	
	Derived from <http://www.factorioforums.com/wiki/index.php?title=Modding_overview#Mods_directory>
	
	If it can't figure out the right place to go, defaults to the current working directory. 
	"""
	ret = None
	if sys.platform.startswith('win'):
		ret = '%appdata%\Factorio\mods'
	elif sys.platform.startwsith('linux'):
		ret = '~/.factorio/mods'
	elif sys.platform.startswith('darwin'):
		ret = '~/Library/Application Support/factorio/mods'
	else:
		ret = '.'
	return os.path.expanduser(os.path.expandvars(ret))
		
	
def makezip(name, destpath=None):
	if destpath is None:
		destpath = get_default_path()
	if not os.path.exists(destpath):
		print >> sys.stderr, "'{}' does not exist. Can't write data there!".format(destpath)
		return
	elif not os.path.isdir(destpath):
		print >> sys.stderr, "'{}' is not a directory. Can't write data there!".format(destpath)
		return
		
	path = os.path.join(destpath, name + '.zip')
	failed = None
	with file(path, 'w') as fp:
		with ZipFile(fp, 'w', compression=ZIP_DEFLATED) as zip:
			for dirpath, dirnames, filenames in os.walk('.'):
				# don't add .git to the packed archive
				if '.git' in dirnames:
					dirnames.remove('.git')
				# don't add .gitignore to the packed archive
				# also don't add the current zipfile, if we happen to be working in the CWD
				ignorefiles = ['.gitignore', name + '.zip']
				for ifn in ignorefiles:
					if ifn in filenames:
						filenames.remove(ifn)
				
				for fn in filenames:
					filepath = os.path.join(dirpath, fn)
					# documentation here: http://www.factorioforums.com/wiki/index.php?title=Modding_overview
					# lies about required structure. It says it must be in a folder inside the zip file, but
					# that causes an error on game load.
					
					# zippath  = os.path.join(name, filepath)

					try:
						# zipfile requires that file names be encoded in cp437. 
						filepath = codecs.encode(filepath, 'cp437') 
						# zippath = codecs.encode(zippath, 'cp437') 
					except ValueError, e:
						print >> sys.stderr, "Failed to encode", name
						print >> sys.stderr, e
						failed = e
						break;
						
					# actually add the item to the archive
					zip.write(filepath)
	
	if failed is not None:
		# we had a catastrophic error and don't want to leave a partial file hanging around
		os.remove(path)

if __name__ == '__main__':
	import argparse
	
	desc = __doc__.strip()
	
	parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
	
	parser.add_argument('-o', '--output-directory', metavar="OD", dest='od',
	                    help="specify a directory in which to place the output zip")
	parser.add_argument('-.', '--output-here', action='store_const', dest='od', const='.',
	                    help="store the output in the current dir. Same as '--output-directory .'")
	parser.add_argument('-d', '--detect-directory', action='store_true', default=False,
	                    help="show the detected mods directory on this machine and exit")
	
	args = parser.parse_args()
	
	if args.detect_directory:
		print get_default_path()
		sys.exit(0)
	
	stashed = stash()
	makezip(form_name(), args.od)
	if stashed:
		unstash()