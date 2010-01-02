#!/bin/bash
# whoneeds package : shows explicitly installed packages that require some package

# we use an associative array to get uniqueness for "free"
typeset -A root_packages
query=$1

function whoneeds_f () {

    local package=$1
    
    # If we've already found $package, we exit, else we open the 
    # the possibility of infinitely traversing a subset of nodes
    [[ ${root_packages[$package]} -eq 1 ]] && return 0 
    
    # we do this so that we can make a single call to pacman
    # to get both bits of information that we require
    result=( $(LC_ALL=c pacman -Qi $package | awk -F':' \
      'BEGIN { dependents = none; explicit = 0 }
       {
          if ($1 ~ /^Required By/ && $2 !~ /None/) {  dependents = $2 }
          if ($1 ~ /^Install Reason $/ && $2 ~/^ Explicitly installed/) { explicit = 1 }
       }
       END { print explicit,dependents}') )

    if [[ ${result[0]} -eq 1 ]]; then
        # we found an explicitly installed package that relies on
        # the original query. Add it to our array, provided it isn't
        # the original query, as that would be useless information
        [[ "$query" != "$package" ]] && root_packages[$package]=1
    fi
    if [[ "${result[1]}" != "none" ]]; then
        # iterate over our 'Required By:' packages
        dependents=${result[@]:1:${#result[*]}}
        for i in $dependents; do
            whoneeds_f $i
        done
    fi
}

whoneeds_f $1

echo "Packages that depend on [$query]"
if [[ -n "${!root_packages[@]}" ]]; then
    echo "  ${!root_packages[@]}"
    exit 0
fi
echo "  None"
exit 1

# vim: set ts=4 sw=4 et:
