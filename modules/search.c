#include <Python.h>
#define _GNU_SOURCE 1
#include <archive.h>
#include <archive_entry.h>
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <libgen.h>
#include "search.h"
#include "match.h"
#define ABUFLEN 1024

static cookie_io_functions_t archive_stream_funcs = {
.read = (cookie_read_function_t*)archive_read_data,
.write = NULL,
.seek = NULL,
.close = NULL
};

static FILE *open_archive_stream(struct archive *archive) {
  return fopencookie(archive, "r", archive_stream_funcs);
}

typedef enum {
  SEARCH_NONE,
  SEARCH_PATH,
  SEARCH_FILENAME,
  SEARCH_PACKAGE
} SearchType;

static PyObject *search_file(const char *filename,
                             MatchFunc match_func,
                             SearchType search_type,
                             void *data) {
  struct archive *a;
  struct archive_entry *entry;
  struct stat st;
  char pname[ABUFLEN], *fname, *dname;
  char *l = NULL, *m, *p;
  FILE *stream = NULL;
  size_t n = 0;
  int nread;
  PyObject *ret, *dict, *pystr, *files;

  pname[ABUFLEN-1]='\0';
  if(stat(filename, &st)==-1 || !S_ISREG(st.st_mode)) {
    PyErr_Format(PyExc_IOError, "File does not exist: %s\n", filename);
    return NULL;
  }
  ret = PyList_New(0);
  if(ret == NULL) {
    return NULL;
  }

  files = PyList_New(0);
  if(files == NULL) {
    Py_DECREF(ret);
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
    if(search_type == SEARCH_PACKAGE) {
      m = strdup(dname);
      p = m + strlen(m);
      for(--p; *p && *p != '-'; --p);
      for(--p; *m && *p != '-'; --p);
      if(p<=m || *p != '-' || (*p = '\0', !match_func(m, data))) {
        free(m);
        archive_read_data_skip(a);
        continue;
      }
      free(m);
    }
    
    stream = open_archive_stream(a);
    if (!stream) {
      PyErr_SetString(PyExc_RuntimeError, "Unable to open archive stream.");
      goto cleanup;
    }

    while((nread = getline(&l, &n, stream)) != -1) {
      /* Note: getline returns -1 on both EOF and error. */
      /* So I'm assuming that nread > 0. */
      if(l[nread - 1] == '\n')
        l[nread - 1] = '\0';  /* Clobber trailing newline. */
      if(strcmp(l, "%FILES%") == 0)
        continue;
      if(search_type == SEARCH_FILENAME) {
        m = rindex(l, '/');
        if(m == NULL || strlen(m) == 0 || strlen(++m) == 0)
          continue;
      } else {
        m = l;
      }
      if(search_type == SEARCH_PACKAGE || match_func(m, data)) {
        pystr = PyString_FromString(l);
        if(pystr == NULL)
          goto cleanup;
        PyList_Append(files, pystr);
        Py_DECREF(pystr);
      }
    }

    if(search_type == SEARCH_PACKAGE || PyList_Size(files) > 0) {
      pystr = PyString_FromString(dname);
      if(pystr == NULL)
        goto cleanup;
      dict = PyDict_New();
      if(dict == NULL) {
        Py_DECREF(pystr);
        goto cleanup;
      }
      PyDict_SetItemString(dict, "package", pystr);
      Py_DECREF(pystr);
      PyDict_SetItemString(dict, "files", files);
      Py_DECREF(files);

      PyList_Append(ret, dict);
      Py_DECREF(dict);

      files = PyList_New(0);
      if(files == NULL)
        goto cleanup_nofiles;
    }
    fclose(stream);
  }

  Py_DECREF(files);
  if(l)
    free(l);

  archive_read_finish(a);
  return ret;

cleanup:
  Py_DECREF(files);
cleanup_nofiles:
  if(l)
    free(l);
  archive_read_finish(a);
  Py_DECREF(ret);
  return NULL;
}

typedef struct {
  PyObject_HEAD
  MatchType match_type;
  MatchFunc match_func;
  SearchType search_type;
  void *data;
} Search;

