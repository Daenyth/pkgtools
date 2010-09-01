#!/usr/bin/python
###
# pkgfile.py -- search the arch repo to see what package owns a file
# This program is a part of pkgtools
#
# Copyright (C) 2010 solsTiCe d'Hiver <solstice.dhiver@gmail.com>
#
# original bash version copyright was:
# Copyright (C) 2008-2010 Daenyth <Daenyth+Arch _AT_ gmail _DOT_ com>
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

import glob
import os
import re
import atexit
import sys
import os.path
import optparse
import subprocess
import urllib
import alpm2sqlite
import tarfile

VERSION = '22'
CONFIG_DIR = '/etc/pkgtools'
FILELIST_DIR = '/var/cache/pkgtools/lists'
LOCKFILE = '/var/lock/pkgfile'

def find_dbpath():
    '''find pacman dbpath'''

    p = subprocess.Popen(['pacman', '-v'], stdout=subprocess.PIPE)
    output = p.communicate()[0]
    for line in output.split('\n'):
        if line.startswith('DB Path'):
            return line.split(':')[1].strip()

def parse_config(filename, comment_char='#', option_char='='):
    '''basic function to parse a key=value config file'''
    # Borrowed at http://www.decalage.info/en/python/configparser
    # another option is http://mail.python.org/pipermail/python-dev/2002-November/029987.html

    options = {}
    try:
        with open(filename) as f:
            for line in f:
                line = line.strip()
                if comment_char in line:
                    line, comment = line.split(comment_char, 1)
                if option_char in line:
                    option, value = line.split(option_char, 1)
                    option = option.strip()
                    value = value.strip('"\' ')
                    try:
                        options[option] = int(value)
                    except ValueError:
                        options[option] = value
    except IOError:
        pass
    return options

def load_config(conf_file):
    '''load main config file and try in XDG_CONFIG_HOME too'''

    options = parse_config(os.path.join(CONFIG_DIR, conf_file))
    XDG_CONFIG_HOME = os.getenv('XDG_CONFIG_HOME')
    if  XDG_CONFIG_HOME is not None:
        xdg_conf_file = os.path.join(XDG_CONFIG_HOME, 'pkgtools', conf_file)
        if os.path.exists(xdg_conf_file):
            tmp = parse_config(xdg_conf_file)
            for k in tmp:
                options[k] = os.path.expanduser(tmp[k])
    return options

def die(n=-1, msg='Unknown error'):
    print >> sys.stderr, msg
    sys.exit(n)

# Locking is usefull ? because sqlite3 can handle 2 process writing in a db file.
# This only avoid 2 updates at the same time
# TODO: Look at fcntl.lockf but to lock the db file instead ?
def lock():
    if os.path.exists(LOCKFILE):
        die(1, 'Error: Unable to take lock at %s' % LOCKFILE)
    try:
        with open(LOCKFILE, 'w') as f:
            f.write('%d' % os.getpid())
    except IOError:
        die(1, 'Error: Unable to take lock at %s' % LOCKFILE)

def unlock():
    try:
        if os.path.exists(LOCKFILE):
            os.unlink(LOCKFILE)
    except OSError:
        print >> sys.stderr, 'Warning: Failed to unlock %s' % LOCKFILE

# used below in print_pkg
PKG_ATTRS = ('name', 'filename', 'version', 'url', 'license', 'groups', 'provides',
            'depends', 'optdepends', 'conflicts', 'replaces', 'isize','packager',
            'arch', 'installdate', 'builddate', 'desc')
WIDTH = max(len(i) for i in PKG_ATTRS) + 1

# It's ugly but it does the job
def print_pkg(pkg):
    '''pretty print a pkg dict, mimicking pacman -Qi output'''

    # all attributes are not printed
    for p in PKG_ATTRS:
        field = p.capitalize().ljust(WIDTH)
        try:
            value = pkg[p]
        except KeyError:
            continue
        if value is None:
            print '%s: --' % field
            continue
        if p == 'csize' or p == 'isize':
            print '%s: %d k' % (field, value/1024)
        #elif p == 'force':
        #    print = '%s: %d' % (field, value)
        elif p in ('groups', 'license', 'replaces',  'depends', 'optdepends', 'conflicts', 'provides'):
            print '%s: %s' % (field, '  '.join(value))
        elif p == 'backup':
            s = field+':'
            for i in value:
                s += '\n'+': '.join(i.split('\t')) +'\n'
            else:
                s += ' --'
            print s
        #elif p == 'files':
        #    print '%s: %s' % (field, '\n'+'\n'.join(value))
        else:
            print '%s: %s' % (field, value)
    print

