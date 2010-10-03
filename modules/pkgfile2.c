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
#include <fnmatch.h>
#include <regex.h>
#include <pcre.h>
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

static PyObject *search_file(const char *filename,
                             int (*match_func)(const char *dbfile, void *data),
                             void *data) {
  struct archive *a;
  struct archive_entry *entry;
  struct stat st;
  char pname[ABUFLEN], *fname, *dname;
  char *l = NULL;
  FILE *stream = NULL;
  size_t n = 0;
  int nread;
  PyObject *ret, *dict, *pystr, *files;

  pname[ABUFLEN-1]='\0';
  if(stat(filename, &st)==-1 || !S_ISREG(st.st_mode)) {
    PyErr_Format(PyExc_RuntimeError, "File does not exist: %s\n", filename);
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
    
    stream = open_archive_stream(a);
    if (!stream) {
      PyErr_SetString(PyExc_RuntimeError, "Unable to open archive stream.");
      goto cleanup;
    }

    while((nread = getline(&l, &n, stream)) != -1) {
      /* Note: getline returns -1 on both EOF and error. */
      /* So I'm assuming that nread > 0. */
      if(l[nread - 1] == '\n')
        l[nread - 1] = '\0';	/* Clobber trailing newline. */
      if(strcmp(l, "%FILES%") && match_func(l, data)) {
        pystr = PyString_FromString(l);
        if(pystr == NULL)
          goto cleanup;
        PyList_Append(files, pystr);
        Py_DECREF(pystr);
      }
    }

    if(PyList_Size(files) > 0) {
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

/*
 * Matches the db entry f to the argument m
 * The names must either match completely,
 * or m must match the portion of f after the last /
 */
static int simple_match(const char *f, void *d) {
  char *mb;
  const char *m = (const char*)d;

  if(f==NULL || strlen(f)<=0)
    return 0;
  if((m[0]=='/' && !strcmp(f,m+1)) || !strcmp(f, m))
    return 1;
  mb = rindex(f, '/');
  if(mb != NULL && !strcmp(mb+1,m))
    return 1;
  return 0;
}

static int shell_match(const char *f, void *d) {
  char *mb;
  const char *m = (const char*)d;

  if(f==NULL || strlen(f)<=0)
    return 0;
  mb = rindex(f, '/');
  if(mb != NULL)
    return !fnmatch(m, mb+1, 0);
  return 0;
}

static int regex_match(const char *f, void *d) {
  if(f==NULL || strlen(f)<=0)
    return 0;
  return !regexec((regex_t*)d, f, (size_t)0, NULL, 0);
}

struct my_pcredata {
  pcre *re;
  pcre_extra *re_extra;
};

static int pcre_match(const char *f, void *d) {
  if(f==NULL || strlen(f)<=0)
    return 0;
  return pcre_exec(((struct my_pcredata*)d)->re, ((struct my_pcredata*)d)->re_extra, f, strlen(f), 0, 0, NULL, 0) >= 0;
}

static PyMethodDef PkgfileMethods[] = {
  {NULL, NULL, 0, NULL}
};

typedef enum {
  MATCH_NONE,
  MATCH_SIMPLE,
  MATCH_SHELL,
  MATCH_REGEX,
  MATCH_PCRE
} SearchTypes;

typedef struct {
  PyObject_HEAD
  SearchTypes search_type;
  int (*match_func)(const char *dbfile, void *data);
  void *data;
} Search;

static PyObject *Search_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
  Search *self;

  self = (Search*)type->tp_alloc(type, 0);
  if (self != NULL) {
    self->search_type = MATCH_NONE;
    self->match_func = NULL;
    self->data = NULL;
  }

  return (PyObject *)self;
}

static void Search_reset(Search *self) {
  /* For PCRE only */
  struct my_pcredata *pd;

  switch(self->search_type) {
    case MATCH_SIMPLE:
    case MATCH_SHELL:
      free(self->data);
      break;
    case MATCH_REGEX:
      regfree(self->data);
      free(self->data);
      break;
    case MATCH_PCRE:
      pd = (struct my_pcredata*)self->data;
      pcre_free(pd->re);
      pcre_free(pd->re_extra);
      free(self->data);
      break;
    case MATCH_NONE:
      break;
  }
  self->search_type = MATCH_NONE;
  self->match_func = NULL;
  self->data = NULL;
}

static void Search_dealloc(Search* self) {
  Search_reset(self);
  self->ob_type->tp_free((PyObject*)self);
}

static int Search_init(Search *self, PyObject *args, PyObject *kwds) {
  long t;
  const char *pattern;
  /* For PCRE only */
  struct my_pcredata *pd;
  const char *error;
  int erroffset;

  Search_reset(self);
  if(!PyArg_ParseTuple(args, "ls", &t, &pattern))
    return -1;

  switch(t) {
    case MATCH_SIMPLE:
      if(pattern != NULL && strlen(pattern)>0) {
        self->match_func = &simple_match;
        self->data = (void*)strdup(pattern);
      } else {
        PyErr_SetString(PyExc_RuntimeError, "Empty pattern given.");
        return -1;
      }
      break;
    case MATCH_SHELL:
      if(pattern != NULL && strlen(pattern)>0) {
        self->match_func = &shell_match;
        self->data = (void*)strdup(pattern);
      } else {
        PyErr_SetString(PyExc_RuntimeError, "Empty pattern given.");
        return -1;
      }
      break;
    case MATCH_REGEX:
      self->match_func = &regex_match;
      self->data = malloc(sizeof(regex_t));
      if(self->data == NULL) {
        PyErr_SetString(PyExc_RuntimeError, "Unable to allocate memory.");
        return -1;
      }
      if(regcomp(self->data, pattern, REG_EXTENDED | REG_NOSUB) != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Could not compile regex.");
        free(self->data);
        return -1;
      }
      break;
    case MATCH_PCRE:
      self->match_func = &pcre_match;
      self->data = malloc(sizeof(struct my_pcredata));
      pd = (struct my_pcredata*)self->data;

      pd->re = pcre_compile(pattern, 0, &error, &erroffset, NULL);
      if(pd->re == NULL) {
        PyErr_Format(PyExc_RuntimeError, "Could not compile regex at %d: %s", erroffset, error);
        free(self->data);
        return -1;
      }
      pd->re_extra = pcre_study(pd->re, 0, &error);
      if(error != NULL) {
        PyErr_Format(PyExc_RuntimeError, "Could not study regex: %s", error);
        pcre_free(pd->re);
        free(self->data);
        return -1;
      }
      break;
    default:
      PyErr_SetString(PyExc_RuntimeError, "Invalid matching method given.");
      return -1;
  }
  self->search_type = t;
  return 0;
}

static PyObject *Search_call(Search *self, PyObject *args, PyObject *kw) {
  const char *filename;
  static char *kwlist[] = {"filename", NULL};

  if(!PyArg_ParseTupleAndKeywords(args, kw, "s", kwlist, &filename))
    return NULL;
  if(filename == NULL || strlen(filename)<=0) {
    PyErr_SetString(PyExc_RuntimeError, "Empty files tarball name given.");
    return NULL;
  }
  if(self->search_type == MATCH_NONE || self->match_func == NULL) {
    PyErr_SetString(PyExc_RuntimeError, "Invalid matching function.");
    return NULL;
  }
  return search_file(filename, self->match_func, self->data);
}

static PyTypeObject SearchType = {
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

PyMODINIT_FUNC initpkgfile(void) {
  PyObject *m, *to;
  m = Py_InitModule("pkgfile", PkgfileMethods);

  if(m == NULL)
    return;

  if (PyType_Ready(&SearchType) < 0)
    return;
  to = (PyObject*)&SearchType;
  Py_INCREF(to);
  PyModule_AddObject(m, "Search", (PyObject*)&SearchType);
  PyModule_AddIntConstant(m, "MATCH_SIMPLE", MATCH_SIMPLE);
  PyModule_AddIntConstant(m, "MATCH_SHELL", MATCH_SHELL);
  PyModule_AddIntConstant(m, "MATCH_REGEX", MATCH_REGEX);
  PyModule_AddIntConstant(m, "MATCH_PCRE", MATCH_PCRE);
}
