#!/usr/bin/python

import re
import pwd
import sys
import time
import pprint
import argparse
from datetime import datetime
from stat import *
from os import listdir,stat,remove
from os.path import isfile,join,splitext,split,basename

### This python script uses tabs!

parser = argparse.ArgumentParser(description="{0} - clean up the backup cruft".format(sys.argv[0]))
parser.add_argument('action', metavar='action', type=str, nargs=1, 
	help="What do you want me to do with the backups?  Valid actions are: show, delete, move, test")
parser.add_argument('-d', '--directory', required=True, dest='startdir', \
	help="The directory to analyze for moldy backups.")
parser.add_argument('-p', '--period', required=False, dest='period', type=int, default=90, \
	help="The retention period for backup files.")
args = parser.parse_args()

class BackupFile(object):
	@staticmethod
	def _parse_backup_date(datestr):
		"""
		Take extrapolated date string input from
		file name and return datetime.datetime object.
		"""
		# YYYY-mm-dd-HH-MM-SS
		try:
			(year, month, day, hour, mins, secs) = datestr.split('-')
			dt = datetime(int(year), int(month), int(day), \
				int(hour), int(mins), int(secs))
		except ValueError, err:
			if not len(datestr) > 8:
				return -1
			else:
				print("|{0}|".format(datestr))
				raise(err)
		return dt
		
	def __init__(self, fullfilename):
		pp = pprint.PrettyPrinter(indent=4)
		base,name = split(fullfilename)
		name2,ext2 = splitext(name)
		name3,ext = splitext(name2)
		self.dirname = base
		self.filename = name
		self.extension = "".join([ext, ext2])
		parts = name3.split('_')
		match = re.search(r'^(full|var(?:etc)?|root|nexpose(?:\-db)?|nxbackup|home|nightlyscandata)$', parts[0])
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
			self.backupDate = self._parse_backup_date(parts[1])
			self.host = parts[2]
		else:
			self.host = parts[1]
			try:
				self.backupDate = self._parse_backup_date(parts[2])
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
		self.dt_atime = datetime.fromtimestamp(fileStats.st_atime)
		self.mtime = fileStats.st_mtime
		self.dt_mtime = datetime.fromtimestamp(fileStats.st_mtime)
		self.ctime = fileStats.st_ctime
		self.dt_ctime = datetime.fromtimestamp(fileStats.st_ctime)
		
def test():
	# create a bogus backup objects and then print all the properties
	###
	# print the simplest methods (size_gb, etyc.)
	backup = BackupFile('/opt/backups/home_is-vmcrbn-p01.sempra.com_2017-11-11-03-01-01.tar.xz')
	test_message = """

Using file /opt/backups/home_is-vmcrbn-p01.sempra.com_2017-11-11-03-01-01.tar.xz
	for testing purposes.

File dir name:		{12}
	(type):		{15}
File name:		{13}
	(type):		{16}
File extension:		{14}
	(type):		{17}
Backup Type:		{30}
	(type):		{31}
File Mode: 		{0}
	(type):		{18}
Owner UID:		{1}
	(type):		{19}
Owner GID:		{2}
	(type):		{20}
File Size (bytes):	{3}
	(type):		{21}
File atime:		{4}
	(type):		{22}
File atime (DT):	{5}
	(type):		{23}
File mtime:		{6}
	(type):		{24}
File mtime (DT):	{7}
	(type):		{25}
File ctime:		{8}
	(type):		{26}
File ctime: (DT):	{9}
	(type):		{27}
Backup Date:		{10}
	(type):		{28}
Backup Host:		{11}
	(type):		{29}
	"""
	print(test_message.format(backup.fileMode, backup.ownerUID, backup.ownerGID,
		backup.size,backup.atime, backup.dt_atime, backup.mtime, backup.dt_mtime,
		backup.ctime, backup.dt_ctime, backup.backupDate, backup.host, backup.dirname,
		backup.filename, backup.extension, type(backup.fileMode), type(backup.filename), 
		type(backup.extension), type(backup.fileMode), type(backup.ownerUID), 
		type(backup.ownerGID), type(backup.size), type(backup.atime), type(backup.dt_atime),
		type(backup.mtime), type(backup.dt_mtime), type(backup.ctime), type(backup.dt_ctime),
		type(backup.backupDate), type(backup.host), backup.backupType, type(backup.backupType))) 

def main():
	pp = pprint.PrettyPrinter(indent=4)
	# get the files in the start dir
	tarballs = []
	for f in listdir(args.startdir):
		if isfile(join(args.startdir, f)):
			tarballs.append(join(args.startdir, f))
			#print("Directory entity: {0}".format(join(args.startdir, f)))

	print("Got {0} backup files.".format(len(tarballs)))
	deprecated = []
	dep = {}
	for tb in tarballs:
		bak = BackupFile(tb)
		# if backupDate is -1, then the file wasn't named using the expected
		# convention, or something else when wrong.  Skip it for now.
		if bak.backupDate == -1: continue
		delta = datetime.now() - bak.backupDate
		if delta.days > args.period:
			deprecated.append(bak)
			if not bak.host in dep.keys():
				dep[bak.host] = []
			dep[bak.host].append(bak)
		
	print("Got {0} deprecated backup files.".format(len(deprecated)))
	#for B in deprecated:
	#	print("\t{0}".format(B.filename))
	sorted(dep)
	total_disk = 0
	for host in dep.keys(): 
		for tar in dep[host]:
			total_disk += tar.size
	print("You will save {0} gigabytes when removing the below files.".format((total_disk / 1024 / 1024 / 1024)))
	if 'show' in args.action:
		for host in dep:
			print("{0}: ".format(host))
			for tar in dep[host]:
				print("\t{0}".format(tar.filename))
				print("\trm -vf {0}/{1}".format(tar.dirname, tar.filename))
	elif 'delete' in args.action:
		for host in dep:
			print "{0}: ".format(host)
			for tar in dep[host]:
				print("Removing {0}...".format(tar.filename))
				remove("{0}/{1}".format(tar.dirname, tar.filename))
	else:
		raise Exception("Unrecognized action! ({0})".format(args.action))

if __name__ == '__main__':
	if 'test' in args.action:
		test()
	else:
		main()

