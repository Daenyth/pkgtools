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

PyMODINIT_FUNC initpkgfile(void) {
  PyObject *m;
  m = Py_InitModule("pkgfile", PkgfileMethods);

  if(m == NULL)
    return;

	RegexError = PyErr_NewException("pkgfile.RegexError", NULL, NULL);
	Py_INCREF(RegexError);
	PyModule_AddObject(m, "RegexError", RegexError);

  search_pyinit(m);
  match_pyinit(m);
}
