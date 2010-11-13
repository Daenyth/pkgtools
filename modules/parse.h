#ifndef PARSE_H
#define PARSE_H

#include <stdio.h>
#include <Python.h>

int parse_depends(FILE *stream, PyObject **ppkg);
int parse_desc(FILE *stream, PyObject **ppkg);
PyObject *pkg_info(PyObject *self, PyObject *args);
#endif /* PARSE_H */
