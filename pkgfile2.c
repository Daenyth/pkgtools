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
#define FBUFLEN 10240

cookie_io_functions_t archive_stream_funcs = {
.read = archive_read_data,
.write = NULL,
.seek = NULL,
.close = NULL
};

FILE *open_archive_stream(struct archive *archive) {
  return fopencookie(archive, "r", archive_stream_funcs);
}

/*
 * Matches the db entry f to the argument m
 * The names must either match completely,
 * or m must match the portion of f after the last /
 */
int match_filename(char *f, const char *m) {
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

void search_file(const char *repo, const char *pattern) {
  struct archive *a;
  struct archive_entry *entry;
  struct stat st;
  char pname[ABUFLEN], *fname, *dname, filename[ABUFLEN];
  char *l = NULL;
  FILE *stream = NULL;
  size_t n = 0;
  int nread;
  pname[ABUFLEN-1]='\0';
  strncpy(filename, repo, ABUFLEN);
  strncat(filename, ".files.tar.gz", ABUFLEN);
  filename[ABUFLEN-1]='\0';

  if(stat(filename, &st)==-1 || !S_ISREG(st.st_mode)) {
    fprintf(stderr, "File does not exist: %s\n", filename);
    return;
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
      fprintf(stderr, "Unable to open archive stream.\n");
      exit(1);
    }

    while((nread = getline(&l, &n, stream)) != -1) {
      /* Note: getline returns -1 on both EOF and error. */
      /* So I'm assuming that nread > 0. */
      if(l[nread - 1] == '\n')
        l[nread - 1] = '\0';	/* Clobber trailing newline. */
      if(strcmp(l, "%FILES%") && match_filename(l, pattern))
        printf("%s/%s: %s\n", repo, dname, l);
    }
    fclose(stream);
  }

  if(l)
    free(l);

  archive_read_finish(a);
}

int main(int argc, char *argv[]) {
  const char *repos[] = { "testing", "core", "extra", "community", "community-testing", NULL };
  const char **repo;
  if(argc<1) {
    fprintf(stderr, "Usage: %s pattern\n", argv[0]);
    return -1;
  }
  for(repo=&repos[0]; *repo!=NULL; repo++)
    search_file(*repo, argv[1]);
  return 0;
}
