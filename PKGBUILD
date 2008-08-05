# Contributor: Daenyth <Daenyth+Arch AT gmail DOT com>
pkgname=pkgtools
pkgver=9
pkgrel=1
pkgdesc="A collection of scripts for Arch Linux packages"
arch=(any)
url="http://bbs.archlinux.org/viewtopic.php?pid=384196"
license=('GPL')
source=(newpkg pkgfile aurball spec2arch
        functions
        newpkg.conf pkgfile.conf spec2arch.conf
        spec2arch.8 spec2arch.conf.5
        pkgfile-hook pkgfile.cron)
backup=('etc/pkgtools/newpkg.conf' 'etc/pkgtools/pkgfile.conf' 'etc/pkgtools/spec2arch.conf')
replaces=(newpkg)
conflicts=(newpkg)
provides=(newpkg)
install="$pkgname.install"
optdepends=('zsh: For command not found hook'
            'cron: For pkgfile --update entry')


build() {
  # Common fucntions needed by all scripts
  install -Dm644 "${srcdir}/functions"        "${pkgdir}/usr/share/pkgtools/functions"

  # newpkg
  install -Dm755 "${srcdir}/newpkg"           "${pkgdir}/usr/bin/newpkg"
  install -Dm644 "${srcdir}/newpkg.conf"      "${pkgdir}/etc/pkgtools/newpkg.conf"

  # pkgfile
  install -d "$pkgdir/usr/share/pkgtools/lists/"
  install -Dm755 "${srcdir}/pkgfile"          "${pkgdir}/usr/bin/pkgfile"
  install -Dm644 "${srcdir}/pkgfile.conf"     "${pkgdir}/etc/pkgtools/pkgfile.conf"
  install -Dm644 "${srcdir}/pkgfile-hook"     "${pkgdir}/usr/share/pkgtools/pkgfile-hook"
  install -Dm744 "${srcdir}/pkgfile.cron"     "${pkgdir}/etc/cron.daily/pkgfile"

  # aurball
  install -Dm755 "${srcdir}/aurball"          "${pkgdir}/usr/bin/aurball"

  # spec2arch
  install -Dm755 "${srcdir}/spec2arch"        "${pkgdir}/usr/bin/spec2arch"
  install -Dm644 "${srcdir}/spec2arch.conf"   "${pkgdir}/etc/pkgtools/spec2arch.conf"
  install -Dm644 "${srcdir}/spec2arch.8"      "${pkgdir}/usr/share/man/man8/spec2arch.8"
  install -Dm644 "${srcdir}/spec2arch.conf.5" "${pkgdir}/usr/share/man/man8/spec2arch.conf.5"
}

# vim:set ts=2 sw=2 et:
md5sums=('ff115b184d090deae11afc67f56094eb'
         '8eb98a93c4f53dd06062efbe0a6e4fc6'
         'adc46727c22d790454b2137a8f3d2c88'
         '886655bf39624428fa7c7127d55f9839'
         '3788d4d6900bfaad04e97b47d0ac1b70'
         'e711a94744171b66ca41c8ad157fb4bd'
         '79e306084c11059d6b15bccc44557af8'
         '1e3b1c6efcca3d7ae64a85d12d769ffa'
         'b60b17497f9679ff05f19c6674f543e9'
         '0ec3dbb726830035d067c91e625dd5ed'
         '1d7fdb5a445fd9e9b1816872909c17a7'
         '3456bbd52daac40e771e7ab619e9378b')
