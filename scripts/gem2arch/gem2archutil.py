#!/usr/bin/env python
import sys
from functools import reduce

global allowed_levels
allowed_levels = ( "E!", "W:", "I:" )

def message(prefix, text):
    global allowed_levels
    retval = prefix + " "
    if prefix in allowed_levels:
        retval += wrap(text, 75)
        retval = retval.strip() + "\n"
        sys.stderr.write(retval)

def error(text):
    message("E!", text)

def warn(text):
    message("W:", text)

def inform(text):
    message("I:", text)

def wrap(text, width):
    """
    A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line
    breaks are posix newlines (\n).
    """
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[(len(line)-line.rfind('\n')-1
                         + len(word.split('\n',1)[0]
                              ) >= width)],
                   word),
                  text.split(' ')
                 )

def indent(string):
    if string:
        string = "  " + string
        string = string.replace("\n", "\n  ")
        return string
