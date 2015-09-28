"""\
Build the current project as a Factorio mod.

Not required, but handy for work on the mod. The basic process is this:

 1. If the git status isn't clean, throw the current stuff into the stash
 2. Get the current name and version from info.json for the zip name
 3. Find the appropriate output directory
 4. Delete old versions of the output
 3. Zip the current working directory into name_version.zip, in the appropriate directory
 4. Unstash to restore the directory status. 
 
Note: this utility assumes you're using `git`, and builds only what's committed in HEAD. You can't
build what you haven't committed!
"""

import subprocess
import json
from zipfile import ZipFile, ZIP_DEFLATED
import os
import codecs
import sys
from glob import glob

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
	subprocess.check_call(['git', 'stash', 'pop'])
	
def form_name(info):
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
		
def remove_other_versions(path, info):
	"""\
	Remove any other output files from the target directory.
	
	A typical run of this utility will simply overwrite the output zipfile already present. However,
	when the version number changes, a new zipfile will be produced. In the typical case that the
	output is written directoy to the Factorio mods directory, that will cause an error due to 
	conflicting mod versions being present simultaneously. To fix that, we automatically remove 
	old versions from the target directory.
	
	Note: this assumes that the only change between versions is the version number. If the name 
	changes, this *will not* automatically remove the versions with the old name. On the other hand,
	in that case Factorio won't complain about duplicate mods, so it's fine.
	
	This behavior can be suppressed using the `--keep-old-versions` flag.
	"""
	obsolete = info['name'] + '*.zip'
	rmglob = os.path.join(path, obsolete)
	matches = glob(rmglob)
	for match in matches:
		os.remove(match)

def get_destination_path(destpath):
	"""\
	Converts the destination path to a form which is guaranteed not to be None, nonexistent, or not 
	a directory. If None is passed in, returns the default path for this system. If the path is 
	nonexistent or not a directory, returns a ValueError.
	"""
	if destpath is None:
		destpath = get_default_path()
	if not os.path.exists(destpath):
		raise ValueError("'{}' does not exist. Can't write data there!".format(destpath))
	elif not os.path.isdir(destpath):
		raise ValueError("'{}' is not a directory. Can't write data there!".format(destpath))
	return destpath
		
		
def makezip(name, destpath):
	path = os.path.join(destpath, name + '.zip')
	failed = None
	with file(path, 'wb') as fp:
		with ZipFile(fp, 'w', compression=ZIP_DEFLATED) as zip:
			for dirpath, dirnames, filenames in os.walk('.'):
				# don't add .git to the packed archive
				if '.git' in dirnames:
					dirnames.remove('.git')
				# don't add .gitignore to the packed archive
				# also don't add the current zipfile, if we happen to be working in the CWD
				ignorefiles = ['.gitignore', '*.zip']
				for pattern in ignorefiles:
					for match in glob(pattern):
						if match in filenames:
							filenames.remove(ifn)
				
				
				for fn in filenames:
					filepath = os.path.join(dirpath, fn)
					# documentation here: http://www.factorioforums.com/wiki/index.php?title=Modding_overview
					
					zippath  = os.path.join(name, filepath)

					try:
						# zipfile requires that file names be encoded in cp437. 
						filepath = codecs.encode(filepath, 'cp437') 
						zippath = codecs.encode(zippath, 'cp437') 
					except ValueError, e:
						print >> sys.stderr, "Failed to encode", name
						print >> sys.stderr, e
						failed = e
						break;
						
					# actually add the item to the archive
					zip.write(filepath, zippath)
	
	if failed is None:
		with file(path, 'rb') as fp:
			with ZipFile(fp, 'r') as zip:
				failed = zip.testzip()
	
	if failed is not None:
		# we had a catastrophic error and don't want to leave a partial file hanging around
		os.remove(path)
		print >> sys.stderr, "Failed to write", path
	else:
		print "Successfully wrote and tested", path

if __name__ == '__main__':
	# ensure info.json exists and is a valid json file; this utility depends on it
	if not (os.path.exists('info.json') and os.path.isfile('info.json')):
		print >> sys.stderr, "This utility requires info.json to exist in the current directory"
		sys.exit(1)
	with file('info.json', 'r') as fp:
		try:
			info = json.load(fp)
		except ValueError:
			print >> sys.stderr, "Could not decode info.json. Please ensure it is readable and a valid json file."
			sys.exit(1)

	import argparse
	
	desc = __doc__.strip()
	
	parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
	
	parser.add_argument('-o', '--output-directory', metavar="OD", dest='od',
	                    help="specify a directory in which to place the output zip")
	parser.add_argument('-.', '--output-here', action='store_true', dest='local', default=False,
	                    help="store the output in the current dir without deletion. Same as '--output-directory --keep-old-versions.'")
	parser.add_argument('-d', '--detect-directory', action='store_true', default=False,
	                    help="show the detected mods directory on this machine and exit")
	parser.add_argument('-k', '--keep-old-versions', action='store_false', default=True, dest='delete',
	                    help="do not automatically delete old output from the target directory")
	
	args = parser.parse_args()
	
	# -. implies two things: set the destination directory to the current dir, and don't remove old versions.
	# argparse doesn't natively support implication, so we handle it here.
	if args.local:
		args.od = '.'
		args.delete = False
	
	if args.detect_directory:
		print get_default_path()
		sys.exit(0)
	
	stashed = stash()
	
	try:
		path = get_destination_path(args.od)
	except ValueError:
		path = '.'
		args.delete = False
		print >> sys.stderr, "{} doesn't exist or is not a directory; falling through to '.'".format(args.od)
		print >> sys.stderr, "Turning off auto-delete functionality so as not to clobber anything."
	
	if args.delete:
		remove_other_versions(path, info)
		
	makezip(form_name(info), path)
	
	if stashed:
		unstash()