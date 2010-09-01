INSTALL = install
INSTALL_DATA = $(INSTALL) -Dm644
INSTALL_PROGRAM = $(INSTALL) -Dm755
INSTALL_CRON = $(INSTALL) -Dm744

prefix = /usr
exec_prefix = $(prefix)
confdir = /etc
bindir = $(exec_prefix)/bin
libdir = $(prefix)/lib
sharedir = $(prefix)/share/pkgtools
cachedir = /var/cache/pkgtools/lists
profiledir = $(confdir)/profile.d
crondir = $(confdir)/cron.daily
mandir = $(prefix)/share/man

.PHONY: install uninstall


install:
	# Common functions needed by all scripts
	$(INSTALL_DATA) other/functions $(DESTDIR)$(sharedir)/functions

	# newpkg
	$(INSTALL_PROGRAM) scripts/newpkg $(DESTDIR)$(bindir)/newpkg
	$(INSTALL_DATA) other/functions.newpkg $(DESTDIR)$(sharedir)/functions.newpkg
	$(INSTALL_DATA) confs/newpkg.conf $(DESTDIR)$(confdir)/pkgtools/newpkg.conf
	$(INSTALL) -d $(DESTDIR)$(sharedir)/newpkg/presets/
	$(INSTALL) -m644 other/newpkg_presets/* $(DESTDIR)$(sharedir)/newpkg/presets/

	# pkgfile
	$(INSTALL) -d $(DESTDIR)$(cachedir)
	$(INSTALL_PROGRAM) scripts/pkgfile.py $(DESTDIR)$(bindir)/pkgfile
	$(INSTALL_PROGRAM) scripts/alpm2sqlite.py $(DESTDIR)$(libdir)/python2.6/site-packages/alpm2sqlite.py
	$(INSTALL_DATA) confs/pkgfile.conf $(DESTDIR)$(confdir)/pkgtools/pkgfile.conf
	$(INSTALL_CRON) other/pkgfile.cron $(DESTDIR)$(crondir)/pkgfile
	# Loads shell hooks
	$(INSTALL_PROGRAM) other/pkgfile-hook.sh $(DESTDIR)$(profiledir)/pkgfile-hook.sh
	$(INSTALL_DATA) other/pkgfile-hook.zsh $(DESTDIR)$(sharedir)/pkgfile-hook.zsh
	$(INSTALL_DATA) other/pkgfile-hook.bash $(DESTDIR)$(sharedir)/pkgfile-hook.bash

	# spec2arch
	$(INSTALL_PROGRAM) scripts/spec2arch $(DESTDIR)$(bindir)/spec2arch
	$(INSTALL_DATA) confs/spec2arch.conf $(DESTDIR)$(confdir)/pkgtools/spec2arch.conf
	$(INSTALL_DATA) doc/spec2arch.8 $(DESTDIR)$(mandir)/man8/spec2arch.8
	$(INSTALL_DATA) doc/spec2arch.conf.5 $(DESTDIR)$(mandir)/man5/spec2arch.conf.5

	# pkgconflict
	$(INSTALL_PROGRAM) scripts/pkgconflict.py $(DESTDIR)$(bindir)/pkgconflict

	# whoneeds
	$(INSTALL_PROGRAM) scripts/whoneeds.bash $(DESTDIR)$(bindir)/whoneeds

	# pkgclean
	$(INSTALL_PROGRAM) scripts/pkgclean $(DESTDIR)$(bindir)/pkgclean

	# maintpkg
	$(INSTALL_PROGRAM) scripts/maintpkg $(DESTDIR)$(bindir)/maintpkg

uninstall:
	rm -Rf $(DESTDIR)$(sharedir)
	rm $(DESTDIR)$(bindir)/{newpkg,pkgfile,spec2arch,pkgconflict,whoneeds,pkgclean}
	rm $(DESTDIR)$(crondir)/pkgfile
	rm $(DESTDIR)$(profiledir)/pkgfile-hook.*
	rm -Rf $(DESTDIR)$(confdir)/pkgtools
	rm $(DESTDIR)$(mandir)/man8/spec2arch.8
	rm $(DESTDIR)$(mandir)/man5/spec2arch.conf.5
