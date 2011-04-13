#include <Python.h>
#include <archive.h>
#include <archive_entry.h>
#include <libgen.h>
#include "listpkg.h"
#include "util.h"
#define ABUFLEN 1024

PyObject *list_packages(PyObject *self, PyObject *args, PyObject *kw) {
  const char *filename;
  static char *kwlist[] = {"filename", NULL};
  struct archive *a;
  struct archive_entry *entry;
  struct stat st;
  char pname[ABUFLEN], *fname, *dname, *pkgname, *pkgver;
  PyObject *ret, *dict, *pystr;

  if(!PyArg_ParseTupleAndKeywords(args, kw, "s", kwlist, &filename))
    return NULL;
  if(filename == NULL || strlen(filename)<=0) {
    PyErr_SetString(PyExc_ValueError, "Empty files tarball name given.");
    return NULL;
  }

  pname[ABUFLEN-1]='\0';
  if(stat(filename, &st)==-1 || !S_ISREG(st.st_mode)) {
    PyErr_Format(PyExc_IOError, "File does not exist: %s\n", filename);
    return NULL;
  }
  ret = PyList_New(0);
  if(ret == NULL) {
    return NULL;
  }
  a = archive_read_new();
  archive_read_support_compression_all(a);
  archive_read_support_format_all(a);
  archive_read_open_filename(a, filename, 10240);
  while (archive_read_next_header(a, &entry) == ARCHIVE_OK) {
    if(!S_ISREG(archive_entry_filetype(entry))) {
      archive_read_data_skip(a);
      continue;
    }
    strncpy(pname, archive_entry_pathname(entry), ABUFLEN-1);
    fname = basename(pname);
    dname = dirname(pname);
    if(strcmp(fname, "files") == 0) {
      if (splitname(dname, &pkgname, &pkgver) == -1) {
        archive_read_data_skip(a);
        continue;
      }
      dict = PyDict_New();
      if(dict == NULL) {
        goto cleanup_nodict;
      }
      pystr = PyUnicode_FromString(pkgname);
      free(pkgname);
      if(pystr == NULL) {
        free(pkgver);
        goto cleanup;
      }
      PyDict_SetItemString(dict, "name", pystr);
      Py_DECREF(pystr);
      pystr = PyUnicode_FromString(pkgver);
      free(pkgver);
      if(pystr == NULL)
        goto cleanup;
      PyDict_SetItemString(dict, "version", pystr);
      Py_DECREF(pystr);

      PyList_Append(ret, dict);
      Py_DECREF(dict);
    }
    archive_read_data_skip(a);
  }
  archive_read_finish(a);
  return ret;

cleanup:
  Py_DECREF(dict);
cleanup_nodict:
  archive_read_finish(a);
  Py_DECREF(ret);
  return NULL;
}
