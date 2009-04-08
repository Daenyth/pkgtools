#!/bin/bash
# whoneeds package : shows explicitly installed packages that require some package

function whoneeds_f
{
    direct_needs=$(LC_ALL=C pacman -Qi $1 | tr '\n' ' ' |  sed 's/.*Required By *: *//' | sed 's/Conflicts With.*//')
    if pacman -Qi $1 | grep -q '^Install Reason : Explicitly installed'; then
        #echo "installed expicitly"
        echo $1
    fi
    if echo "$direct_needs" | grep -qv 'None'; then
        for i in $direct_needs; do
            whoneeds_f $i
        done
    fi
}

whoneeds_f $1 | sort -u

# vim: set ts=4 sw=4 et:
