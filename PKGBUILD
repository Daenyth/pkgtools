# Contributor: Daenyth <Daenyth+Arch AT gmail DOT com>
pkgname=pkgtools
pkgver=5
pkgrel=1
pkgdesc="A collection of scripts for archlinux packages"
arch=(any)
url="http://bbs.archlinux.org/viewtopic.php?pid=384196#p384196"
license=('GPL')
source=(newpkg pkgfile
        newpkg.conf pkgfile.conf
        pkgfile-hook pkgfile.cron)
backup=('etc/pkgtools/newpkg.conf' 'etc/pkgtools/pkgfile.conf')
replaces=(newpkg)
conflicts=(newpkg)
provides=(newpkg)
install="{$pkgname.install}"
optdepends=('zsh: For command not found hook'
            'cron: For pkgfile --update entry')

build() {
  install -d "$pkgdir/usr/share/pkgtools/lists/"
  install -Dm755 "${srcdir}/newpkg" "${pkgdir}/usr/bin/newpkg"
  install -Dm755 "${srcdir}/pkgfile" "${pkgdir}/usr/bin/pkgfile"

  install -Dm644 "${srcdir}/newpkg.conf" "${pkgdir}/etc/pkgtools/newpkg.conf"
  install -Dm644 "${srcdir}/pkgfile.conf" "${pkgdir}/etc/pkgtools/pkgfile.conf"

  install -Dm644 "${srcdir}/pkgfile-hook" "${pkgdir}/usr/share/pkgtools/pkgfile-hook"
  install -Dm744 "${srcdir}/pkgfile.cron" "${pkgdir}/etc/cron.daily/pkgfile"
}

# vim:set ts=2 sw=2 et:
