#include <Python.h>
#include "match.h"
#include "search.h"

static PyMethodDef PkgfileMethods[] = {
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
