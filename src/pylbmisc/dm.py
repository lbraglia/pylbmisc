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
def to_bool(x: _pd.Series):
    """Coerce to boolean a pd.Series using astype

    >>> to_bool(pd.Series([1,0,1,0]))
    >>> to_bool(pd.Series(["","yes","no","boh"]))
    """
    return x.astype("bool", copy=True)


def _replace_comma(x: _pd.Series):
    if _pd.api.types.is_string_dtype(x):
        return x.str.replace(",", ".")
    else:
        return x


def to_integer(x: _pd.Series):
    """Coerce a pd.Series to integer (if possible)

    >>> to_integer(pd.Series([1, 2, 3]))
    >>> to_integer(pd.Series([1., 2., 3., 4., 5., 6.]))
    >>> to_integer(pd.Series(["2001", "2011", "1999"]))
    >>> to_integer(pd.Series(["1.1", "2,1", "asd"]))
    """
    s = x.copy()
    s = _replace_comma(s)
    return _pd.to_numeric(s, errors='coerce', downcast='integer')


def to_numeric(x: _pd.Series):
    """Coerce a pd.Series using pd.to_numeric

    >>> to_integer(pd.Series([1, 2, 3]))
    >>> to_integer(pd.Series([1., 2., 3., 4., 5., 6.]))
    >>> to_integer(pd.Series(["2001", "2011", "1999"]))
    >>> to_integer(pd.Series(["1.1", "2,1", "asd"]))
    """
    s = x.copy()
    s = _replace_comma(s)
    return _pd.to_numeric(s, errors='coerce')


def to_datetime(x: _pd.Series):
    """Coerce to a datetime a pd.Series

    >>> to_datetime(pd.Series([str(dt.datetime.now())] * 6))
    """
    return _pd.to_datetime(x, errors='coerce')


def to_date(x: _pd.Series):
    """Coerce to a date a pd.Series

    >>> to_date(pd.Series([str(dt.datetime.now())] * 6))
    >>> to_date(pd.Series(["2020-01-02", "2021-01-01", "2022-01-02"] * 2))
    """
    return to_datetime(x).dt.floor("D")


def to_categorical(x: _pd.Series,
                   lowcase: bool = False,
                   categories: list[str] = None):
    """Coerce to categorical a pd.Series of strings, with blank values as missing

    >>> to_categorical(pd.Series([1, 2., 1., 2, 3]))
    >>> to_categorical(pd.Series(["AA", "sd", "asd", "aa", ""]))
    """
    # copy the series
    s = x.copy()
    # string preprocessing
    if _pd.api.types.is_string_dtype(s):
        # string: rm spaces
        s = s.str.strip()
        s[s == ""] = _pd.NA
        # string: lowercase
        if lowcase:
            s = s.str.lower()
            if categories != None:
                categories = [c.lower() for c in categories]
    # categorical making
    return _pd.Categorical(s, categories=categories)


def to_noyes(x: _pd.Series):
    """Coerce to no/yes a (string or numerical) pd.Series

    >>> to_noyes(pd.Series(["","yes","no","boh", "si"]))
    >>> to_noyes(pd.Series([0.,1.,2.,1.])) # using to_bool so if != 0 it's yes
    """
    s = x.copy()
    # string preprocessing
    if _pd.api.types.is_string_dtype(s):
        # take the first letter that can be n(o), s(i) or y(es)
        l0 = s.copy().str.strip().str.lower().str[0]
        l0[l0 == 's'] = 'y'
        l0 = l0.replace({"0": "n", "1": "y"}) # for strings 0/1
    else:
        l0 = to_bool(s).map({False: 'n', True: 'y'})
    return to_categorical(l0.map({"n": "no", "y": "yes"}),
                          categories = ['no', 'yes'])


def to_sex(x: _pd.Series):
    """Coerce to male/female a pd.Series of strings (Mm/Ff)

    >>> to_sex(pd.Series(["","m","f"," m", "Fm"]))
    """
    if _pd.api.types.is_string_dtype(x):
        s = x.copy()
        # take the first letter (Mm/Ff)
        l0 = s.str.strip().str.lower().str[0]
        return to_categorical(l0.map({"m": "male", "f": "female"}),
                              categories = ['male', 'female'])
    else:
        raise ValueError("x must be a pd.Series of strings")


def to_recist(x: _pd.Series):
    """Coerce to recist categories a pd.Series of strings

    >>> to_recist(pd.Series(["RC", "PD", "SD", "PR", "RP", "boh"]))
    """
    if _pd.api.types.is_string_dtype(x):
        s = x.copy()
        # rm spaces and uppercase and take the first two letters
        s = s.str.strip().str.upper().str[:2]
        # uniform italian to english
        ita2eng = {"RC": "CR", "RP": "PR"}
        s = s.replace(ita2eng)
        categs = ["CR", "PR", "SD", "PD"]
        return to_categorical(s, categories=categs)
    else:
        raise ValueError("x must be a pd.Series of strings")


def to_other_specify(x: _pd.Series):
    """Try to polish a bit a free-text variable and create a categorical one

    >>> x = pd.Series(["asd", "asd", "", "prova", "ciao", 3]+ ["bar"]*4)
    >>> to_other_specify(x)
    """
    s = x.copy().astype("str")
    s = s.str.strip().str.lower()
    s[s==""] = _pd.NA
    categs = list(s.value_counts().index) # categs ordered by decreasing counts
    return to_categorical(s, categories=categs)


def to_string(x: _pd.Series):
    """ Coerce the pd.Series passed to a string Series

    >>> x = pd.Series(["asd", "asd", "", "prova", "ciao", 3]+ ["bar"]*4)
    >>> to_string(x)
    """
    s = x.copy()
    return s.astype('string')


# --------------- coercion class ----------------------------------------
class Coercer:
    """Coercer of a pandas DataFrame.

    Given directives as a dict (variable name as key, function/coercer
    as value) it applies all the function on a copy of the DataFrame
    and return it.  If verbose print a report of the introduced
    missing values with the coercion for check

    >>> from pylbmisc.dm import *
    >>> import pandas as pd
    >>> import numpy as np
    >>>
    >>> df = pd.DataFrame({
    >>>     "idx" :  [1., 2., 3., 4., 5., 6.],
    >>>     "sex" :  ["m", "maschio", "f", "female", "m", "M"],
    >>>     "now":   [str(dt.datetime.now())] * 6,
    >>>     "date":  ["2020-01-02", "2021-01-01", "2022-01-02"] * 2,
    >>>     "state": ["Ohio", "Ohio", "Ohio", "Nevada", "Nevada", "Nevada"],
    >>>     "ohio" : [1, 1, 1, 0, 0, 0],
    >>>     "year":  [str(y) for y in [2000, 2001, 2002, 2001, 2002, 2003]],
    >>>     "pop":   [str(p) for p in [1.5, 1.7, 3.6, np.nan, 2.9, 3.2]],
    >>>     "recist" : ["", "pd", "sd", "pr", "rc", "cr"],
    >>>     "other" : ["b"]*3 + ["a"]*2 + ["c"]
    >>> })
    >>> 
    >>> directives = {
    >>>     "idx": to_integer,
    >>>     "sex": to_sex,
    >>>     "now": to_datetime,
    >>>     "date": to_date,
    >>>     "state": to_categorical,
    >>>     "ohio": to_noyes,
    >>>     "year": to_integer,
    >>>     "pop": to_numeric,
    >>>     "recist" : to_recist,
    >>>     "other" : to_other_specify
    >>> }
    >>> 
    >>> coercer = Coercer(df, directives)
    >>> coerced = coercer.coerce()
    """

    def __init__(
        self, df: _pd.DataFrame, directives: dict, verbose: bool = True
    ):
        self._df = df
        self._directives = directives
        self._verbose = verbose

    def coerce(self, keep_only_coerced = False) -> _pd.DataFrame:
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
        if keep_only_coerced:
            vars = list(directives.keys())
            df = df[vars]
        return df
