#include <Python.h>
#define _GNU_SOURCE 1
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <locale.h>
#include <time.h>
#include <archive.h>
#include <archive_entry.h>
#include <ctype.h>
#include <libgen.h>
#include "search.h"
#include "util.h"
#define ABUFLEN 1024

#define STRDUP(r, s, action) do { if(s != NULL) { r = strdup(s); if(r == NULL) { ALLOC_FAIL(strlen(s)); action; } } else { r = NULL; } } while(0)

/* Trim whitespace and newlines from a string [from lib/libalpm/util.c] */
char *strtrim(char *str) {
	char *pch = str;

	if (*str == '\0') {
		/* string is empty, so we're done. */
		return (str);
	}

	while (isspace((unsigned char)*pch)) {
		pch++;
	}
	if(pch != str) {
		memmove(str, pch, (strlen(pch) + 1));
	}

	/* check if there wasn't anything but whitespace in the string. */
	if (*str == '\0') {
		return(str);
	}

	pch = (str + (strlen(str) - 1));
	while (isspace((unsigned char)*pch)) {
		pch--;
	}
	*++pch = '\0';

	return (str);
}

/* Modified portion of _alpm_db_read from lib/libalpm/be_local.c */
int parse_depends(FILE *stream, PyObject **ppkg) {
	/* add to ppkg dict the values found in depends file:
	 * the list of depends
	 * the list of optdepends
	 * the list of provides
	 * the list of conflicts
	 */
	char line[1024];
	PyObject *s, *tmp, *pkg=*ppkg;

	while(!feof(stream)) {
		if(fgets(line, sizeof(line), stream) == NULL) {
			break;
		}
		strtrim(line);
		if(strcmp(line, "%DEPENDS%") == 0) {
			tmp = PyList_New(0);
			while(fgets(line, sizeof(line), stream) && strlen(strtrim(line))) {
				s = PyUnicode_FromString(strtrim(line));
				PyList_Append(tmp, s);
				Py_DECREF(s);
			}
			PyDict_SetItemString(pkg, "depends", tmp);
			Py_DECREF(tmp);
		} else if(strcmp(line, "%OPTDEPENDS%") == 0) {
			tmp = PyList_New(0);
			while(fgets(line, sizeof(line), stream) && strlen(strtrim(line))) {
				s = PyBytes_FromString(strtrim(line));
				PyList_Append(tmp, s);
				Py_DECREF(s);
			}
			PyDict_SetItemString(pkg, "optdepends", tmp);
			Py_DECREF(tmp);
		} else if(strcmp(line, "%CONFLICTS%") == 0) {
			tmp = PyList_New(0);
			while(fgets(line, sizeof(line), stream) && strlen(strtrim(line))) {
				s = PyUnicode_FromString(strtrim(line));
				PyList_Append(tmp, s);
				Py_DECREF(s);
			}
			PyDict_SetItemString(pkg, "conflicts", tmp);
			Py_DECREF(tmp);
		} else if(strcmp(line, "%PROVIDES%") == 0) {
			tmp = PyList_New(0);
			while(fgets(line, sizeof(line), stream) && strlen(strtrim(line))) {
				s = PyUnicode_FromString(strtrim(line));
				PyList_Append(tmp, s);
				Py_DECREF(s);
			}
			PyDict_SetItemString(pkg, "provides", tmp);
			Py_DECREF(tmp);
		}
	}

	return 0;
}

