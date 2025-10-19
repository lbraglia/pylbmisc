""" Utilities coming from R."""

import itertools as _itertools
import inspect as _inspect
import numpy as _np
import pandas as _pd
import types as _types
import subprocess as _subprocess
import tempfile as _tempfile
from pprint import pformat as _pformat
import re as _re


def match_arg(arg, choices):
    """R's match.arg equivalent for programming function for interactive use

    Examples
    --------
    >>> from pylbmisc.r import match_arg
    >>> # questo ritorna errore perché matcha troppo
    >>> user_input = "foo"
    >>> # a = match_arg(user_input, ["foobar", "foos", "asdomar"]) # errore
    >>> # questo è ok e viene espanso
    >>> user_input2 = "foob"
    >>> a = match_arg(user_input2, ["foobar", "foos", "asdomar"])
    >>> print(a)
    foobar
    """
    res = [expanded for expanded in choices if expanded.startswith(arg)]
    choices_str = ", ".join(choices)
    res_len = len(res)
    if res_len == 0:
        msg = f"Parameter {arg} must be one of: {choices_str}"
        raise ValueError(msg)
    elif res_len > 1:
        msg = f"Parameter {arg} matches multiple choices from: {choices_str}"
        raise ValueError(msg)
    else:
        return res[0]


def expand_grid(dictionary):
    # https://stackoverflow.com/questions/12130883
    """Replacement for R's expand.grid

    Examples
    --------
    >>> import pylbmisc as lb
    >>> stratas =  {"centres": ["ausl re", "ausl mo"],
    ...             "agecl": ["<18", "18-65", ">65"],
    ...             "foo": ["1"]}
    >>> lb.r.expand_grid(stratas)
       centres  agecl foo
    0  ausl re    <18   1
    1  ausl re  18-65   1
    2  ausl re    >65   1
    3  ausl mo    <18   1
    4  ausl mo  18-65   1
    5  ausl mo    >65   1
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
    >>> import numpy as np
    >>> import pandas as pd
    >>> from pylbmisc.r import dput
    >>> import pylbmisc as lb
    >>> List = list(range(0, 15))
    >>> dput(List)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    >>> Dict = {"a": 1, "b": 2}
    >>> dput(Dict)
    {'a': 1, 'b': 2}
    >>> Dict2 = {"a": List, "b": List}
    >>> dput(Dict2)
    {'a': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
     'b': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]}
    >>> nparray = np.array(List)
    >>> dput(nparray)
    np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])
    >>> series = pd.Series(List)
    >>> dput(series)
    pd.Series([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14])
    >>> def function() -> None:
    ...     pass
    >>> dput(function)
    def function() -> None:
        pass
    <BLANKLINE>
    >>> df = lb.datasets.load()
    >>> dput(df)
    pd.DataFrame({'dead': [6, 13, 18, 28, 52, 53, 61, 60],
     'logdose': [1.691, 1.724, 1.755, 1.784, 1.811, 1.837, 1.861, 1.884],
     'n': [59, 60, 62, 56, 63, 59, 62, 60]})
    """
    if isinstance(x, _types.FunctionType):  # special cases: don't use repr
        print(_inspect.getsource(x))
    elif isinstance(x, _pd.DataFrame):
        dict_rep = _pformat(x.to_dict(orient="list"), compact=True)
        print(f"pd.DataFrame({dict_rep})")
    elif isinstance(x, _pd.Series):
        list_rep = _pformat(x.to_list(), compact=True)
        print(f"pd.Series({list_rep})")
    elif isinstance(x, _np.ndarray):
        list_rep = _pformat(x.tolist(), compact=True)
        print(f"np.array({list_rep})")
    else:
        obj_repr = _pformat(x, compact=True)
        print(obj_repr)


def table(x: _pd.Series | None = None,
          y: _pd.Series | None = None,
          **kwargs):
    """Emulate the good old table for quick crosstabs.

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


def debug(step_into_this):
    r"""Emulate R's debug function as a decorator

    Parameters
    ----------
    step_into_this: function
        the function to be breakpoint()-ed

    Examples
    --------
    >>> # comment the decorator when done with debugging
    >>> @debug
    >>> def myfunction(x, y=1):
    ...     m = 1
    ...     return x * y * m
    >>>
    >>> myfunction(5) # this call is breakpointed
    """
    def wrapper(*args, **kwargs):
        breakpoint()
        return step_into_this(*args, **kwargs)
    return wrapper


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


_comment_re = _re.compile("(#.+)")
_prompt_re = _re.compile("^(>{3} ?|\\.{3} ?)")


def example(f):
    """Extract example code to be executed

    Parameters
    ----------
    f: function
       function for doc's example

    Examples
    --------
    >>> import pylbmisc as lb
    >>> exec(lb.r.example(lb.stats.p_adjust))
    """
    doc = _inspect.getdoc(f)
    # select lines with >>> or ...
    code = [line for line in doc.split("\n")
            if line.startswith(">>>")
            or line.startswith("...")]
    print("\n".join(code))
    # rm from comments onward
    uncommented = [_comment_re.sub("", line) for line in code]
    # rm starting lines
    clean_code = [_prompt_re.sub("", line) for line in uncommented]
    to_be_run = [line for line in clean_code if line != ""]
    return "\n".join(to_be_run)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
