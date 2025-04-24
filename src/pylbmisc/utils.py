"""Miscellaneous utilities

This module has utilities for everyday work such UI/UX (argument parsing,
interactive ascii menu)
"""

import argparse as _argparse
import inspect as _inspect
import pandas as _pd
import re as _re
import readline as _readline
import subprocess as _subprocess
import tempfile as _tempfile

from pylbmisc.iter import unique as _unique
from typing import Sequence as _Sequence


_readline.parse_and_bind("set editing-mode emacs")


def view(df: _pd.DataFrame | _pd.Series) -> None:
    """View a pd.DataFrame using LibreOffice.

    Parameters
    ----------
    df:
        the dataframe to be visualized

    Examples
    --------
    >>> # lb.dm.view(df) # commented to avoid tests fails
    """
    if not isinstance(df, (_pd.DataFrame, _pd.Series)):
        msg = "Only dataframes are visualized."
        raise Exception(msg)
    tempfile = _tempfile.mkstemp(suffix=".xlsx")
    fname = tempfile[1]
    df.to_excel(fname)
    _subprocess.Popen(["libreoffice", fname])




def interactive():
    """Check if python is running in interactive mode

    Returns
    -------
    bool: True if running in interactive mode, False if running using
         ipykernel/quarto

    Examples
    --------
    >>> import sys
    >>> from pyblmisc.utils import interactive
    >>> interactive()
    False  # tests aren't run interactively
    """
    parent_frame = _inspect.currentframe().f_back
    test = "'__PYTHON_EL_eval' in dir()"  # active in Emacs, not in quarto
    return eval(test, parent_frame.f_locals, parent_frame.f_globals)


def argparser(opts):
    """Helper function for argument parsing.

    Examples
    --------
    >>> import pylbmisc as lb # third party
    >>>
    >>> opts = (
    ...  # (param, help, default, type)
    ...  # --dirs
    ...  ("dirs", "str: comma separated list of exercise source directories",
    ...  "~/src/pypkg/exercises/db", str),
    ...  # --list
    ...  ("list", "str: comma separated list of file with lists of source dir",
    ...   None, str),
    ...  # --outfile
    ...  ("outfile", "str:  sqlite3 db to save", "~/.exercises.db", str))
    >>> # args = lb.utils.argparser(opts)   # tests, you know ...
    >>> # dirs = args["dirs"]
    >>> # dirs = dirs.split(",")
    >>> # lists = args["lists"]
    >>> # lists = lists.split(",")
    >>> # outfile = args["outfile"]
    >>> # print({"dirs": dirs, "lists": lists, "outfile": outfile})
    """
    parser = _argparse.ArgumentParser()
    # defaults = {}
    for i in opts:
        optname = i[0]
        optdescription = i[1]
        optdefault = i[2]
        opttype = i[3]
        # create help string and add argument to parsing
        help_string = f"{optdescription} (default: {optdefault!r})"
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
        if opttype is bool:
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
        # converti il tipo a quello specificato, a meno che non sia None se no
        # lascialo così
        if args[optname] is not None:
            args[optname] = opttype(args[optname])
    return args


def line_to_numbers(x: str) -> list[int]:
    """Transform a string of positive numbers "1 2-3, 4, 6-10" into a
    list [1,2,3,4,6,7,8,9,10]

    Parameters
    ----------
    x: str
       string containing numbers such as printers pages lists

    Examples
    --------
    >>> from pylbmisc.utils import line_to_numbers
    >>> line_to_numbers("1, 2-4, 16-18")
    [1, 2, 3, 4, 16, 17, 18]
    """
    # # replace comma with white chars
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
         all the selection number are among the available ones
         (or take the consistent otherwise)
    """
    available_ind = [i + 1 for i in range(len(choices))]
    avail_with_0 = [0, *available_ind]
    the_menu = "\n".join([str(i) + ". " + str(c)
                          for i, c in zip(available_ind, choices)])
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
        while not all(i in avail_with_0 for i in ind):
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

    Parameters
    ----------
    x: str
        message to be prettyprinted

    Examples
    --------
    >>> import pylbmisc as lb
    >>> ascii_header("Hello, world!")
    =============
    Hello, world!
    =============
    <BLANKLINE>
    """
    header = "=" * len(x)
    msg = f"{header}\n{x}\n{header}\n"
    print(msg)


# def match_arg(arg, choices):
#     """R's match.arg equivalent for programming function for interactive use