/* Modified portion of _alpm_db_read from lib/libalpm/be_local.c */
int parse_desc(FILE *stream, PyObject **ppkg) {
	/* add to ppkg dict the values found in desc file */
	char line[1024];
	PyObject *s, *pyl, *pkg=*ppkg;

	while(!feof(stream)) {
		if(fgets(line, sizeof(line), stream) == NULL) {
			break;
		}
		strtrim(line);
		if(strcmp(line, "%NAME%") == 0) {
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			PyObject *tmp = PyDict_GetItemString(pkg, "name"); /* borrowed ref. ! */
			if (tmp != NULL) {
				PyObject *pkgnamestr = PyUnicode_AsUTF8String(tmp);
				const char *pkgname = PyBytes_AsString(pkgnamestr);
				if(strcmp(strtrim(line), pkgname) != 0) {
					/* we have a problem */
					Py_DECREF(pkgnamestr);
					return -1;
				}
				Py_DECREF(pkgnamestr);
			} else {
				s = PyUnicode_FromString(strtrim(line));
				PyDict_SetItemString(pkg, "name", s);
				Py_DECREF(s);
			}
		} else if(strcmp(line, "%VERSION%") == 0) {
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			PyObject *tmp = PyDict_GetItemString(pkg, "version");
			if (tmp != NULL) {
				PyObject *pkgverstr = PyUnicode_AsUTF8String(tmp);
				const char *pkgver = PyBytes_AsString(pkgverstr);
				if(strcmp(strtrim(line), pkgver) != 0) {
					/* we have a problem */
					Py_DECREF(pkgverstr);
					return -1;
				}
				Py_DECREF(pkgverstr);
			} else {
				s = PyUnicode_FromString(strtrim(line));
				PyDict_SetItemString(pkg, "version", s);
				Py_DECREF(s);
			}
		} else if(strcmp(line, "%FILENAME%") == 0) {
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			s = PyBytes_FromString(strtrim(line));
			PyDict_SetItemString(pkg, "filename", s);
			Py_DECREF(s);
		} else if(strcmp(line, "%DESC%") == 0) {
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			s = PyBytes_FromString(strtrim(line));
			PyDict_SetItemString(pkg, "desc", s);
			Py_DECREF(s);
		} else if(strcmp(line, "%GROUPS%") == 0) {
			PyObject *groups = PyList_New(0);
			while(fgets(line, sizeof(line), stream) && strlen(strtrim(line))) {
				s = PyUnicode_FromString(strtrim(line));
				PyList_Append(groups, s);
				Py_DECREF(s);
			}
			PyDict_SetItemString(pkg, "groups", groups);
			Py_DECREF(groups);
		} else if(strcmp(line, "%URL%") == 0) {
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			s = PyBytes_FromString(strtrim(line));
			PyDict_SetItemString(pkg, "url", s);
			Py_DECREF(s);
		} else if(strcmp(line, "%LICENSE%") == 0) {
			PyObject *license = PyList_New(0);
			while(fgets(line, sizeof(line), stream) && strlen(strtrim(line))) {
				s = PyBytes_FromString(strtrim(line));
				PyList_Append(license, s);
				Py_DECREF(s);
			}
			PyDict_SetItemString(pkg, "license", license);
			Py_DECREF(license);
		} else if(strcmp(line, "%ARCH%") == 0) {
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			s = PyUnicode_FromString(strtrim(line));
			PyDict_SetItemString(pkg, "arch", s);
			Py_DECREF(s);
		} else if(strcmp(line, "%BUILDDATE%") == 0) {
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			strtrim(line);

			char first = tolower((unsigned char)line[0]);
			long ltmp;
			if(first > 'a' && first < 'z') {
				struct tm tmp_tm = {0}; /* initialize to null in case of failure */
				setlocale(LC_TIME, "C");
				strptime(line, "%a %b %e %H:%M:%S %Y", &tmp_tm);
				ltmp = (long)mktime(&tmp_tm); /* BAD! assuming time_t == long */
				setlocale(LC_TIME, "");
			} else {
				ltmp = atol(line);
			}
			pyl = PyLong_FromLong(ltmp);
			PyDict_SetItemString(pkg, "builddate", pyl);
			Py_DECREF(pyl);
		} else if(strcmp(line, "%INSTALLDATE%") == 0) {
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			strtrim(line);

			char first = tolower((unsigned char)line[0]);
			long ltmp;
			if(first > 'a' && first < 'z') {
				struct tm tmp_tm = {0}; /* initialize to null in case of failure */
				setlocale(LC_TIME, "C");
				strptime(line, "%a %b %e %H:%M:%S %Y", &tmp_tm);
				ltmp = mktime(&tmp_tm);
				setlocale(LC_TIME, "");
			} else {
				ltmp = atol(line);
			}
			pyl = PyLong_FromLong(ltmp);
			PyDict_SetItemString(pkg, "installdate", pyl);
			Py_DECREF(pyl);
		} else if(strcmp(line, "%PACKAGER%") == 0) {
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			s = PyBytes_FromString(strtrim(line));
			PyDict_SetItemString(pkg, "packager", s);
			Py_DECREF(s);
		} else if(strcmp(line, "%REASON%") == 0) {
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			pyl = PyLong_FromLong(atol(strtrim(line)));
			PyDict_SetItemString(pkg, "reason", pyl);
			Py_DECREF(pyl);
		} else if(strcmp(line, "%SIZE%") == 0 || strcmp(line, "%CSIZE%") == 0) {
			/* NOTE: the CSIZE and SIZE fields both share the "size" field
			 *       in the pkginfo_t struct.  This can be done b/c CSIZE
			 *       is currently only used in sync databases, and SIZE is
			 *       only used in local databases.
			 */
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			pyl = PyLong_FromLong(atol(strtrim(line)));
			PyDict_SetItemString(pkg, "size", pyl);
			/* also store this value to isize if isize is unset */
			PyDict_SetItemString(pkg, "isize", pyl);
			Py_DECREF(pyl);
		} else if(strcmp(line, "%ISIZE%") == 0) {
			/* ISIZE (installed size) tag only appears in sync repositories,
			 * not the local one. */
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			pyl = PyLong_FromLong(atol(strtrim(line)));
			PyDict_SetItemString(pkg, "isize", pyl);
			Py_DECREF(pyl);
		} else if(strcmp(line, "%MD5SUM%") == 0) {
			/* MD5SUM tag only appears in sync repositories,
			 * not the local one. */
			if(fgets(line, sizeof(line), stream) == NULL) {
				goto error;
			}
			s = PyUnicode_FromString(strtrim(line));
			PyDict_SetItemString(pkg, "md5sum", s);
			Py_DECREF(s);
		} else if(strcmp(line, "%REPLACES%") == 0) {
			PyObject *replaces = PyList_New(0);
			while(fgets(line, sizeof(line), stream) && strlen(strtrim(line))) {
				s = PyUnicode_FromString(strtrim(line));
				PyList_Append(replaces, s);
				Py_DECREF(s);
			}
			PyDict_SetItemString(pkg, "replaces", replaces);
			Py_DECREF(replaces);
		} else if(strcmp(line, "%FORCE%") == 0) {
			PyDict_SetItemString(pkg, "force", Py_True);
		}
	}

	return 0;

error:
	return -1;
}

