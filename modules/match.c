#include <Python.h>
#include <fnmatch.h>
#include <regex.h>
#include <pcre.h>
#include <string.h>
#include "match.h"

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

void match_reset(MatchType* match_type, MatchFunc* match_func, void **data) {
  /* For PCRE only */
  struct my_pcredata *pd;

  switch(*match_type) {
    case MATCH_SIMPLE:
    case MATCH_SHELL:
      free(*data);
      break;
    case MATCH_REGEX:
      regfree(*data);
      free(*data);
      break;
    case MATCH_PCRE:
      pd = (struct my_pcredata*)*data;
      pcre_free(pd->re);
      pcre_free(pd->re_extra);
      free(*data);
      break;
    case MATCH_NONE:
      break;
  }
  *match_type = MATCH_NONE;
  *match_func = NULL;
  *data = NULL;
}

int match_init(MatchType arg_type, const char *pattern, MatchType* match_type, MatchFunc* match_func, void **data) {
  /* For PCRE only */
  struct my_pcredata *pd;
  const char *error;
  int erroffset;

  switch(arg_type) {
    case MATCH_SIMPLE:
      if(pattern != NULL && strlen(pattern)>0) {
        *match_func = &simple_match;
        *data = (void*)strdup(pattern);
      } else {
        PyErr_SetString(PyExc_ValueError, "Empty pattern given.");
        return -1;
      }
      break;
    case MATCH_SHELL:
      if(pattern != NULL && strlen(pattern)>0) {
        *match_func = &shell_match;
        *data = (void*)strdup(pattern);
      } else {
        PyErr_SetString(PyExc_ValueError, "Empty pattern given.");
        return -1;
      }
      break;
    case MATCH_REGEX:
      *match_func = &regex_match;
      *data = malloc(sizeof(regex_t));
      if(*data == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Unable to allocate memory.");
        return -1;
      }
      if(regcomp(*data, pattern, REG_EXTENDED | REG_NOSUB) != 0) {
        PyErr_SetString(PyExc_RuntimeError, "Could not compile regex.");
        free(*data);
        return -1;
      }
      break;
    case MATCH_PCRE:
      *match_func = &pcre_match;
      *data = malloc(sizeof(struct my_pcredata));
      if(*data == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Unable to allocate memory.");
        return -1;
      }
      pd = (struct my_pcredata*)*data;

      pd->re = pcre_compile(pattern, 0, &error, &erroffset, NULL);
      if(pd->re == NULL) {
        PyErr_Format(PyExc_RuntimeError, "Could not compile regex at %d: %s", erroffset, error);
        free(*data);
        return -1;
      }
      pd->re_extra = pcre_study(pd->re, 0, &error);
      if(error != NULL) {
        PyErr_Format(PyExc_RuntimeError, "Could not study regex: %s", error);
        pcre_free(pd->re);
        free(*data);
        return -1;
      }
      break;
    default:
      PyErr_SetString(PyExc_ValueError, "Invalid matching method given.");
      return -1;
  }
  *match_type = arg_type;
  return 0;
}

void match_pyinit(PyObject *m) {
  PyModule_AddIntConstant(m, "MATCH_SIMPLE", MATCH_SIMPLE);
  PyModule_AddIntConstant(m, "MATCH_SHELL", MATCH_SHELL);
  PyModule_AddIntConstant(m, "MATCH_REGEX", MATCH_REGEX);
  PyModule_AddIntConstant(m, "MATCH_PCRE", MATCH_PCRE);
}