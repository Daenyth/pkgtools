# Contributor: Daenyth <Daenyth+Arch AT gmail DOT com>
pkgname=pkgtools
pkgver=4
pkgrel=1
pkgdesc="A collection of scripts for archlinux packages"
arch=(any)
url="http://bbs.archlinux.org/viewtopic.php?pid=384196#p384196"
license=('GPL')
source=(newpkg pkgfile zsh_command_not_found)
md5sums=('8e9e3f0df80a3a4286baf8e88080bd46' 'eb09cc47539c7d34c8f44145ce903424'\
         '1d66952f54f6e21a0149c70f3b546415')
replaces=(newpkg)
conflicts=(newpkg)
provides=(newpkg)

build() {
  install -d "$pkgdir/usr/share/pkgtools/lists/"
  install -Dm755 "${srcdir}/newpkg" "${pkgdir}/usr/bin/newpkg"
  install -Dm755 "${srcdir}/pkgfile" "${pkgdir}/usr/bin/pkgfile"
}

# vim:set ts=2 sw=2 et:
