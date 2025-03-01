"""Miscellaneous utilities

This module has utilities for everyday work such UI/UX (argument parsing,
interactive ascii menu) and some R utilities (match_arg, expand_grid, dput)
"""

import argparse as _argparse
import itertools as _itertools
import numpy as _np
import pandas as _pd
import re as _re
import readline as _readline
import types as _types

from pylbmisc.iter import unique as _unique
from inspect import getsource as _getsource
from typing import Sequence as _Sequence
from pprint import pformat as _pformat

_readline.parse_and_bind("set editing-mode emacs")


def argparser(opts):
    """Helper function for argument parsing.

    Examples
    --------
    >>> import pylbmisc as lb # third party
    >>> # from ..utils import argparser # in scripts directory
    >>>
    >>> opts = (
    >>>   # (param, help, default, type)
    >>>   # --dirs
    >>>   ("dirs", "str: comma separated list of exercise source directories","~/src/pypkg/exercises/db", str),
    >>>   # --lists
    >>>   ("lists", "str: comma separated list of file with lists of source dir", None, str),
    >>>   # --outfile
    >>>   ("outfile", "str:  sqlite3 db to save", "~/.exercises.db", str))
    >>>
    >>> args = lb.utils.argparser(opts)
    >>> dirs = args["dirs"]
    >>> dirs = dirs.split(",")
    >>> lists = args["lists"]
    >>> lists = lists.split(",")
    >>> outfile = args["outfile"]
    >>> print({"dirs": dirs, "lists": lists, "outfile": outfile})
    """
    parser = _argparse.ArgumentParser()
    # defaults = {}
    for i in opts:
        optname = i[0]
        optdescription = i[1]
        optdefault = i[2]
        opttype = i[3]
        # create help string and add argument to parsing
        help_string = "{0} (default: {1})".format(
            optdescription, str(optdefault)
        )
        parser.add_argument("--" + optname, help=help_string, type=str)
    # do parsing
    args = vars(parser.parse_args())  # vars to change to a dict
    # defaults settings and types management
    for i in opts:
        optname = i[0]
        optdescription = i[1]
        optdefault = i[2]
        opttype = i[3]
        # se il valore è a none in args impostalo al valore di default
        # specificato
        if args[optname] is None:
            args[optname] = optdefault
        # se il tipo è logico sostituisci un valore possibile true con
        # l'equivalente python
        if opttype == bool:
            # mv to character if not already (not if used optdefault)
            args[optname] = str(args[optname])
            true_values = (
                "true",
                "True",
                "TRUE",
                "t",
                "T",
                "1",
                "y",
                "Y",
                "yes",
                "Yes",
                "YES",
            )
            if args[optname] in true_values:
                args[optname] = "True"
            else:
                args[optname] = ""
        # converti il tipo a quello specificato, a meno che non sia None se no lascialo così
        if args[optname] is not None:
            args[optname] = opttype(args[optname])
    return args


def line_to_numbers(x: str) -> list[int]:
    """transform a string of positive numbers "1 2-3, 4, 6-10" into a
    list [1,2,3,4,6,7,8,9,10]

    Examples
    --------
    >>> line_to_numbers("1, 2-5")
    """
    # replace comma with white chars
    x = x.replace(",", " ")
    # keep only digits, - and white spaces
    x = _re.sub(r"[^\d\- ]", "", x)
    # split by whitespaces
    spl = x.split(" ")
    # change ranges to proper
    expanded = []
    single_page_re = _re.compile("^[0-9]+$")
    pages_range_re = _re.compile("^([0-9]+)-([0-9]+)$")
    for i in range(len(spl)):
        # Check if the single element match one of the regular expression
        single_page = single_page_re.match(spl[i])
        pages_range = pages_range_re.match(spl[i])
        if single_page:
            # A) One single page: append it to results
            expanded.append(spl[i])
        elif pages_range:
            # B) Pages range: append a list of (expanded) pages to results
            first = int(pages_range.group(1))
            second = int(pages_range.group(2))
            # step is 1 if first is less than or equal to second or -1
            # otherwise
            step = 1 * int(first <= second) - 1 * int(first > second)
            if step == 1:
                second += 1
            elif step == -1:
                second -= 1
            else:
                # do nothing (ignore if they don't match)
                pass
            expanded_range = [str(val) for val in range(first, second, step)]
            expanded += expanded_range
        else:
            ValueError(
                str(spl[i])
                + "does not match a single page re nor a pages range re."
            )
    # coerce to integer expanded
    res: list[int] = [int(x) for x in expanded]
    return res


def menu(choices: _Sequence[str],
         title: str | None = None,
         allow_repetition: bool = False,
         strict: bool = True,
         ) -> _Sequence[str]:
    """
    CLI menu for user single/multiple choices

    Parameters
    ----------
    choices: list of string
         printed choices
    title: str
         a pretty printed title
    allow_repetition: bool
         multiple selected items
    strict: bool
         all the selection number are among the available ones (or take the consistent otherwise)
    """
    available_ind = [i + 1 for i in range(len(choices))]
    avail_with_0 = [0] + available_ind
    the_menu = "\n".join([str(i) + ". " + str(c) for i, c in zip(available_ind, choices)])
    if title:
        ascii_header(title)
    print(the_menu, "\n")
    select_msg = "Selection (values as '1, 2-3, 6') or 0 to exit: "
    ind = line_to_numbers(input(select_msg))
    # normalize to list (for single selections, for now)
    if not isinstance(ind, list):
        ind = list(ind)
    if strict:
        # continue asking for input until all index are between the selectable
        while not all([i in avail_with_0 for i in ind]):
            not_in = [i for i in ind if i not in avail_with_0]
            print("Not valid insertion: ", not_in, "\n")
            ind = line_to_numbers(input(select_msg))
            if not isinstance(ind, list):
                ind = list(ind)
    else:
        # keep only the input in avail_with_0
        allowed = [i for i in ind if i in avail_with_0]
        any_not_allowed = not all(allowed)
        if any_not_allowed:
            print(
                "Removed some values (not 0 or specified possibilities): ",
                list(set(ind) - set(allowed)),
                ".",
            )
            ind = allowed
    # make unique if not allowed repetitions
    if not allow_repetition:
        ind = list(_unique(ind))
    # obtain the selection: return always a list should simplify the code
    rval = [choices[i - 1] for i in ind if i != 0]
    return rval


def ascii_header(x: str) -> None:
    """
    Create an ascii header given a string as title.

    Examples
    --------
    >>> ascii_header("Title")
    """
    header = "=" * len(x)
    print(header)
    print(x)
    print(header, "\n")


def match_arg(arg, choices):
    """R's match.arg equivalent for programming function for interactive use

    Examples
    --------
    >>> # questo ritorna errore perché matcha troppo
    >>> user_input = "foo"
    >>> a = match_arg(user_input, ["foobar", "foos", "asdomar"])

    >>> # questo è ok e viene espanso
    >>> user_input2 = "foob"
    >>> a = match_arg(user_input2, ["foobar", "foos", "asdomar"])
    >>> print(a)
    """
    res = [expanded for expanded in choices if expanded.startswith(arg)]
    choices_str = ", ".join(choices)
    l = len(res)
    if l == 0:
        msg = f"Parameter {arg} must be one of: {choices_str}"
        raise ValueError(msg)
    elif l > 1:
        msg = f"Parameter {arg} matches multiple choices from: {choices_str}"
        raise ValueError(msg)
    else:
        return res[0]


def expand_grid(dictionary):
    # https://stackoverflow.com/questions/12130883
    """Replacement for R's expand.grid

    Examples
    --------
    >>> stratas =  {"centres": ["ausl re", "ausl mo"],
                    "agecl": ["<18", "18-65", ">65"],
                    "foo": ["1"]}
    >>> lb.utils.expand_grid(stratas)
    """
    rows = [row for row in _itertools.product(*dictionary.values())]
    return _pd.DataFrame(rows, columns=dictionary.keys())


def dput(x) -> None:
    """Try to print the ASCII representation of a certain object

    Parameters
    ----------
    x : anything
        data to be printed

    Examples
    --------
    >>> from pylbmisc.utils import dput
    >>> import pylbmisc as lb
    >>> List = list(range(0, 200))
    >>> dput(List)
    >>> Dict = {"a": 1, "b": 2}
    >>> dput(Dict)
    >>> Dict2 = {"a": List, "b": List}
    >>> dput(Dict2)
    >>> nparray = _np.array(List)
    >>> dput(nparray)
    >>> series = _pd.Series(List)
    >>> dput(series)
    >>>
    >>> def function() -> None:
    >>>     pass
    >>> dput(function)
    >>> lb.datasets.ls()
    >>> df = lb.datasets.load('aidssi.csv')
    >>> dput(df)
    """
    if isinstance(x, _types.FunctionType):  # special cases: don't use repr
        print(_getsource(x))
    elif isinstance(x, _pd.DataFrame):
        dict_rep = _pformat(x.to_dict(orient="list"), compact=True)
        print(f"pd.DataFrame({dict_rep})")
    elif isinstance(x, _pd.Series):
        list_rep = _pformat(x.to_list(), compact=True)
        print(f"pd.Series({list_rep})")
    elif isinstance(x, _np.ndarray):
        list_rep = _pformat(nparray.tolist(), compact=True)
        print(f"np.array({list_rep})")
    else:
        obj_repr = _pformat(x, compact=True)
        print(obj_repr)


def table(x: _pd.Series | None = None,
          y: _pd.Series | None = None,
          **kwargs):
    """Emulate the good old table for quick crosstabs

    Parameters
    ----------
    x: pd.Series
       first variable
    y: pd.Series
       second variable
    kwargs: Any
       other parameters passed to Series.value_counts or pd.crosstab
    """
    if x is None:
        msg = "Almeno una variable"
        raise ValueError(msg)
    if y is None:
        return x.value_counts(dropna=False, **kwargs)
    else:
        return _pd.crosstab(x, y, dropna=False, margins=True, **kwargs)


if __name__ == "__main__":
    import pylbmisc as lb
    List = list(range(0, 200))
    dput(List)
    Dict = {"a": 1, "b": 2}
    dput(Dict)
    Dict2 = {"a": List, "b": List}
    dput(Dict2)
    nparray = _np.array(List)
    dput(nparray)
    series = _pd.Series(List)
    dput(series)

    def function() -> None:
        pass
    dput(function)
    lb.datasets.ls()
    df = lb.datasets.load("aidssi.csv")
    dput(df)
