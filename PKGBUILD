# Maintainer: Daenyth <Daenyth+Arch AT gmail DOT com>
# Contributor: Daenyth <Daenyth+Arch AT gmail DOT com>
pkgname=pkgtools
pkgver=25
pkgrel=1
pkgdesc="A collection of scripts for Arch Linux packages"
arch=('any')
url="https://bbs.archlinux.org/viewtopic.php?pid=384196"
license=('GPL')
depends=('bash>=4' 'pcre' 'libarchive' 'python' 'namcap' 'pkgfile')
optdepends=('abs: Provides PKGBUILD prototypes for newpkg')
provides=('newpkg')
backup=('etc/pkgtools/newpkg.conf' 'etc/pkgtools/pkgfile.conf' 'etc/pkgtools/spec2arch.conf')
install=pkgtools.install
source=("${pkgname}-v${pkgver}.tar.gz::https://github.com/Daenyth/pkgtools/tarball/v$pkgver")
md5sums=('9e9d7aad5ba8ecee1b798c3ed4e0a0a7')

package() {
	cd "Daenyth-$pkgname"-*

	make DESTDIR="$pkgdir" install
}
