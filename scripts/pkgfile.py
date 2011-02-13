#!/usr/bin/python2
###
# pkgfile.py -- search the arch repo to see what package owns a file
# This program is a part of pkgtools
#
# Copyright (C) 2010 solsTiCe d'Hiver <solstice.dhiver@gmail.com>
# Copyright (C) 2008-2011 Daenyth <Daenyth+Arch _AT_ gmail _DOT_ com>
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

import re
import glob
import os
import sys
import optparse
import subprocess
import urllib2
import tarfile
import time
import pkgfile

VERSION = '22'
CONFIG_DIR = '/etc/pkgtools'
FILELIST_DIR = '/var/cache/pkgtools/lists'

def find_dbpath():
    '''find pacman dbpath'''

    p = subprocess.Popen(['pacman', '-Tv'], stdout=subprocess.PIPE)
    output = p.communicate()[0]
    for line in output.split('\n'):
        if line.startswith('DB Path'):
            return line.split(':')[1].strip()
    raise RuntimeError("Unable to determine pacman DB path")

def parse_config(filename, options=None, comment_char='#', option_char='='):
    '''basic function to parse a key=value config file'''
    # Borrowed at http://www.decalage.info/en/python/configparser
    # another option is http://mail.python.org/pipermail/python-dev/2002-November/029987.html

    if options is None:
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

def load_config(conf_file, options=None):
    '''load main config file and try in XDG_CONFIG_HOME too'''

    options = parse_config(os.path.join(CONFIG_DIR, conf_file), options=options)
    XDG_CONFIG_HOME = os.getenv('XDG_CONFIG_HOME')
    if  XDG_CONFIG_HOME is not None:
        xdg_conf_file = os.path.join(XDG_CONFIG_HOME, 'pkgtools', conf_file)
        if os.path.exists(xdg_conf_file):
            local_options = parse_config(xdg_conf_file)
            options.update(local_options)
    return options

def die(n=-1, msg='Unknown error'):
    # TODO: All calls to die() should probably just be exceptions
    print >> sys.stderr, msg
    sys.exit(n)

def print_pkg(pkg):
    '''pretty print a pkg dict, mimicking pacman -Qi output'''

    PKG_ATTRS = ('name', 'version', 'url', 'license', 'groups', 'provides',
            'depends', 'optdepends', 'conflicts', 'replaces',
            'isize','packager', 'arch', 'installdate', 'builddate', 'desc')
    WIDTH = max(len(i) for i in PKG_ATTRS) + 1

    # all attributes are not printed
    for attr in PKG_ATTRS:
        field = attr.capitalize().ljust(WIDTH)
        try:
            value = pkg[attr]
        except KeyError:
            continue
        if value is None:
            print '%s: --' % field
            continue

        if attr == 'csize' or attr == 'isize':
            print '%s: %d k' % (field, value/1024)
        #elif attr == 'force':
        #    print = '%s: %d' % (field, value)
        elif attr in ('groups', 'license', 'replaces',  'depends', 'conflicts', 'provides'):
            print '%s: %s' % (field, '  '.join(value))
        elif attr == 'optdepends':
            print '%s: %s' % (field, ('\n'+(WIDTH+2)*' ').join(value))
        elif attr == 'builddate':
            try:
                print '%s: %s' % (field, time.strftime('%a, %d %b %Y %H:%M:%S',
                    time.localtime(value)))
            except ValueError:
                print '%s: error !' % attr.ljust(22)
        elif attr == 'backup':
            s = field + ':'
            for i in value:
                s += '\n'+': '.join(i.split('\t')) +'\n'
            else:
                s += ' --'
            print s
        #elif attr == 'files':
        #    print '%s: %s' % (field, '\n'+'\n'.join(value))
        else:
            print '%s: %s' % (field, value)
    print

def get_mirrorlist():
    """Return a list of (reponame, mirror_url) for all mirrors known to pacman"""
    p = subprocess.Popen(['pacman', '-T', '--debug'], stdout=subprocess.PIPE)
    output = p.communicate()[0]

    mirrors = []
    server = re.compile(r'.*adding new server URL to database \'(.*)\': (.*)')
    for line in output.split('\n'):
        m = server.match(line)
        if m:
            mirrors.append((m.group(1), m.group(2)))
    return mirrors

def update_repo(options, target_repos=None, filelist_dir=FILELIST_DIR):
    '''download .files.tar.gz for each repo found in pacman config or the one specified'''

    # XXX: This function is way too big. Needs refactoring

    if not os.path.exists(filelist_dir):
        print >> sys.stderr, 'Warning: %s does not exist. Creating it.' % filelist_dir
        try:
            os.mkdir(filelist_dir, 0755)
        except OSError:
            # TODO: raise UpdateFailedError("Failed to create filelist dir: e")...
            die(1, 'Error: Can\'t create %s directory' % filelist_dir)

    # Check here first since we squash IOError later, and it goes into a long
    # loop of repeated errors.
    if not os.access(filelist_dir, os.F_OK|os.R_OK|os.W_OK|os.X_OK):
        die(1, 'Error: %s is not accessible' % filelist_dir)

    mirror_list = get_mirrorlist()
    repo_done = []
    for repo, mirror in mirror_list:
        if target_repos is not None and repo != target_repos:
            continue
        if repo not in repo_done:
            print ':: Checking [%s] for files list ...' % repo
            repofile = '%s.files.tar.gz' % repo
            fileslist = os.path.join(mirror, repofile)

            try:
                if options.verbose:
                    print '    Trying mirror %s ...' % mirror
                dbfile = '%s/%s.files.tar.gz' % (filelist_dir, repo)
                try:
                    # try to get mtime of dbfile
                    local_mtime = os.path.getmtime(dbfile)
                except os.error:
                    local_mtime = 0 # fake a very old date if dbfile doesn't exist
                # Initiate connection to get 'Last-Modified' header
                conn = urllib2.urlopen(fileslist, timeout=30)
                last_modified = conn.info().getdate('last-modified')
                if last_modified is None:
                    should_update = True
                else:
                    remote_mtime = time.mktime(last_modified)
                    should_update = remote_mtime > local_mtime

                if should_update or options.update > 1:
                    if options.verbose:
                        print '    Downloading %s ...' % fileslist
                    f = open(dbfile, 'w')
                    f.write(conn.read())
                    f.close()
                    conn.close()
                else:
                    print '    No update available'
                    conn.close()
                repo_done.append(repo)
            except IOError as e:
                print >> sys.stderr, 'Warning: could not retrieve %s' % fileslist
                if options.verbose:
                    print >> sys.stderr, "         " + str(e)
                continue

    local_db = os.path.join(filelist_dir, 'local.files.tar.gz')

    if target_repos is None or target_repos == 'local':
        update_local_repo(local_db)

    # remove left-over db (for example for repo removed from pacman config)
    # XXX: This should probably be in some type of behavior like pacman -Scc (pkgfile -c[c]?)
    repos = glob.glob(os.path.join(filelist_dir, '*.files.tar.gz'))
    registered_repos = set(os.path.join(filelist_dir, r[0]+'.files.tar.gz') for r in mirror_list)
    registered_repos.add(local_db)
    for r in repos:
        if r not in registered_repos:
            print ':: Deleting %s' % r
            os.unlink(r)

def update_local_repo(local_db):
    """Update the file list for the local repo db."""
    print ':: Converting local repo ...'
    local_dbpath = os.path.join(find_dbpath(), 'local')
    # create a tarball of local repo
    tf = tarfile.open(local_db, 'w:gz')
    cwd = os.getcwd() # save current working directory
    os.chdir(local_dbpath)
    # we don't want a ./ prefix on all the files in the tarball
    for i in os.listdir('.'):
        tf.add(i)
    tf.close()
    os.chdir(cwd) # restore it
    print 'Done'

def is_binary(path):
    """Utility function used to determine whether a file should be displayed under -b"""
    return re.search(r'(?:^|/)s?bin/.', path) != None

def list_files(pkgname, options, filelist_dir=FILELIST_DIR):
    '''list files of package matching pkgname'''

    target_repo = options.repo
    if '/' in pkgname:
        res = pkgname.split('/')
        if len(res) > 2:
            # XXX: This behavior seems to duplicate the -R switch. Maybe we
            #  should pick one and forbid the other. Probably this is the
            #  behavior that should be removed
            print >> sys.stderr, 'If given foo/bar, assume "bar" package in "foo" repo'
            return
        target_repo, pkg = res
    else:
        pkg = pkgname

    local_db = os.path.join(filelist_dir, 'local.files.tar.gz')
    if target_repo:
        tmp = os.path.join(filelist_dir, '%s.files.tar.gz' % target_repo)
        if not os.path.exists(tmp):
            die(1, 'Error: %s repo does not exist' % target_repo)
        repo_list = [tmp]
    else:
        repo_list = glob.glob(os.path.join(filelist_dir, '*.files.tar.gz'))
        try:
            del repo_list[repo_list.index(local_db)]
        except ValueError:
            # TODO: Replace with custom NoFileDBError class
            raise RuntimeError("No local file db found. Run --update")

    try:
        if options.glob:
            match_type = pkgfile.MATCH_SHELL
        elif options.regex:
            match_type = pkgfile.MATCH_REGEX
        else:
            match_type = pkgfile.MATCH_SIMPLE
        search = pkgfile.Search(match_type, pkgfile.SEARCH_PACKAGE, pkg)
    except pkgfile.RegexError:
        die(1, 'Error: invalid pattern or regular expression')

    found_pkg = False
    for dbfile in repo_list:
        repo = os.path.basename(dbfile).replace('.files.tar.gz', '')

        matches = search(dbfile)
        # XXX: nested loop, investigate options
        for match in sorted(matches):
            for file_ in sorted(match['files']):
                if options.binaries:
                    if is_binary(file_):
                        print '%s /%s' % (match['name'], file_)
                        found_pkg = True
                else:
                    print '%s /%s' % (match['name'], file_)
                    found_pkg = True

    if not found_pkg:
        print 'Package "%s" not found' % pkg,
        if target_repo != '':
            print ' in [%s] repo ' % target_repo,
        print

