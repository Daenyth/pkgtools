#include <Python.h>
#include "match.h"
#include "search.h"
#include "listpkg.h"

static PyMethodDef PkgfileMethods[] = {
  {"list_packages", (PyCFunction)&list_packages, METH_VARARGS | METH_KEYWORDS, "List the packages of a file list tarball."},
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initpkgfile(void) {
  PyObject *m;
  m = Py_InitModule("pkgfile", PkgfileMethods);

  if(m == NULL)
    return;

  search_pyinit(m);
  match_pyinit(m);
}