#     Examples
#     --------
#     >>> from pylbmisc.utils import match_arg
#     >>> # questo ritorna errore perché matcha troppo
#     >>> user_input = "foo"
#     >>> # a = match_arg(user_input, ["foobar", "foos", "asdomar"]) # errore
#     >>> # questo è ok e viene espanso
#     >>> user_input2 = "foob"
#     >>> a = match_arg(user_input2, ["foobar", "foos", "asdomar"])
#     >>> print(a)
#     foobar
#     """
#     res = [expanded for expanded in choices if expanded.startswith(arg)]
#     choices_str = ", ".join(choices)
#     res_len = len(res)
#     if res_len == 0:
#         msg = f"Parameter {arg} must be one of: {choices_str}"
#         raise ValueError(msg)
#     elif res_len > 1:
#         msg = f"Parameter {arg} matches multiple choices from: {choices_str}"
#         raise ValueError(msg)
#     else:
#         return res[0]


# def expand_grid(dictionary):
#     # https://stackoverflow.com/questions/12130883
#     """Replacement for R's expand.grid

#     Examples
#     --------
#     >>> import pylbmisc as lb
#     >>> stratas =  {"centres": ["ausl re", "ausl mo"],
#     ...             "agecl": ["<18", "18-65", ">65"],
#     ...             "foo": ["1"]}
#     >>> lb.utils.expand_grid(stratas)
#        centres  agecl foo
#     0  ausl re    <18   1
#     1  ausl re  18-65   1
#     2  ausl re    >65   1
#     3  ausl mo    <18   1
#     4  ausl mo  18-65   1
#     5  ausl mo    >65   1
#     """
#     rows = [row for row in _itertools.product(*dictionary.values())]
#     return _pd.DataFrame(rows, columns=dictionary.keys())


# def dput(x) -> None:
#     """Try to print the ASCII representation of a certain object

#     Parameters
#     ----------
#     x : anything
#         data to be printed

#     Examples
#     --------
#     >>> import numpy as np
#     >>> import pandas as pd
#     >>> from pylbmisc.utils import dput
#     >>> import pylbmisc as lb
#     >>> List = list(range(0, 15))
#     >>> dput(List)
#     [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
#     >>> Dict = {"a": 1, "b": 2}
#     >>> dput(Dict)
#     {'a': 1, 'b': 2}
#     >>> Dict2 = {"a": List, "b": List}
#     >>> dput(Dict2)
#     {'a': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
#      'b': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]}
#     >>> nparray = np.array(List)
#     >>> dput(nparray)
#     np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])
#     >>> series = pd.Series(List)
#     >>> dput(series)
#     pd.Series([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])
#     >>> def function() -> None:
#     ...     pass
#     >>> dput(function)
#     def function() -> None:
#         pass
#     <BLANKLINE>
#     >>> df = lb.datasets.load()
#     >>> dput(df)
#     pd.DataFrame({'dead': [6, 13, 18, 28, 52, 53, 61, 60],
#      'logdose': [1.691, 1.724, 1.755, 1.784, 1.811, 1.837, 1.861, 1.884],
#      'n': [59, 60, 62, 56, 63, 59, 62, 60]})
#     """
#     if isinstance(x, _types.FunctionType):  # special cases: don't use repr
#         print(_inspect.getsource(x))
#     elif isinstance(x, _pd.DataFrame):
#         dict_rep = _pformat(x.to_dict(orient="list"), compact=True)
#         print(f"pd.DataFrame({dict_rep})")
#     elif isinstance(x, _pd.Series):
#         list_rep = _pformat(x.to_list(), compact=True)
#         print(f"pd.Series({list_rep})")
#     elif isinstance(x, _np.ndarray):
#         list_rep = _pformat(x.tolist(), compact=True)
#         print(f"np.array({list_rep})")
#     else:
#         obj_repr = _pformat(x, compact=True)
#         print(obj_repr)


# def table(x: _pd.Series | None = None,
#           y: _pd.Series | None = None,
#           **kwargs):
#     """Emulate the good old table for quick crosstabs.

#     Parameters
#     ----------
#     x: pd.Series
#        first variable
#     y: pd.Series
#        second variable
#     kwargs: Any
#        other parameters passed to Series.value_counts or pd.crosstab
#     """
#     if x is None:
#         msg = "Almeno una variable"
#         raise ValueError(msg)
#     if y is None:
#         return x.value_counts(dropna=False, **kwargs)
#     else:
#         return _pd.crosstab(x, y, dropna=False, margins=True, **kwargs)


# def in(x: list, y: list):
#     """Emulate R's %in% for lists"""
#     return [a in set(y) for a in x]


# def nin(x: list, y: list):
#     """Emulate my %nin% for lists"""
#     return [a not in set(y) for a in x]

    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
