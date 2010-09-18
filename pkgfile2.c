#include <Python.h>
#define _GNU_SOURCE 1
#include <archive.h>
#include <archive_entry.h>
#include <stdio.h>
#include <stdlib.h>
#include <libgen.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#define ABUFLEN 1024

static cookie_io_functions_t archive_stream_funcs = {
.read = archive_read_data,
.write = NULL,
.seek = NULL,
.close = NULL
};

static FILE *open_archive_stream(struct archive *archive) {
  return fopencookie(archive, "r", archive_stream_funcs);
}

/*
 * Matches the db entry f to the argument m
 * The names must either match completely,
 * or m must match the portion of f after the last /
 */
static int simple_match(const char *f, const char *m) {
  char *mb;

  if(f==NULL || strlen(f)<0 || m==NULL || strlen(m)<0)
    return 0;
  if((m[0]=='/' && !strcmp(f,m+1)) || !strcmp(f, m))
    return 1;
  mb = rindex(f, '/');
  if(mb != NULL && !strcmp(mb+1,m))
    return 1;
  return 0;
}

static PyObject *search_file(PyObject *self, PyObject *args, int (*match_func)(const char *dbfile, const char *pattern)) {
  const char *filename, *pattern;
  struct archive *a;
  struct archive_entry *entry;
  struct stat st;
  char pname[ABUFLEN], *fname, *dname;
  char *l = NULL;
  FILE *stream = NULL;
  size_t n = 0;
  int nread;
  PyObject *ret, *dict, *pystr;

  pname[ABUFLEN-1]='\0';
  PyArg_ParseTuple(args, "ss", &filename, &pattern);

  if(stat(filename, &st)==-1 || !S_ISREG(st.st_mode)) {
    PyErr_Format(PyExc_RuntimeError, "File does not exist: %s\n", filename);
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
  l = NULL;
  while (archive_read_next_header(a, &entry) == ARCHIVE_OK) {
    if(!S_ISREG(archive_entry_filetype(entry))) {
      archive_read_data_skip(a);
      continue;
    }
    strncpy(pname, archive_entry_pathname(entry), ABUFLEN-1);
    fname = basename(pname);
    dname = dirname(pname);
    if(strcmp(fname, "files")) {
      archive_read_data_skip(a);
      continue;
    }
    
    stream = open_archive_stream(a);
    if (!stream) {
      PyErr_SetString(PyExc_RuntimeError, "Unable to open archive stream.");
      Py_DECREF(ret);
      archive_read_finish(a);
      return NULL;
    }

    while((nread = getline(&l, &n, stream)) != -1) {
      /* Note: getline returns -1 on both EOF and error. */
      /* So I'm assuming that nread > 0. */
      if(l[nread - 1] == '\n')
        l[nread - 1] = '\0';	/* Clobber trailing newline. */
      if(strcmp(l, "%FILES%") && match_func(l, pattern)) {
        dict = PyDict_New();

        pystr = PyString_FromString(dname);
        PyDict_SetItemString(dict, "package", pystr);
        Py_DECREF(pystr);
        pystr = PyString_FromString(l);
        PyDict_SetItemString(dict, "file", pystr);
        Py_DECREF(pystr);

        PyList_Append(ret, dict);
        Py_DECREF(dict);
      }
    }
    fclose(stream);
  }

  if(l)
    free(l);

  archive_read_finish(a);
  return ret;
}

static PyObject *search(PyObject *self, PyObject *args) {
  return search_file(self, args, &simple_match);
}

static PyObject *search_regex(PyObject *self, PyObject *args) {
  /*return search_file(self, args, &regex_match);*/
  PyErr_SetString(PyExc_NotImplementedError, "Regex searching is not implemented yet.");
  return NULL;
}

static PyMethodDef PkgfileMethods[] = {
  { "search", (PyCFunction)&search, METH_VARARGS, "foo" },
  { "search_regex", (PyCFunction)&search_regex, METH_VARARGS, "foo" },
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC
initpkgfile(void)
{
  (void) Py_InitModule("pkgfile", PkgfileMethods);
}
