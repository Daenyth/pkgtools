#ifndef MATCH_H
#define MATCH_H

typedef enum {
  MATCH_NONE,
  MATCH_SIMPLE,
  MATCH_SHELL,
  MATCH_REGEX,
  MATCH_PCRE
} MatchType;

typedef int (*MatchFunc)(const char*, void*);

void match_reset(MatchType* match_type, MatchFunc* match_func, void **data);
int match_init(MatchType arg_type, const char *pattern, MatchType* match_type, MatchFunc* match_func, void **data);
void match_pyinit(PyObject *m);

#endif /* MATCH_H */
