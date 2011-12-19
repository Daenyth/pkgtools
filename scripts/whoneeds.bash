#!/bin/bash
# whoneeds package : shows explicitly installed packages that require some package

# we use associative arrays to get uniqueness for "free"
typeset -A root_packages
typeset -A walked_nodes
query=$1

function walk_nodes () {

    local package=$1

    # if we've walked this node before, skip. This drastically
    # reduces overhead for a relatively cheap operation
    [[ ${walked_nodes[$package]} -eq 1 ]] && return 0
    walked_nodes[$package]=1

    # we do this so that we can make a single call to pacman
    # to get both bits of information that we require
    result=( $(LC_ALL=c pacman -Qi $package | awk -F':' \
      'BEGIN { tag = ""; dependents = ""; explicit = 0 }
       {
          # since the formatting of the pacman output is more for human
          # consumption than programmatic, we find ourselves with the following need.
          # if we have two fields, then we know we have a proper identifier on the line
          # so we store the identifier as a current tag
          # All identifier checks are made against the current tag, which allows us
          # to deal with instances where "Required By" spans lines
          if (NF == 2) { tag = $1 }
          if (tag ~ /^Required By[ ]*$/) {  dependents = dependents $(NF) }
          if ($1 ~ /^Install Reason $/ && $2 ~/^ Explicitly installed/) { explicit = 1 }
       }
       END { print explicit,dependents}') )

    # and if we hit an issue retrieving package information
    if [[ ${#result[*]} -lt 2 ]]; then
            echo "error: could not get information on $package" 1>&2
            exit 3
    fi
    if [[ ${result[0]} -eq 1 ]]; then
        # we found an explicitly installed package that relies on
        # the original query. Add it to our array, provided it isn't
        # the original query, as that would be useless information
        [[ "$query" != "$package" ]] && root_packages[$package]=1
    fi
    if [[ "${result[1]}" != "None" ]]; then
        # iterate over our 'Required By:' packages
        dependents=${result[@]:1:${#result[*]}}
        for i in $dependents; do
            walk_nodes $i
        done
    fi
}


if [ $# -ne 1 ]; then
    echo "error: unexpected number of arguments" 1>&2
    echo "Usage: $(basename $0) <package-name>"
    exit 2
fi

walk_nodes $1
echo "Packages that depend on [$query]"
if [[ -n "${!root_packages[*]}" ]]; then
    for pkg in "${!root_packages[@]}"; do
        echo "  $pkg"
    done | sort
    exit 0
fi
echo "  None"
exit 1

# vim: set ts=4 sw=4 et:
