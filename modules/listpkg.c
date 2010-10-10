#include <Python.h>
#include <archive.h>
#include <archive_entry.h>
#include <libgen.h>
#include "listpkg.h"
#define ABUFLEN 1024

PyObject *list_packages(PyObject *self, PyObject *args, PyObject *kw) {
  const char *filename;
  static char *kwlist[] = {"filename", NULL};
  struct archive *a;
  struct archive_entry *entry;
  struct stat st;
  char pname[ABUFLEN], *fname, *dname;
  PyObject *ret, *pystr;

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
      pystr = PyString_FromString(dname);
      if(pystr == NULL)
        goto cleanup;
      PyList_Append(ret, pystr);
      Py_DECREF(pystr);
    }
    archive_read_data_skip(a);
  }
  archive_read_finish(a);
  return ret;

cleanup:
  archive_read_finish(a);
  Py_DECREF(ret);
  return NULL;
}
