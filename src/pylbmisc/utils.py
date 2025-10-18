"""Miscellaneous utilities

This module has utilities for everyday work such UI/UX (argument parsing,
interactive ascii menu), system info
"""

import argparse as _argparse
import datetime as _dt
import inspect as _inspect
import re as _re
import readline as _readline
import sys as _sys
import time as _time
import types as _types

from pprint import pp as _pp
from pylbmisc.iter import unique as _unique
from typing import Sequence as _Sequence


_readline.parse_and_bind("set editing-mode emacs")


def is_interactive():
    """Check if python is running in interactive mode

    Returns
    -------
    bool: True if running in interactive mode, False if running using
         ipykernel/quarto

    Examples
    --------
    >>> import sys
    >>> from pyblmisc.utils import is_interactive
    >>> is_interactive()
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


def _imports(globs):
    "Something like https://stackoverflow.com/questions/4858100"
    for val in globs.values():
        if isinstance(val, _types.ModuleType):
            yield val


def sysinfo():
    """Display several system informations.

    Examples
    --------
    >>> import pylbmisc as lb
    >>> lb.utils.sysinfo()
    """
    parent_frame = _inspect.currentframe().f_back
    globs = parent_frame.f_globals
    _pp({
        "python-path": _sys.executable,
        "python-version": _sys.version,
        "imports": list(_unique(_imports(globs=globs))),
        "paths": _sys.path,
        "now": _dt.datetime.now().isoformat(),
    })


def timeit(n=1):
    """A timer decorator with parameter for number of execution

    Parameters
    ----------
    n: integer
       number of function execution (default=1)

    Examples
    --------
    >>> import pylbmisc as lb
    >>> import time
    >>> @timeit
    >>> def test():
    ...      time.sleep(2)
    >>>
    >>> test()
    >>>
    >>> @timeit(n=3)
    >>> def test2():
    ...      time.sleep(2)
    >>>
    >>> test2()
    """
    def inner(f):
        def wrapper(*args, **kwargs):
            start_time = _time.perf_counter()
            for i in range(n):
                rval = f(*args, **kwargs)
            stop_time = _time.perf_counter()
            elapsed = stop_time - start_time
            function_name = f.__name__
            msg_start = f"{n} calls of" if n > 1 else "Function"
            msg_end = f" (mean: {elapsed/n:.4f} secs)" if n > 1 else "."
            msg = f"{msg_start} {function_name} [{args=} {kwargs=}] " \
                f"took {elapsed:.2f} secs{msg_end}"
            print(msg)
            return rval
        return wrapper
    return inner


if __name__ == "__main__":
    import doctest
    doctest.testmod()
