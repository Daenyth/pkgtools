all : 
	echo "Ready. Now run 'sudo make install'"

newpkg_install : newpkg newpkg.conf
	install -Dm755 newpkg           /usr/bin/newpkg
	install -Dm644 newpkg.conf      /etc/pkgtools/newpkg.conf
