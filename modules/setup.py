#!/usr/bin/python3
from distutils.core import setup, Extension

setup(name='pkgfile',
      version='0.1',
      ext_modules=[Extension('pkgfile',
          ['pkgfile2.c', 'match.c', 'search.c', 'listpkg.c', 'util.c', 'parse.c'],
          libraries=['archive', 'pcre'],
          extra_compile_args=['-Wall'])],
      )
