#ifndef SEARCH_H
#define SEARCH_H

#include <archive.h>

FILE *open_archive_stream(struct archive *archive);
void search_pyinit(PyObject *m);

#endif /* SEARCH_H */
