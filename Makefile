INSTALL = install
INSTALL_DATA = $(INSTALL) -Dm644
INSTALL_PROGRAM = $(INSTALL) -Dm755
prefix = /usr
exec_prefix = $(prefix)
confdir = /etc
bindir = $(exec_prefix)/bin
libdir = $(prefix)/lib
sharedir = $(prefix)/share/pkgtools
profiledir = $(confdir)/profile.d
mandir = $(prefix)/share/man

.PHONY: all

all: install

install:
	# Common functions needed by all scripts
	$(INSTALL_DATA) other/functions $(DESTDIR)$(sharedir)/functions

	# newpkg
	$(INSTALL_PROGRAM) scripts/newpkg $(DESTDIR)$(bindir)/newpkg
	$(INSTALL_DATA) other/functions.newpkg $(DESTDIR)$(sharedir)/functions.newpkg
	$(INSTALL_DATA) confs/newpkg.conf $(DESTDIR)$(confdir)/pkgtools/newpkg.conf
	$(INSTALL) -d $(DESTDIR)$(sharedir)/newpkg/presets/
	$(INSTALL) -m644 other/newpkg_presets/* $(DESTDIR)$(sharedir)/newpkg/presets/

	# spec2arch
	$(INSTALL_PROGRAM) scripts/spec2arch $(DESTDIR)$(bindir)/spec2arch
	$(INSTALL_DATA) confs/spec2arch.conf $(DESTDIR)$(confdir)/pkgtools/spec2arch.conf
	$(INSTALL_DATA) doc/spec2arch.1 $(DESTDIR)$(mandir)/man1/spec2arch.1
	$(INSTALL_DATA) doc/spec2arch.conf.5 $(DESTDIR)$(mandir)/man5/spec2arch.conf.5

	# pkgconflict
	$(INSTALL_PROGRAM) scripts/pkgconflict.py $(DESTDIR)$(bindir)/pkgconflict

	# whoneeds
	$(INSTALL_PROGRAM) scripts/whoneeds.bash $(DESTDIR)$(bindir)/whoneeds

	# pkgclean
	$(INSTALL_PROGRAM) scripts/pkgclean $(DESTDIR)$(bindir)/pkgclean

	# maintpkg
	$(INSTALL_PROGRAM) scripts/maintpkg $(DESTDIR)$(bindir)/maintpkg

	# pip2arch
	$(INSTALL_PROGRAM) scripts/pip2arch/pip2arch.py $(DESTDIR)$(bindir)/pip2arch

uninstall:
	rm -Rf $(DESTDIR)$(sharedir)
	rm $(DESTDIR)$(bindir)/{newpkg,spec2arch,pkgconflict,whoneeds,pkgclean,pip2arch}
	rm -Rf $(DESTDIR)$(confdir)/pkgtools
	rm $(DESTDIR)$(mandir)/man8/spec2arch.8
	rm $(DESTDIR)$(mandir)/man5/spec2arch.conf.5
