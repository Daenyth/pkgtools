#!/bin/bash
command_not_found_handle () {
	local command="$1"
	local pkgs="$(pkgfile -b -v "$command")"
	if [ ! -z "$pkgs" ]; then
		echo -e "\n$command may be found in the following packages:\n$pkgs"
		return 0
	fi
	printf "bash: $(gettext bash "%s: command not found")\n" $command >&2
	return 127
}
export -f command_not_found_handle
