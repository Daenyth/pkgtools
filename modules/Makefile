CC=gcc
CFLAGS ?= -Wall -O2 -pipe

all: pkgfile.so

pkgfile2.o: pkgfile2.c
	$(CC) -c $(CFLAGS) -I/usr/include/python3.1 -fPIC pkgfile2.c

pkgfile.so: pkgfile2.o
	$(CC) $(LDFLAGS) -shared -fPIC -larchive -lpcre pkgfile2.o -o pkgfile.so

clean:
	rm -f pkgfile.so pkgfile2.o
