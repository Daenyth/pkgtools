#!/usr/bin/env python3

###
# pkgconflict.py -- check a binary .pkg.tar.gz file for conflicts with
# existing packages.
# This program is a part of pkgtools

# Copyright (C) 2009-2010 Chris Brannon <cmbrannon79 _AT_ gmail _DOT_ com>
#
# Pkgtools is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# Pkgtools is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
##

import os
import sys
import tarfile
import gzip

def chomp(x): return x[0:-1]
def isfilename(x): return not x.endswith('/')

def read_file_lists(list_base):
  """Snarf filelists into memory; return hash mapping filenames to
  (repo, package) tuples."""
  known_files = {}
  repos = (p for p in os.listdir(list_base))
  for repo in repos:
    repopath = os.path.join(FILELIST_DIR, repo)
    magic = '070707' # cpio magic (old binary format)
    header = 6+6+6+6+6+6+6+6+11+6+11 # portable ASCII header
    end = 'TRAILER!!!' # end of cpio archive
    try:
      fp = open(repopath, 'r')
      lines = fp.readlines()
    except UnicodeDecodeError: # if it's a gzip file
      fp = gzip.open(repopath, 'rt')
      lines = fp.readlines()
    for l in range(0, len(lines)-1):
      file = lines[l][:-1]
      if file[0:1] != '/': # if it's a package
        package = file[header:-6-2]
        while True: # find files
          l += 1
          file = lines[l][:-1]
          if file[:6] == magic or file[-10:] == end: # go to next package
            break
          else:
            if file[-1:] != '/':
              known_files[file[1:]] = (repo[:-6], package[:package.find('-')])
  return known_files

def list_package_contents(package):
  """Return a list containing the names of the files in the tarball.
  Removes the entries .INSTALL and .PKGINFO."""
  tarball = tarfile.open(package, 'r:xz')
  names = tarball.getnames()
  tarball.close()
  try:
    del names[names.index('.PKGINFO')]
    del names[names.index('.INSTALL')]
    del names[names.index('.MTREE')]
  except ValueError:
    pass
  return names

HOME = os.environ['HOME']
CONFIG_DIR = '/etc/pkgtools'
FILELIST_DIR = '/var/cache/pkgfile'
try:
  with open(sys.argv[1]) as f:
    pass
except (IndexError, FileNotFoundError):
    sys.stderr.write('Usage: %s <PACKAGEFILE>\n' % (sys.argv[0], ))
    sys.exit(1)
known_files = read_file_lists(FILELIST_DIR)
pkg_contents = list_package_contents(sys.argv[1])
for file in pkg_contents:
  if file in known_files:
    (repo, package) = known_files[file]
    print("%s already provided by the %s package from [%s]" % (file, package, repo))
