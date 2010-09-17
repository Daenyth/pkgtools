#!/usr/bin/python

###
# alpm2sqlite.py -- convert an alpm like database to a sqlite one
# This program is a part of pkgtools

# Copyright (C) 2010 solsTiCe d'Hiver <solstice.dhiver@gmail.com>
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

import sys
import os
import tarfile
import cPickle
import zlib
import sqlite3
from datetime import datetime

def die(n=-1, msg='Unknown error'):
    print >> sys.stderr, msg
    sys.exit(n)

# _getsection and parse_* functions are borrowed from test/pacman/pmdb.py

def _getsection(fd):
    i = []
    while True:
        line = fd.readline().strip("\n")
        if not line:
            break
        i.append(line)
    return i

# parse_* function parse files found in pacman repo

def parse_files(pkg, f):
    '''parse a files file'''

    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip("\n")
        if line == "%FILES%":
            pkg['files'] = []
            while line:
                line = f.readline().strip("\n")
                #if line and not line.endswith("/"):
                # also pick the directories
                if line:
                    pkg['files'].append(line)
        if line == "%BACKUP%":
            pkg['backup'] = _getsection(f)

def parse_desc(pkg, f):
    '''parse a desc file'''

    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip("\n")
        if line == "%NAME%":
            pkg['name'] = f.readline().strip("\n")
        if line == "%FILENAME%":
            pkg['filename'] = f.readline().strip("\n")
        elif line == "%VERSION%":
            pkg['version'] = f.readline().strip("\n")
        elif line == "%DESC%":
            pkg['desc'] = f.readline().strip("\n")
        elif line == "%GROUPS%":
            pkg['groups'] = _getsection(f)
        elif line == "%URL%":
            pkg['url'] = f.readline().strip("\n")
        elif line == "%LICENSE%":
            pkg['license'] = _getsection(f)
        elif line == "%ARCH%":
            pkg['arch'] = f.readline().strip("\n")
        # directly keep the datetime instead of the timestamp (using local tz ?)
        elif line == "%BUILDDATE%":
            try:
                pkg['builddate'] = datetime.fromtimestamp(int(f.readline().strip("\n")))
            except ValueError:
                pkg['builddate'] = None
        elif line == "%INSTALLDATE%":
            try:
                pkg['installdate'] = datetime.fromtimestamp(int(f.readline().strip("\n")))
            except ValueError:
                pkg['installdate'] = None
        elif line == "%PACKAGER%":
            pkg['packager'] = f.readline().strip("\n")
        elif line == "%REASON%":
            pkg['reason'] = int(f.readline().strip("\n"))
        elif line == "%SIZE%" or line == "%ISIZE%":
            pkg['isize'] = int(f.readline().strip("\n"))
        elif line == "%CSIZE%":
            pkg['csize'] = int(f.readline().strip("\n"))
        elif line == "%MD5SUM%":
            pkg['md5sum'] = f.readline().strip("\n")
        elif line == "%REPLACES%":
            pkg['replaces'] = _getsection(f)
        elif line == "%FORCE%":
            f.readline()
            pkg['force'] = 1

def parse_depends(pkg, f):
    '''parse a depends file'''

    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip("\n")
        if line == "%DEPENDS%":
            pkg['depends'] = _getsection(f)
        elif line == "%OPTDEPENDS%":
            pkg['optdepends'] = _getsection(f)
        elif line == "%CONFLICTS%":
            pkg['conflicts'] = _getsection(f)
        elif line == "%PROVIDES%":
            pkg['provides'] = _getsection(f)

# helper dict to call the correct function given the file to be parsed
parsers = {'files':parse_files, 'depends':parse_depends, 'desc':parse_desc}

# for extra.files.tar.gz
#          (1)   (2)    (3)     (4)
# Time     ~31s   ~34s  ~33s    ~33s
# Size     46MB   49MB  7.9MB   8.3MB
# (1) without zlib, pickle protocol -1
# (2) without zlib, no pickle protocol
# (3) with zlib, no pickle protocol
# (4) with zlib, pickle protocol -1

def adapt_list(L):
    '''pickle and zlib compress lists automatically'''
    # use a buffer to force a BLOB type in sqlite3
    return buffer(zlib.compress(cPickle.dumps(L)))

def convert_list(s):
    '''pickle and zlib compress lists automatically'''
    return cPickle.loads(zlib.decompress(s))

# Register the adapter
sqlite3.register_adapter(list, adapt_list)

# Register the converter
sqlite3.register_converter("list", convert_list)

# sqlite3 module include already adapter/converter for datetime.datetime
# That's why you'll see datetime in the create statement below

