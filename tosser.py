#!/usr/bin/python

import re
import sys
import pprint
import argparse
from stat import *
from os import listdir,stat
from os.path import isfile,join,splitext,split,basename

### This python script uses tabs!

parser = argparse.ArgumentParser(description="{0} - clean up the backup cruft".format(sys.argv[0]))
parser.add_argument('-d', '--directory', required=True, dest='startdir', help="The directory to analyze for moldy backups.")
args = parser.parse_args()

class BackupFile(object):
	def __init__(self, fullfilename):
		pp = pprint.PrettyPrinter(indent=4)
		base,name = split(fullfilename)
		name2,ext2 = splitext(name)
		name3,ext = splitext(name2)
		self.dirname = base
		self.filename = name
		self.extension = join([ext, ext2])
		parts = name3.split('_')
		match = re.search(r'(full|var(?:etc)?|full|root|nexpose(?:\-db)?|nxbackup|home)', parts[0])
		if match:
			self.backupType = parts[0]
		else:
			self.backupType = -1
		try:
			match = re.search(r'^[0-9-]+$', parts[1])
			#print("Parts1: {0} Parts2: {1}".format(parts[1], parts[2]))
		except IndexError, err:
			print("Got {0} elements in parts.".format(len(parts)))
			pp.pprint(name3)
			#exit(1)
		if match:
			self.backupDate = parts[1]
			self.host = parts[2]
		else:
			self.host = parts[1]
			try:
				self.backupDate = parts[2]
			except IndexError, err:
				if 'nxbackup' in self.backupType or \
					'nexpose' in self.backupType:
					self.backupDate = -1
				else:
					print(self.backupType)
					raise(err)
		#print("Base: {0}, Name:{1}, Ext:{2}".format(base, name2, ext))
		fileStats = stat(fullfilename)
		self.fileMode = oct(fileStats.st_mode)
		self.ownerUID = fileStats.st_uid
		self.ownerGID = fileStats.st_gid
		self.size = fileStats.st_size
		self.atime = fileStats.st_atime
		self.mtime = fileStats.st_mtime
		self.ctime = fileStats.st_ctime
		

def main():
	pp = pprint.PrettyPrinter(indent=4)
	# get the files in the start dir
	tarballs = []
	for f in listdir(args.startdir):
		if isfile(join(args.startdir, f)):
			tarballs.append(join(args.startdir, f))
			#print("Directory entity: {0}".format(join(args.startdir, f)))

	print("Got {0} backup files.".format(len(tarballs)))
	for tb in tarballs:
		bak = BackupFile(tb)
		print("Name: {0} Type: {1}, Perms: {2}, \n\tSize: {3}, MTime: {4}".format( \
			bak.filename, bak.backupType, bak.fileMode, bak.size, bak.mtime))
		print("\tBackupDate: {0}, Host: {1}".format(bak.backupDate, bak.host))


if __name__ == '__main__':
	main()