static PyObject *Search_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  Search *self;

  self = (Search*)type->tp_alloc(type, 0);
  if (self != NULL) {
    self->match_type = MATCH_NONE;
    self->match_func = NULL;
    self->search_type = SEARCH_NONE;
    self->data = NULL;
  }

  return (PyObject *)self;
}

static void Search_dealloc(Search* self) {
  match_reset(&(self->match_type), &(self->match_func), &(self->data));
  self->ob_type->tp_free((PyObject*)self);
}

static int Search_init(Search *self, PyObject *args, PyObject *kw) {
  long mt, st;
  const char *pattern;
  static char *kwlist[] = {"matchtype", "searchtype", "pattern", NULL};

  match_reset(&(self->match_type), &(self->match_func), &(self->data));
  self->search_type = SEARCH_NONE;
  if(!PyArg_ParseTupleAndKeywords(args, kw, "lls", kwlist, &mt, &st, &pattern))
    return -1;
  switch(st) {
    case SEARCH_PATH:
    case SEARCH_PACKAGE:
    case SEARCH_FILENAME:
      break;
    default:
      PyErr_SetString(PyExc_ValueError, "Invalid search type given.");
      return -1;
  }
  self->search_type = st;
  return match_init(mt, pattern, &(self->match_type), &(self->match_func), &(self->data));
}

static PyObject *Search_call(Search *self, PyObject *args, PyObject *kw) {
  const char *filename;
  static char *kwlist[] = {"filename", NULL};

  if(!PyArg_ParseTupleAndKeywords(args, kw, "s", kwlist, &filename))
    return NULL;
  if(filename == NULL || strlen(filename)<=0) {
    PyErr_SetString(PyExc_ValueError, "Empty files tarball name given.");
    return NULL;
  }
  if(self->match_type == MATCH_NONE || self->match_func == NULL || self->search_type == SEARCH_NONE) {
    PyErr_SetString(PyExc_RuntimeError, "Invalid matching function or search type.");
    return NULL;
  }
  return search_file(filename, self->match_func, self->search_type, self->data);
}

static PyTypeObject SearchPyType = {
  PyObject_HEAD_INIT(NULL)
  0,                          /*ob_size*/
  "pkgfile.Search",           /*tp_name*/
  sizeof(Search),             /*tp_basicsize*/
  0,                          /*tp_itemsize*/
  (destructor)Search_dealloc, /*tp_dealloc*/
  0,                          /*tp_print*/
  0,                          /*tp_getattr*/
  0,                          /*tp_setattr*/
  0,                          /*tp_compare*/
  0,                          /*tp_repr*/
  0,                          /*tp_as_number*/
  0,                          /*tp_as_sequence*/
  0,                          /*tp_as_mapping*/
  0,                          /*tp_hash */
  (ternaryfunc)Search_call,   /*tp_call*/
  0,                          /*tp_str*/
  0,                          /*tp_getattro*/
  0,                          /*tp_setattro*/
  0,                          /*tp_as_buffer*/
  Py_TPFLAGS_DEFAULT,         /*tp_flags*/
  "Search object",            /* tp_doc */
  0,                          /* tp_traverse */
  0,                          /* tp_clear */
  0,                          /* tp_richcompare */
  0,                          /* tp_weaklistoffset */
  0,                          /* tp_iter */
  0,                          /* tp_iternext */
  0,                          /* tp_methods */
  0,                          /* tp_members */
  0,                          /* tp_getset */
  0,                          /* tp_base */
  0,                          /* tp_dict */
  0,                          /* tp_descr_get */
  0,                          /* tp_descr_set */
  0,                          /* tp_dictoffset */
  (initproc)Search_init,      /* tp_init */
  0,                          /* tp_alloc */
  Search_new,                 /* tp_new */
};

void search_pyinit(PyObject *m) {
  PyObject *to;

  if (PyType_Ready(&SearchPyType) < 0)
    return;
  to = (PyObject*)&SearchPyType;
  Py_INCREF(to);
  PyModule_AddObject(m, "Search", (PyObject*)&SearchPyType);
  PyModule_AddIntConstant(m, "SEARCH_PATH", SEARCH_PATH);
  PyModule_AddIntConstant(m, "SEARCH_FILENAME", SEARCH_FILENAME);
  PyModule_AddIntConstant(m, "SEARCH_PACKAGE", SEARCH_PACKAGE);
}