def open_db(dbfile):
    '''open or create the sqlite3 dbfile and the db; check integrity'''

    conn = sqlite3.connect(dbfile, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.text_factory = str
    conn.row_factory = sqlite3.Row
    # check the integrity of the db
    try:
        row = conn.execute('PRAGMA INTEGRITY_CHECK').fetchone()
    except sqlite3.DatabaseError:
        die(2, 'Error: %s does not seem to be a sqlite3 db.' % dbfile)
    if row[0] != 'ok':
        die(2, 'Error: the db %s is corrupted' % dbfile)

    # do not sync to disk. If the OS crashes, the db could be corrupted.
    conn.execute('PRAGMA SYNCHRONOUS=0')

    # try to get speed. Useless ?
    conn.execute('PRAGMA journal_mode=PERSIST')

    # create the db if it's not already there
    conn.execute('''CREATE TABLE IF NOT EXISTS pkg(
        name        TEXT,
        filename    TEXT,
        version     TEXT,
        desc        TEXT,
        url         TEXT,
        packager    TEXT,
        md5sum      TEXT,
        arch        TEXT,
        builddate   DATETIME,
        installdate DATETIME,
        isize       INTEGER,
        csize       INTEGER,
        reason      INTEGER,
        license     LIST,
        groups      LIST,
        depends     LIST,
        optdepends  LIST,
        conflicts   LIST,
        provides    LIST,
        replaces    LIST,
        files       LIST,
        backup      LIST,
        force       INTEGER)''')

    cur = conn.cursor()

    return (conn, cur)

def commit_pkg(pkg, conn, cur, verbose):
    '''add a pkg to the sqlite3 db (or update it if already there)'''

    try:
        row = cur.execute('SELECT rowid FROM pkg WHERE name=?', (pkg['name'],)).fetchone()
        if row is not None:
            #if verbose:
            #    # we could only show the pkgname because convert_tarball pass only
            #    # incomplete pkg dict
            #    print ':: Updating %s' % pkg['name']
            cur.execute('UPDATE pkg SET '+','.join('%s=:%s' % (p,p) for p in pkg)+ ' WHERE name=:name', pkg)
        else:
            #if verbose:
            #    # same remark as above
            #    print ':: Adding %s' % pkg['name']
            cur.execute('INSERT INTO pkg ('+','.join(p for p in pkg)+') VALUES('+ ','.join(':%s' % p for p in pkg)+')', pkg)
        conn.commit()
    except sqlite3.Error as e:
        die(1, 'SQLite3 %s' % e)

def convert_tarball(tf, conn, cur, verbose):
    '''convert a .files.tar.gz to a sqlite3 db'''

    # Do not try to create a complete pkg dict
    # but instead commit to db as soon as we have parsed a file

    # Loop through the tarinfo(ti) of the tarfile(tf)
    for ti in tf:
        if ti.isfile():
            f = tf.extractfile(ti)
            fname = os.path.basename(ti.name)
            if fname not in ('desc', 'depends', 'files'):
                continue
            pkgdir = os.path.basename(os.path.dirname(ti.name))
            pkgname = '-'.join(pkgdir.split('-')[:-2])
            # use pkgver from pkgdir because some repo do not include desc in their
            # *.files.tar.gz (arch-games for example)
            pkgver = '-'.join(pkgdir.split('-')[-2:])
            pkg = {'name':pkgname, 'version':pkgver}
            parsers[fname](pkg, f)
            f.close()

            commit_pkg(pkg, conn, cur, verbose)

def convert_dir(path, conn, cur, verbose):
    '''convert a repo dir "pacman style" to a sqlite3 db'''

    for pkgdir in sorted(os.listdir(path)):
        pkgpath = '/'.join((path, pkgdir))
        pkgname = '-'.join(pkgdir.split('-')[:-2])
        pkgver = '-'.join(pkgdir.split('-')[-2:])
        pkg = {'name':pkgname, 'version':pkgver} # just to be safe

        for fname in ('desc', 'depends', 'files'):
            pathfile = os.path.join(pkgpath, fname)
            if os.path.exists(pathfile):
                with open(pathfile) as f:
                    parsers[fname](pkg, f)

        commit_pkg(pkg, conn, cur, verbose)

def update_repo_from_tarball(tf, conn, cur, verbose):
    '''update sqlite db from a repo directory
    This function avoids parsing unnecessary files'''

    # list only the directory from tarball
    dirs = [ti.name for ti in tf if ti.isdir()]

    # look for new or changed packages
    for pkgdir in sorted(dirs):
        # get name and version from dir name
        pkgname = '-'.join(pkgdir.split('-')[:-2])
        pkgver = '-'.join(pkgdir.split('-')[-2:])

        oldpkg = cur.execute('SELECT version FROM pkg WHERE name=?', (pkgname,)).fetchone()
        # If not in the db or a different version, include or update it
        update = 0
        if not oldpkg:
            update = 1
        elif oldpkg['version'] != pkgver:
            update = 2
        if update > 0:
            if verbose:
                if update == 1:
                    print ':: Adding %s-%s' % (pkgname, pkgver)
                elif update == 2:
                    print ':: Updating %s (%s -> %s)' % (pkgname, oldpkg['version'], pkgver)
            pkg = {'name':pkgname, 'version':pkgver} # just to be safe

            # parse files again
            for fname in ('desc', 'depends', 'files'):
                pathfile = os.path.join(pkgdir, fname)
                try:
                    f = tf.extractfile(pathfile)
                    parsers[fname](pkg, f)
                except KeyError:
                    pass

            commit_pkg(pkg, conn, cur, verbose)

    # check for removed package
    rows = cur.execute('SELECT name,version FROM pkg')
    pkgs = rows.fetchmany()

    while pkgs:
        for pkg in pkgs:
            pkgname, pkgver = pkg
            # look for the directory in our self-made list
            d = '%s-%s' %( pkgname, pkgver)
            if d not in dirs:
                if verbose:
                    print ':: Removing %s-%s' % (pkgname, pkgver)
                cur.execute('DELETE FROM pkg WHERE name=?', (pkgname,))
                conn.commit()
        pkgs = rows.fetchmany()

def update_repo_from_dir(path, conn, cur, verbose):
    '''update sqlite db from a repo directory
    This function avoids parsing unnecessary files and a lot of I/O'''

    # look for new or changed packages
    for pkgdir in sorted(os.listdir(path)):
        # get name and version from dir name
        pkgname = '-'.join(pkgdir.split('-')[:-2])
        pkgver = '-'.join(pkgdir.split('-')[-2:])

        oldpkg = cur.execute('SELECT version FROM pkg WHERE name=?', (pkgname,)).fetchone()
        # If not in the db or a different version, include or update it
        update = 0
        if not oldpkg:
            update = 1
        elif oldpkg['version'] != pkgver:
            update = 2
        if update > 0:
            if verbose:
                if update == 1:
                    print ':: Adding %s-%s' % (pkgname, pkgver)
                elif update == 2:
                    print ':: Updating %s (%s -> %s)' % (pkgname, oldpkg['version'], pkgver)
            pkgpath = '/'.join((path, pkgdir))
            pkg = {'name':pkgname, 'version':pkgver} # just to be safe

            # parse files again
            for fname in ('desc', 'depends', 'files'):
                pathfile = os.path.join(pkgpath, fname)
                if os.path.exists(pathfile):
                    with open(pathfile) as f:
                        parsers[fname](pkg, f)

            commit_pkg(pkg, conn, cur, verbose)

    # check for removed package
    rows = cur.execute('SELECT name,version FROM pkg')
    pkgs = rows.fetchmany()

    while pkgs:
        for pkg in pkgs:
            pkgname, pkgver = pkg
            # look for the directory in the alpm db
            d = os.path.join(path, '%s-%s' %( pkgname, pkgver))
            if not os.path.isdir(d):
                if verbose:
                    print ':: Removing %s-%s' % (pkgname, pkgver)
                cur.execute('DELETE FROM pkg WHERE name=?', (pkgname,))
                conn.commit()
        pkgs = rows.fetchmany()

def convert(path, dbfile, verbose):
    '''wrapper around convert_dir and convert_tarball'''

    tf = None
    if isinstance(path, str):
        if os.path.isfile(path):
            try:
                tf = tarfile.open(path)
            except tarfile.TarError as t:
                print >> sys.stderr, 'Error: Unable to open %s' % path
                raise t
    else:
        # if it's a file like object
        try:
            tf = tarfile.open(fileobj=path)
        except tarfile.TarError as t:
            print >> sys.stderr, 'Error: Not a tar file'
            raise t

    try:
        update = os.path.exists(dbfile)
        conn, cur = open_db(dbfile)
        if update:
            # update db if it exists already
            if tf is not None:
                update_repo_from_tarball(tf, conn, cur, verbose)
            else:
                update_repo_from_dir(path, conn, cur, verbose)
            # compact the db
            cur.execute('VACUUM;');
        else:
            # else make the conversion
            if tf is not None:
                convert_tarball(tf, conn, cur, verbose)
            else:
                convert_dir(path, conn, cur, verbose)
        cur.close()
        conn.close()
    except sqlite3.OperationalError as e:
        die(1, 'Error: %s' % e)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print '''Usage: %s [directory|somedb.files.tar.gz]
Convert an alpm directory or a .files.tar.gz file to a sqlite db file''' % sys.argv[0]
        sys.exit(1)

    path = sys.argv[1]
    if os.path.isdir(path):
        dbfile = os.path.basename('%s.db' % path.rstrip('/'))
        print ':: converting %s repo into %s' % (path, dbfile)
    elif os.path.isfile(path):
        if path.endswith('.files.tar.gz'):
            dbfile = path.replace('.files.tar.gz', '.db')
        else:
            dbfile = path+'.db' # ??
        print ':: converting %s file into %s' % (path, dbfile)

    sys.exit(convert(path, dbfile, True))