def update_repo(options, target_repo=None):
    '''download .files.tar.gz for each repo found in pacman config or the one specified and convert them to a sqlite3 db'''

    if not os.path.exists(FILELIST_DIR):
        print >> sys.stderr, 'Warning: %s does not exist. Creating it.' % FILELIST_DIR
        try:
            os.mkdir(FILELIST_DIR, 0755)
        except OSError:
            die(1, 'Error: Can\'t create %s directory' % FILELIST_DIR)

    # check if FILELIST_DIR is writable
    if not os.access(FILELIST_DIR, os.F_OK|os.R_OK|os.W_OK|os.X_OK):
        die(1, 'Error: %s is not accessible' % FILELIST_DIR)

    p = subprocess.Popen(['pacman', '--debug'], stdout=subprocess.PIPE)
    output = p.communicate()[0]

    # get a list of repo and mirror
    res = []
    server = re.compile(r'.*adding new server URL to database \'(.*)\': (.*)')
    for line in output.split('\n'):
        m = server.match(line)
        if m:
            res.append((m.group(1), m.group(2)))

    # ok. so here we go
    lock()

    repo_done = []
    for repo, mirror in res:
        if target_repo is not None and repo != target_repo:
            continue
        if repo not in repo_done:
            print ':: Downloading [%s] file list ...' % repo
            repofile = '%s.files.tar.gz' % repo
            filelist = os.path.join(mirror, repofile)

            try:
                if options.verbose:
                    print 'Trying mirror %s ...' % mirror
                filename, headers = urllib.urlretrieve(filelist)
                # tmp file will be automatically deleted after the process dies

                print ':: Converting [%s] file list ...' % repo
                # TODO: catch error better
                try:
                    alpm2sqlite.convert(filename, '%s/%s.db' % (FILELIST_DIR, repo), options)
                    repo_done.append(repo)
                    print 'Done'
                except tarfile.TarError:
                    # error already printed in convert
                    pass
            except IOError:
                print >> sys.stderr, 'Warning: could not retrieve %s' % filelist
                continue

    local_db = os.path.join(FILELIST_DIR, 'local.db')

    if target_repo is None or target_repo == 'local':
        print ':: Converting local repo ...'
        local_dbpath = os.path.join(find_dbpath(), 'local')
        alpm2sqlite.convert(local_dbpath, local_db, options)
        print 'Done'

    # remove left-over db (for example for repo removed from pacman config)
    repos = glob.glob(os.path.join(FILELIST_DIR, '*.db'))
    registered_repos = set(os.path.join(FILELIST_DIR, r[0]+'.db') for r in res)
    registered_repos.add(local_db)
    for r in repos:
        if r not in registered_repos:
            print ':: Deleting %s' % r
            os.unlink(r)

    unlock()

def check_FILELIST_DIR():
    '''check if FILELIST_DIR exists and contais any *.db file'''

    if not os.path.exists(FILELIST_DIR):
        die(1, 'Error: %s does not exist. You might want to run "pkgfile -u" first.' % FILELIST_DIR)
    if len(glob.glob(os.path.join(FILELIST_DIR, '*.db'))) ==  0:
        die(1, 'Error: You need to run "pkgfile -u" first.')

def regex_search(expr, s):
    regex = re.compile(expr)
    return regex.match(s) is not None

def list_files(s, options):
    '''list files of package matching s'''

    check_FILELIST_DIR()

    target_repo = ''
    if '/' in s:
        res = s.split('/')
        if len(res) > 2:
            print >> sys.stderr, 'If given foo/bar, assume "bar" package in "foo" repo'
            return
        target_repo, pkg = res
    else:
        pkg = s

    sql_stmt, search = ('SELECT name,files FROM pkg WHERE name=?' , (pkg,))
    if options.glob:
        sql_stmt, search = ('SELECT name,files FROM pkg WHERE name LIKE ?' , (pkg.replace('*', '%').replace('?', '_'),))
    elif options.regex:
        sql_stmt, search = ('SELECT name,files FROM pkg WHERE name REGEXP ?' , (pkg,))

    res = []
    local_db = os.path.join(FILELIST_DIR, 'local.db')
    if options.local:
        repo_list = [local_db]
    else:
        repo_list = glob.glob(os.path.join(FILELIST_DIR, '*.db'))
        del repo_list[repo_list.index(local_db)]

    foundpkg = False
    for dbfile in repo_list:
        repo = os.path.basename(dbfile).replace('.db', '')
        if target_repo != '' and target_repo != repo:
            continue

        conn, cur = alpm2sqlite.open_db(dbfile)
        if options.regex:
            conn.create_function('REGEXP', 2, regex_search)
        rows = cur.execute(sql_stmt, search)
        matches = rows.fetchmany()
        while matches != []:
            foundpkg = True
            for pkg, files in matches:
                for f in sorted(files):
                    if options.binaries:
                        if '/sbin/' in f or '/bin/' in f:
                            print '%s /%s' % (pkg, f)
                    else:
                        print '%s /%s' % (pkg, f)
            matches = rows.fetchmany()

        cur.close()
        conn.close()

    if not foundpkg:
        print 'Package "%s" not found' % pkg,
        if target_repo != '':
            print ' in repo %s' % target_repo,
        print

