#include <stdlib.h>
#include <string.h>

/* from pacman/lib/libalpm/be_files.c */

int splitname(const char *target, char **pkgname, char **pkgver) {
	/* the format of a db entry is as follows:
	 *    package-version-rel/
	 * package name can contain hyphens, so parse from the back- go back
	 * two hyphens and we have split the version from the name.
	 */
	char *tmp, *p, *q;

	if(target == NULL) {
		return(-1);
	}
	tmp = strdup(target);
	p = tmp + strlen(tmp);

	/* do the magic parsing- find the beginning of the version string
	 * by doing two iterations of same loop to lop off two hyphens */
	for(q = --p; *q && *q != '-'; q--);
	for(p = --q; *p && *p != '-'; p--);
	if(*p != '-' || p == tmp) {
		return(-1);
	}

	*pkgver = strdup(p+1);
	/* insert a terminator at the end of the name (on hyphen)- then copy it */
	*p = '\0';
	*pkgname = strdup(tmp);

	free(tmp);
	return(0);
}

