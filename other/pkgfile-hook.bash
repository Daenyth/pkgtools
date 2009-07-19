#!/bin/bash
command_not_found_handle () {
	local _prev_command="$1"
	local pkgs="$(pkgfile -b -v "$_prev_command")"
	if [ ! -z "$pkgs" ]; then
		echo -e "\n$_prev_command may be found in the following packages:\n$pkgs"
	fi
}
