"""Data management utilities for pandas Series/DataFrame"""

import numpy as _np
import pandas as _pd


# decorators
def _verboser(f):
    def transformer(x: _pd.Series):
        coerced = f(x)
        report = _pd.DataFrame({"original": x, "coerced": coerced})
        # meh non son sicuro qua sotto
        new_na = _pd.isna(report).apply(sum, axis=1) == 1
        if _np.any(new_na):
            print("Coercion introduced missing values:")
            print(report[new_na])
        return coerced

    return transformer


# --------------- coercion workers ----------------------------------------
def to_integer(x: _pd.Series):
    """Coerce to integer a pd.Series (if possible)"""
    return _pd.to_numeric(x, errors='coerce', downcast='integer')


def to_numeric(x: _pd.Series):
    """Coerce to float a pd.Series"""
    return _pd.to_numeric(x, errors='coerce')


def to_datetime(x: _pd.Series):
    """Coerce to a datetime a pd.Series"""
    return _pd.to_datetime(x, errors='coerce')


# --------------- coercion class ----------------------------------------
class Coercer:
    """Coercer of a pandas DataFrame.

    Given directives as a dict (variable name as key, function/coercer
    as value) it applies all the function on a copy of the DataFrame
    and return it.  If verbose print a report of the introduced
    missing values with the coercion for check

    >>> import pylbmisc as lb
    >>> import pandas as pd

    >>> df = pd.DataFrame({"a": ["1.1", "2,1", "asd"]})
    >>> directives = {"a": lb.dm.to_integer}
    >>> coercer = lb.dm.Coercer(df, directives)
    >>> coerced = coercer.coerce()
    """

    def __init__(
        self, df: _pd.DataFrame, directives: dict, verbose: bool = True
    ):
        self._df = df
        self._directives = directives
        self._verbose = verbose

    def coerce(self) -> _pd.DataFrame:
        # do not modify the input data
        df = self._df.copy()
        directives = self._directives
        verbose = self._verbose
        # make verbose all the functions by decorating them
        if verbose:
            for var in directives.keys():
                directives[var] = _verboser(directives[var])
        # apply the coercers
        for var, fun in directives.items():
            if verbose:
                print("Processing {}.".format(var))
            df[var] = fun(df[var])
        # return results
        return df