def query_pkg(filename, options):
    '''search package with a file matching filename'''

    check_FILELIST_DIR()

    if options.glob:
        from fnmatch import translate
        regex = translate(filename)
    elif options.regex:
        regex = filename
    else:
        indx = 1 if filename.startswith('/') else 0
        regex = '.*/' + re.escape(filename[indx:]) + '$'

    flags = 0 if options.case_sensitive else re.IGNORECASE

    try:
        filematch = re.compile(regex, flags)
    except re.error as e:
        die(1, 'Regex Error: %s' % e)

    local_db = os.path.join(FILELIST_DIR, 'local.db')
    if os.path.exists(filename) or options.local:
        repo_list = [local_db]
    else:
        repo_list = glob.glob(os.path.join(FILELIST_DIR, '*.db'))
        del repo_list[repo_list.index(local_db)]

    for dbfile in repo_list:
        conn, cur = alpm2sqlite.open_db(dbfile)
        repo = os.path.basename(dbfile).replace('.db', '')
        rows = cur.execute('SELECT name,version,files FROM pkg')

        pkgfiles = rows.fetchmany()
        # search the package name that have a filename
        res = []
        while pkgfiles != []:
            for n, v, fls in pkgfiles:
                matches = [f for f in sorted(fls) if filematch.match('/'+f)]
                if matches != []:
                    if options.info:
                        res.append((n, matches))
                    else:
                        if options.verbose:
                            print '\n'.join('%s/%s (%s) : /%s' % (repo, n, v, f) for f in matches)
                        else:
                            print '%s/%s' % (repo, n)
            pkgfiles = rows.fetchmany()

        for n, fls in res:
            pkg = cur.execute('SELECT * FROM pkg WHERE name=?', (n,)).fetchone()
            print_pkg(pkg)
            if options.verbose:
                print '\n'.join('%s/%s : /%s' % (repo, n, f) for f in fls) 
                print
        cur.close()
        conn.close()

def main():
    global FILELIST_DIR

    usage = '%prog [ACTIONS] [OPTIONS] filename'
    parser = optparse.OptionParser(usage=usage, version='%%prog %s' % VERSION)
    # actions
    actions = optparse.OptionGroup(parser, 'ACTIONS')
    actions.add_option('-i', '--info', dest='info', action='store_true',
            default=False, help='provides information about the package owning a file')
    actions.add_option('-l', '--list', dest='list', action='store_true',
            default=False, help='list files of a given package; similar to "pacman -Ql"')
    actions.add_option('-s', '--search', dest='search', action='store_true',
            default=True, help='search which package owns a file')
    actions.add_option('-u', '--update', dest='update', action='store_true',
            default=False, help='update to the latest filelist. This requires write permission to %s' % FILELIST_DIR)
    parser.add_option_group(actions)

    # options
    parser.add_option('-b', '--binaries', dest='binaries', action='store_true',
            default=False, help='only show files in a {s}bin/ directory. Works with -s, -l')
    parser.add_option('-c', '--case-sensitive', dest='case_sensitive', action='store_true',
            default=False, help='make searches case sensitive')
    parser.add_option('-g', '--glob', dest='glob', action='store_true',
            default=False, help='allow the use of * and ? as wildcards.')
    parser.add_option('-r', '--regex', dest='regex', action='store_true',
            default=False, help='allow the use of regex in searches')
    parser.add_option('-L', '--local', dest='local', action='store_true',
            default=False, help='search only in the local pacman repository')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
            default=False, help='enable verbose output')

    (options, args) = parser.parse_args()

    # This section is here for backward compatibility
    dict_options = load_config('pkgfile.conf')
    try:
        FILELIST_DIR = dict_options['FILELIST_DIR'].rstrip('/')
    except KeyError:
        pass
    # PKGTOOLS_DIR is meaningless here
    # CONFIG_DIR is useless
    # RATELIMIT is not used yet
    # options are:
    #   * use wget
    #   * make a throttling urlretrieve
    #   * use urlgrabber
    #   * use pycurl
    # CMD_SEARCH_ENABLED is not used here
    # UPDATE_CRON neither 

    if options.glob and options.regex:
        die(1, 'Error: -g/--glob and -r/--regex are exclusive.')

    if options.update:
        try:
            update_repo(options, target_repo=args[0])
        except IndexError:
            update_repo(options)
    elif options.list:
        try:
            list_files(args[0], options)
        except IndexError:
            die(1, 'Error: No target specified to search for !')
    elif options.info or options.search:
        try:
            query_pkg(args[0], options)
        except IndexError:
            die(1, 'Error: No target specified to search for !')

if __name__ == '__main__':
    # be sure to remove the lock at exit or in case of exception
    atexit.register(unlock)

    # This will ensure that any files we create are readable by normal users
    os.umask(0022)

    try:
        main()
    except KeyboardInterrupt:
        print 'Aborted'
