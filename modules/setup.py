#!/usr/bin/python
from distutils.core import setup, Extension

setup(name='pkgfile',
      version='0.1',
      ext_modules=[Extension('pkgfile', ['pkgfile2.c'],
          libraries=['archive', 'pcre'])],
      )
