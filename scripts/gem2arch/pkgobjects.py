#!/usr/bin/env python
import gem2archutil as util

class PKGBUILD:
    def __init__(self, gem_spec):
        self.maintainer = self.get_maintainer('/etc/makepkg.conf')
        self.pkgname = "ruby-%s" % (gem_spec.name)
        self.pkgver = gem_spec.version.version
        self.pkgrel = "1"
        self.pkgdesc = self.get_summary(gem_spec.summary)
        self.arch = "('any')"
        self.url = '"%s"' % (gem_spec.homepage)
        self.license = self.get_licenses(getattr(gem_spec, 'licenses', False))
        self.groups = "()"
        self.depends = self.get_deps(gem_spec.dependencies)
        self.makedepends = "('ruby')"
        self.optdepends = "()"
        self.provides = "()"
        self.conflicts = "()"
        self.replaces = "()"
        self.backup = "()"
        self.options = "()"
        self.install = ""
        self.source = '("http://gems.rubyforge.org/gems/%s-${pkgver}.gem")' %\
                (gem_spec.name)
        self.noextract = '("%s-${pkgver}.gem")' % (gem_spec.name)
        self.md5sums = "()" # makepkg already generates md5sums.
        self.build = """
  cd "${srcdir}"
  local _gemdir="$(ruby -rubygems -e'puts Gem.default_dir')"
  gem install --ignore-dependencies -i "$pkgdir$_gemdir" %s-$pkgver.gem \\
    -n \"$pkgdir/usr/bin\"
""" % (gem_spec.name)

    def get_maintainer(self, makepkg_conf):
        default = 'Your Name <YourEmail "AT" example "DOT" com>'
        try:
            for line in open(makepkg_conf):
                if line.startswith('PACKAGER='):
                    return line.strip('PACKAGER=\n ')[1:-1]
            return default
        except IOError:
            return default

    def get_licenses(self, licenses):
        if not licenses or len(licenses) == 0:
            util.warn("License not found! Figure it out and add it.")
            return "()"
        else:
            return "(%s)" % " ".join('%r' % license for license in licenses)

    def get_summary(self, summary):
        if len(summary) > 80:
            util.warn("Summary too long, cut it back to 80 characters.")
        return "\"" + summary + "\""

# TODO Should look into how to format "version must be greater than x
#      and less than y". For now, assume that we just get a single
#      version range restriction
    def get_version_req(self, dependency):
        retval = ""
        for requirement in dependency.version_requirements.requirements:
            # Requirement could be more than one
            retval += str(requirement[0])
            retval += str(requirement[1].version)

        # FIXME what should I really be doing here? "~>1" means "NOT =1".
        if "~" in retval:
                retval = ""
        if retval == ">=0":
                retval = ""
        return retval

    def get_deps(self, dependencies, prefix="ruby-"):
        if not dependencies or len(dependencies) == 0:
            return "()"

        retval = "('ruby' "
        for dependency in dependencies:
            retval += "'" + prefix + dependency.name
            versionreq = self.get_version_req(dependency)
            if versionreq != "":
                retval += versionreq
            retval += "'"
            if dependencies.index(dependency) != len(dependencies) - 1:
                retval += " "

        retval += ")"
        return retval

    _pkg = ['pkgname', 'pkgver', 'pkgrel', 'pkgdesc', 'arch', 'url', 'license',
            'groups', 'depends', 'makedepends', 'optdepends', 'provides',
            'conflicts', 'replaces', 'backup', 'options', 'install', 'source',
            'noextract', 'md5sums']
    #The *:set* command is mangled to keep vim from being really annoying.
    def __repr__(self):
        return '# Maintainer: %s\n%s\n\npackage() {%s}\n\n# %s:set ts=2 sw=2 \
et:' % (self.maintainer, '\n'.join('%s=%s' % (k, getattr(self, k))\
                                   for k in self._pkg), self.build, 'vim')

    def __str__(self):
        return self.__repr__()
