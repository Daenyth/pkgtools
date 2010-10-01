# Licensed under GPL, see COPYING for the whole text
#
# This script will look-up command in the database and suggest
# installation of packages available from the repository
#
function command_not_found_handler() {
  local command="$1"
  [ -n "$command" ] && [ -x /usr/bin/pkgfile ] && {
      echo -e "searching for \"$command\" in repos..."
      local pkgs="$(pkgfile -b -v "$command")"
      if [ ! -z "$pkgs" ]; then
        echo -e "\"$command\" may be found in the following packages:\n\n${pkgs}\n"
      fi
  }
  return 1
}
# vim: set filetype=zsh :