PyObject *pkg_info(PyObject *self, PyObject *args) {
	/* collect package info of packages listed in given .files.tar.gz files
	 * return a list of dict */
	int found, existing;
	char *l = NULL, *p, *v;
	char pname[ABUFLEN], *fname, *dname;
	const char *filename=NULL, *pkgname;
	struct stat st;
	struct archive *a;
	struct archive_entry *entry;
	FILE *stream = NULL;
	PyObject *ret=NULL, *pkgnames_list=NULL, *pkg=NULL, *waiting_dict=NULL;
	Py_ssize_t lp, i;

	if (!PyArg_ParseTuple(args, "sO", &filename, &pkgnames_list)) {
		PyErr_SetString(PyExc_ValueError, "pkg_info() has invalid arguments");
		return NULL;
	}
	if (filename == NULL || strlen(filename)<=0) {
		PyErr_SetString(PyExc_ValueError, "pkg_info() was given an empty files tarball name.");
		return NULL;
	}

	if (!PyList_Check(pkgnames_list)) {
		PyErr_SetString(PyExc_ValueError, "pkg_info() 2nd argument must be a list");
		return NULL;
	}
	lp = PyList_Size(pkgnames_list);
	if ( lp == 0) {
		return PyList_New(0);
	}

	pname[ABUFLEN-1]='\0';
	if(stat(filename, &st)==-1 || !S_ISREG(st.st_mode)) {
		PyErr_Format(PyExc_IOError, "File does not exist: %s\n", filename);
		return NULL;
	}
	ret = PyList_New(0);
	if (ret == NULL) {
		goto error;
	}
	waiting_dict = PyDict_New();
	if (waiting_dict == NULL) {
		goto error;
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
		if (splitname(dname, &p, &v) == -1) {
			archive_read_data_skip(a);
			continue;
		}
		found = 0;
		for (i=0; i<lp; i++) {
			PyObject *pkgnamestr = PyList_GetItem(pkgnames_list, i);
			pkgname = PyBytes_AsString(pkgnamestr);
			if (pkgname == NULL) {
				goto error;
			}
			if (strcmp(p, pkgname) == 0) {
				found = 1;
				//Py_DECREF(pkgnamestr);
				break;
			}
			//Py_DECREF(pkgnamestr);
		}
		free(p);
		free(v);

		if (!found) {
			archive_read_data_skip(a);
			continue;
		}

		pkg = PyDict_GetItemString(waiting_dict, pkgname);
		existing = 1;
		if (pkg == NULL) {
			existing = 0;
			pkg = PyDict_New();
			if (pkg == NULL) {
				goto error;
			}
		}

		if(strcmp(fname, "desc") == 0) {
			stream = open_archive_stream(a);
			if (!stream) {
				PyErr_SetString(PyExc_IOError, "Unable to open archive stream.");
				goto error;
			}

			if (parse_desc(stream, &pkg) == -1) {
				fclose(stream);
				if (!existing) Py_DECREF(pkg);
				continue;
			}
			fclose(stream);
		} else if (strcmp(fname, "depends") == 0) {
			stream = open_archive_stream(a);
			if (!stream) {
				PyErr_SetString(PyExc_IOError, "Unable to open archive stream.");
				goto error;
			}

			if (parse_depends(stream, &pkg) == -1) {
				fclose(stream);
				if (!existing) Py_DECREF(pkg);
				continue;
			}
			fclose(stream);
		} else {
			archive_read_data_skip(a);
			continue;
		}

		if (existing) {
			PyList_Append(ret, pkg);
			PyDict_DelItemString(waiting_dict, pkgname);
			pkg = NULL;
		} else {
			PyDict_SetItemString(waiting_dict, pkgname, pkg);
			Py_DECREF(pkg);
		}
	}
	if(l)
		free(l);

	archive_read_finish(a);

	/* we discard element still present in waiting_dict because they miss either the desc
	 * or depends values */
	Py_DECREF(waiting_dict);

	return ret;

error:
	Py_XDECREF(ret);
	Py_XDECREF(waiting_dict);
	Py_XDECREF(pkg);
	return NULL;
}
