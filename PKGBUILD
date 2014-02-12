# Maintainer: Daenyth <Daenyth+Arch AT gmail DOT com>
# Contributor: Daenyth <Daenyth+Arch AT gmail DOT com>
pkgname=pkgtools
pkgver=24
pkgrel=1
pkgdesc="A collection of scripts for Arch Linux packages"
arch=('any')
url="https://bbs.archlinux.org/viewtopic.php?pid=384196"
license=('GPL')
depends=('bash>=4' 'pcre' 'libarchive' 'python' 'namcap')
optdepends=('abs: Provides PKGBUILD prototypes for newpkg')
provides=('newpkg' 'pkgfile')
backup=('etc/pkgtools/newpkg.conf' 'etc/pkgtools/pkgfile.conf' 'etc/pkgtools/spec2arch.conf')
install=pkgtools.install
source=("${pkgname}-v${pkgver}.tar.gz::https://github.com/Daenyth/pkgtools/tarball/v$pkgver")
md5sums=('f139c3940e1038cac4e29e985089e8a8')

package() {
	cd "Daenyth-$pkgname"-*

	make DESTDIR="$pkgdir" install
}
