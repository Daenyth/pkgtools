# Maintainer: Daenyth <Daenyth+Arch AT gmail DOT com>
# Contributor: Daenyth <Daenyth+Arch AT gmail DOT com>
pkgname=pkgtools
pkgver=23
pkgrel=1
pkgdesc="A collection of scripts for Arch Linux packages"
arch=('any')
url="https://bbs.archlinux.org/viewtopic.php?pid=384196"
license=('GPL')
depends=('bash>=4' 'pcre' 'libarchive' 'python')
optdepends=('abs: Provides proto packaging files for newpkg')
provides=('newpkg' 'pkgfile')
backup=('etc/pkgtools/newpkg.conf' 'etc/pkgtools/pkgfile.conf' 'etc/pkgtools/spec2arch.conf')
install=pkgtools.install
source=("v$pkgver::https://github.com/Daenyth/pkgtools/tarball/v$pkgver")
md5sums=('5361111e31741f8d7ff8ca45c7996b6b')

package() {
	cd "Daenyth-$pkgname"-*

	make DESTDIR="$pkgdir" install
}
