/* This program is free software. It comes without any warranty, to
 * the extent permitted by applicable law. You can redistribute it
 * and/or modify it under the terms of the Do What The Fuck You Want
 * To Public License, Version 2, as published by Sam Hocevar. See
 * http://sam.zoy.org/wtfpl/COPYING for more details. */

#include <Python.h>
#include "match.h"
#include "search.h"
#include "listpkg.h"
#include "parse.h"

PyObject *RegexError;

static PyMethodDef PkgfileMethods[] = {
  {"list_packages", (PyCFunction)&list_packages, METH_VARARGS | METH_KEYWORDS, "List the packages of a file list tarball."},
  {"pkg_info", (PyCFunction)&pkg_info, METH_VARARGS, "Return info about a package in a file list tarball."},
  {NULL, NULL, 0, NULL}
};

static struct PyModuleDef PkgfileDef = {
  PyModuleDef_HEAD_INIT,
  "pkgfile",
  NULL,
  -1,
  PkgfileMethods
};

PyMODINIT_FUNC PyInit_pkgfile(void) {
  PyObject *m = PyModule_Create(&PkgfileDef);

  if(m == NULL)
    return NULL;

	RegexError = PyErr_NewException("pkgfile.RegexError", NULL, NULL);
	Py_INCREF(RegexError);
	PyModule_AddObject(m, "RegexError", RegexError);

  search_pyinit(m);
  match_pyinit(m);

  return m;
}
