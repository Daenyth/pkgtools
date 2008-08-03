# Contributor: Daenyth <Daenyth+Arch AT gmail DOT com>
pkgname=pkgtools
pkgver=8
pkgrel=1
pkgdesc="A collection of scripts for Arch Linux packages"
arch=(any)
url="http://bbs.archlinux.org/viewtopic.php?pid=384196"
license=('GPL')
source=(newpkg pkgfile aurball
        'functions'
        newpkg.conf pkgfile.conf
        pkgfile-hook pkgfile.cron)
backup=('etc/pkgtools/newpkg.conf' 'etc/pkgtools/pkgfile.conf')
replaces=(newpkg)
conflicts=(newpkg)
provides=(newpkg)
install="$pkgname.install"
optdepends=('zsh: For command not found hook'
            'cron: For pkgfile --update entry')


build() {
  # Common fucntions needed by all scripts
  install -Dm644 "${srcdir}/functions" "${pkgdir}/usr/share/pkgtools/functions"

  # newpkg
  install -Dm755 "${srcdir}/newpkg" "${pkgdir}/usr/bin/newpkg"
  install -Dm644 "${srcdir}/newpkg.conf" "${pkgdir}/etc/pkgtools/newpkg.conf"

  # pkgfile
  install -Dm755 "${srcdir}/pkgfile" "${pkgdir}/usr/bin/pkgfile"
  install -Dm644 "${srcdir}/pkgfile.conf" "${pkgdir}/etc/pkgtools/pkgfile.conf"
  install -d "$pkgdir/usr/share/pkgtools/lists/"
  install -Dm644 "${srcdir}/pkgfile-hook" "${pkgdir}/usr/share/pkgtools/pkgfile-hook"
  install -Dm744 "${srcdir}/pkgfile.cron" "${pkgdir}/etc/cron.daily/pkgfile"

  # aurball
  install -Dm755 "${srcdir}/aurball" "${pkgdir}/usr/bin/aurball"
}

# vim:set ts=2 sw=2 et:
md5sums=('bbb512c746b07a99df61b05eb57bfc7d'
         '5eaa612048524aab938f87702382c63e'
         'dad5dcdb4cd1a53c2b2a1186b06b6fc3'
         '3788d4d6900bfaad04e97b47d0ac1b70'
         'e711a94744171b66ca41c8ad157fb4bd'
         '79e306084c11059d6b15bccc44557af8'
         '1d7fdb5a445fd9e9b1816872909c17a7'
         '3456bbd52daac40e771e7ab619e9378b')
