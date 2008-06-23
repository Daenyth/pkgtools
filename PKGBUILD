# Contributor: Daenyth <Daenyth+Arch AT gmail DOT com>
pkgname=pkgtools
pkgver=5
pkgrel=1
pkgdesc="A collection of scripts for archlinux packages"
arch=(any)
url="http://bbs.archlinux.org/viewtopic.php?pid=384196#p384196"
license=('GPL')
source=(newpkg pkgfile
        newpkg.conf
        pkgfile-hook)
backup=('etc/pkgtools/newpkg.conf')
replaces=(newpkg)
conflicts=(newpkg)
provides=(newpkg)
install="{$pkgname.install}"
optdepends=('zsh: For command not found hook')

build() {
  install -d "$pkgdir/usr/share/pkgtools/lists/"
  install -Dm755 "${srcdir}/newpkg" "${pkgdir}/usr/bin/newpkg"
  install -Dm755 "${srcdir}/pkgfile" "${pkgdir}/usr/bin/pkgfile"

  install -Dm644 "${srcdir}/newpkg.conf" "${pkgdir}/etc/pkgtools/newpkg.conf"
}

# vim:set ts=2 sw=2 et:
