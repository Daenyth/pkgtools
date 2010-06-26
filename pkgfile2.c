#include <archive.h>
#include <archive_entry.h>
#include <stdio.h>
#include <libgen.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#define ABUFLEN 1024
#define FBUFLEN 10240

/* 
 * Reads a line from the archive a
 * If the line is longer than FBUFLEN-1, it will be truncated
 * Returns NULL if end of file has been reached
 */
char *my_archive_readline(struct archive *a) {
  static char buf[FBUFLEN];
  static char lbuf[FBUFLEN];
  static size_t fill = 0;
  char *n;
  ssize_t r;
  
  r = archive_read_data(a, buf+fill, FBUFLEN-fill);
  fill += r;
  if(r<0 || fill==0) {
    fill = 0;
    return NULL;
  }

  n = index(buf, '\n');
  if(n==NULL) {
    n = buf+FBUFLEN-1;
    fill -= n-buf;
  } else {
    fill -= n-buf+1;
  }
  strncpy(lbuf, buf, n-buf);
  lbuf[n-buf]='\0';
  if(*n=='\n')
    memmove(buf, n+1, fill);
  else
    memmove(buf, n, fill);
  return lbuf;
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
  char pname[ABUFLEN], *fname, *dname, *l, filename[ABUFLEN];
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
    
    while((l = my_archive_readline(a))!=NULL)
      if(strcmp(l, "%FILES%") && match_filename(l, pattern))
        printf("%s/%s: %s\n", repo, dname, l);
  }
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
