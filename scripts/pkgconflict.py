#!/usr/bin/env python
import os
import sys
import tarfile

def chomp(x): return x[0:-1]
def isfilename(x): return not x.endswith('/')

def read_file_lists():
  known_files = {}
  pkgfile_path = "/var/cache/pkgtools/lists"
  repos = os.listdir(pkgfile_path)
  for repo in repos:
    repopath = os.path.join(pkgfile_path, repo)
    packages = os.listdir(repopath)
    for package in packages:
      listfile = open(os.path.join(repopath, package, 'files'))
      listfile.readline() # discard the %files% line
      for entry in filter(isfilename, map(chomp, listfile.readlines())):
        known_files[entry] = (repo, package)
      listfile.close()
  return known_files

def list_package_contents(package):
  tarball = tarfile.open(package, 'r:gz')
  names = tarball.getnames()
  tarball.close()
  try:
    del names[names.index('.PKGINFO')]
  except ValueError:
    pass
  return names

if len(sys.argv) != 2:
  sys.stderr.write('Usage: %s <PACKAGEFILE>\n' % (sys.argv[0], ))
  sys.exit(1)
known_files = read_file_lists()
pkg_contents = list_package_contents(sys.argv[1])
for file in pkg_contents:
  if file in known_files:
    (repo, package) = known_files[file]
    print "%s already provided by the %s package from [%s]" % (file, package, repo)