def query_pkg(filename, options, filelist_dir=FILELIST_DIR):
    '''search package with a file matching filename'''

    try:
        search_type = pkgfile.SEARCH_FILENAME
        if options.glob:
            match_type = pkgfile.MATCH_SHELL
            search_type = pkgfile.SEARCH_PATH
        elif options.regex:
            match_type = pkgfile.MATCH_REGEX
            search_type = pkgfile.SEARCH_PATH
        else:
            match_type = pkgfile.MATCH_SIMPLE
            if filename.startswith('/'):
                search_type = pkgfile.SEARCH_PATH
                filename = filename.lstrip('/')
        search = pkgfile.Search(match_type, search_type, filename)
    except pkgfile.RegexError:
        die(1, 'Error: invalid pattern or regular expression')

    target_repos = options.repo
    local_db = os.path.join(filelist_dir, 'local.files.tar.gz')
    if target_repos:
        tmp = os.path.join(filelist_dir, '%s.files.tar.gz' % target_repos)
        if not os.path.exists(tmp):
            die(1, 'Error: %s repo does not exist' % target_repos)
        repo_list = [tmp]
    elif os.path.exists(filename) or target_repos == 'local':
        repo_list = [local_db]
    else:
        repo_list = glob.glob(os.path.join(filelist_dir, '*.files.tar.gz'))
        del repo_list[repo_list.index(local_db)]

    for dbfile in repo_list:
        # search the package name that have a filename
        matches = search(dbfile)
        repo = os.path.basename(dbfile).replace('.files.tar.gz', '')

        res = []
        for match in matches:
            files = match['files']
            if options.binaries:
                files = filter(is_binary, files)
            if files != []:
                if options.info:
                    pkg = pkgfile.pkg_info(dbfile, [match['name']])[0]
                    print_pkg(pkg)
                    if options.verbose:
                        print '\n'.join('%s/%s : /%s' % (repo, match['name'], f) for f in files)
                        print
                else:
                    if options.verbose:
                        print '\n'.join('%s/%s (%s) : /%s' % (repo, match['name'], match['version'], f) for f in files)
                    else:
                        print '%s/%s' % (repo, match['name'])

def main():
    # This section is here for backward compatibility
    dict_options = load_config('pkgfile.conf')
    try:
        filelist_dir = os.path.expanduser(dict_options['FILELIST_DIR'].rstrip('/'))
    except KeyError:
        filelist_dir = FILELIST_DIR
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
    actions.add_option('-u', '--update', dest='update', action='count',
            default=0, help='update to the latest filelist. This requires write permission to %s' % filelist_dir)
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
    parser.add_option('-R', '--repo', dest='repo', action='store',
            default='', help='search only in the specified repository')
    parser.add_option('-v', '--verbose', dest='verbose', action='store_true',
            default=False, help='enable verbose output')

    (options, args) = parser.parse_args()

    if options.glob and options.regex:
        die(1, 'Error: -g/--glob and -r/--regex are exclusive.')

    if options.update:
        try:
            update_repo(options, filelist_dir=filelist_dir, target_repos=args[0])
        except IndexError:
            update_repo(options, filelist_dir=filelist_dir)
    elif options.list:
        try:
            list_files(args[0], options, filelist_dir=filelist_dir)
        except IndexError:
            parser.print_help()
            die(1, 'Error: No target specified')
    elif options.info or options.search:
        try:
            query_pkg(args[0], options, filelist_dir=filelist_dir)
        except IndexError:
            parser.print_help()
            die(1, 'Error: No target specified')

if __name__ == '__main__':
    # This will ensure that any files we create are readable by normal users
    # TODO: Move to more relevent section
    os.umask(0022)

    try:
        main()
    except KeyboardInterrupt:
        print 'Aborted'
