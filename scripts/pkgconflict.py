#!/usr/bin/env python

###
# pkgconflict.py -- check a binary .pkg.tar.gz file for conflicts with
# existing packages.
# This program is a part of pkgtools

# Copyright (C) 2009 Chris Brannon <cmbrannon79 _AT_ gmail _DOT_ com>
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
import subprocess

def chomp(x): return x[0:-1]
def isfilename(x): return not x.endswith('/')

def get_lists_base(configfile):
  """Obtain the name of the directory containing file lists, by reading
  a config file.  Bash parses the file and prints the directory name.
  This function returns a non-empty string on success, or None on error."""
  if not os.access(configfile, os.R_OK):
    return None
  bash = subprocess.Popen(
    ['bash', '-c', 'source %s ; echo $FILELIST_DIR' % (configfile,)],
    stdout=subprocess.PIPE)
  dirname = bash.stdout.readline()
  status = bash.wait()
  if status == 0:
    dirname = chomp(dirname)
    if dirname == "":
      dirname = None
    return dirname
  else:
    return None

def read_file_lists(list_base):
  """Snarf filelists into memory; return hash mapping filenames to
  (repo, package) tuples."""
  known_files = {}
  repos = os.listdir(list_base)
  for repo in repos:
    repopath = os.path.join(FILELIST_DIR, repo)
    packages = os.listdir(repopath)
    for package in packages:
      listfile = open(os.path.join(repopath, package, 'files'))
      listfile.readline() # discard the %files% line
      for entry in filter(isfilename, map(chomp, listfile.readlines())):
        known_files[entry] = (repo, package)
      listfile.close()
  return known_files

def list_package_contents(package):
  """Return a list containing the names of the files in the tarball.
  Removes the entries .INSTALL and .PKGINFO."""
  tarball = tarfile.open(package, 'r:gz')
  names = tarball.getnames()
  tarball.close()
  try:
    del names[names.index('.PKGINFO')]
    del names[names.index('.INSTALL')]
  except ValueError:
    pass
  return names

HOME = os.environ['HOME']
CONFIG_DIR='/etc/pkgtools'
FILELIST_DIR =(get_lists_base(os.path.join(HOME, '.pkgtools', 'pkgfile.conf'))
               or get_lists_base(os.path.join(CONFIG_DIR, 'pkgfile.conf'))
               or '/var/cache/pkgtools/lists')
if len(sys.argv) != 2:
  sys.stderr.write('Usage: %s <PACKAGEFILE>\n' % (sys.argv[0], ))
  sys.exit(1)
known_files = read_file_lists(FILELIST_DIR)
pkg_contents = list_package_contents(sys.argv[1])
for file in pkg_contents:
  if file in known_files:
    (repo, package) = known_files[file]
    print "%s already provided by the %s package from [%s]" % (file, package, repo)
