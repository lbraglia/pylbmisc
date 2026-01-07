"""Data management utilities for pandas Series/DataFrame"""

import functools as _functools
import inspect as _inspect
import numpy as _np
import pandas as _pd
import pyarrow as _pa
import re as _re
import string as _string
import datetime as _dt

from collections import Counter as _Counter
from functools import singledispatch as _singledispatch
from pathlib import Path as _Path
from pprint import pprint as _pprint


_default_dtype_backend = "pyarrow"

# -------------------------------------------------------------------------
# regular expressions used
# -------------------------------------------------------------------------

# Searching by regex in data
# https://stackoverflow.com/questions/51170763 for general setup
# Mail: https://stackoverflow.com/questions/8022530/ for mail regex
_mail_re = _re.compile(r"[^@]+@[^@]+\.[^@]+")
_fc_re = _re.compile(
    r"[A-Za-z]{6}[0-9]{2}[A-Za-z]{1}[0-9]{2}[A-Za-z]{1}[0-9]{3}[A-Za-z]{1}"
)
_tel_re = _re.compile(r"(.+)?0[0-9]{1,3}[\. /\-]?[0-9]{6,7}")
_mobile_re = _re.compile(r"(.+)?3[0-9]{2}[\. /\-]?[0-9]{6,7}")


_is_mobile_number = _np.vectorize(lambda x: bool(_mobile_re.match(x)))
_is_telephone_number = _np.vectorize(lambda x: bool(_tel_re.match(x)))
_is_email = _np.vectorize(lambda x: bool(_mail_re.match(x)))
_is_fiscal_code = _np.vectorize(lambda x: bool(_fc_re.match(x)))

# cleaning string that have to contain dates
_dates_polish = _re.compile(r"[^/\d-]") # keep only numbers, - and /, and just hope for the best



# -------------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------------
def table2df(df: _pd.DataFrame) -> _pd.DataFrame:
    """Transform a pd.DataFrame representing a two-way table (es
    crosstable, correlation matrix, p.val matrix) in a
    pd.DataFrame with long format.

    Parameters
    ----------
    df:
       the crosstabulation to be put in long form

    Examples
    --------
    >>> import pandas as pd
    >>> a = pd.Series(["foo", "foo", "foo", "foo", "bar", "bar",
    ...                "bar", "bar", "foo", "foo", "foo"], dtype=object)
    >>> b = pd.Series(["one", "one", "one", "two", "one", "one",
    ...                "one", "two", "two", "two", "one"], dtype=object)
    >>> pd.crosstab(a, b)
    col_0  one  two
    row_0
    bar      3    1
    foo      4    3
    >>> tab = pd.crosstab(a,b)
    >>> table2df(tab)
      row_0 col_0  x
    0   bar   one  3
    1   bar   two  1
    2   foo   one  4
    3   foo   two  3
    """
    if not isinstance(df, _pd.DataFrame):
        msg = "Only dataframes are processed."
        raise Exception(msg)
    x = df.copy()
    x = x.stack().reset_index()
    return x.rename(columns={0: "x"})


def dump_unique_values(dfs: _pd.DataFrame | dict[str, _pd.DataFrame],
                       fpath: str | _Path = "data/uniq.txt"):
    """Save unique value of a (dict of) dataframe for inspection and monitor
    during time.

    Parameters
    ----------
    dfs:
        dataframe or dict of dataframes to be dumped
    fpath:
        path where to save the unique values
    """
    if not isinstance(dfs, (_pd.DataFrame, dict)):
        msg = "x deve essere un pd.DataFrame o un dict di pd.DataFrame"
        raise ValueError(msg)
    # normalize single dataframe
    if isinstance(dfs, _pd.DataFrame):
        dfs = {"df": dfs}
        # output
    outfile = _Path(fpath)
    with outfile.open("w") as f:
        for df_lab, df in dfs.items():
            for col in df:
                # Header
                print(f"DataFrame: '{df_lab}', "
                      f"Column: '{col}', "
                      f"Dtype: {df[col].dtype}, "
                      f"Unique values:",
                      file=f)
                # Dati: non sortati perché ci sono problemi se i dati sono metà
                # numerici e meta stringa? bah ci riprovo
                if is_string(df[col]):
                    _pprint(df[col].value_counts().index.to_list(),
                            stream=f,
                            compact=True)
                else:
                    _pprint(df[col].sort_values().unique().tolist(),
                            stream=f,
                            compact=True)
                print(file=f)
            print("-"*80 + "\n\n", file=f)


def names_list(dfs):
    """Dump names to stdout to ease code creation for Coercer

    Parameters
    ----------
    dfs:
        dataframe or dict of dataframes to be dumped
    """
    if isinstance(dfs, dict):
        for k, df in dfs.items():
            print(k, "\n")
            _pprint(df.columns.to_list())
    elif isinstance(dfs, _pd.DataFrame):
        _pprint(dfs.columns.to_list())
    else:
        msg = "Not handled data (only dataframe or dicts of dataframes)"
        raise Exception(msg)


def qcut(x, q, **kwargs) -> _pd.Categorical:
    """An alternative to pd.qcut

    This function produces categorization based on quantiles but without the
    index produced by pd.qcut that can give issues in some routines not

    Parameters
    ----------
    x: 1d ndarray or Series
        as in pd.qcut
    q: int or list-like of float
        as in pd.qcut
    kwargs:
        other parameter passed to pd.qcut (all but labels!)
    """
    full = _pd.qcut(x, q, **kwargs)
    categories = full.cat.categories.astype(str).to_list()
    raw = _pd.qcut(x, q, labels=False, **kwargs)
    recode = {prog: lab for prog, lab in enumerate(categories)}
    mapped = raw.map(recode)
    return to_categorical(mapped, levels=categories)


# -------------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------------

def is_all_missing(x: _pd.Series) -> bool:
    """Check if all the Series is composed of missing values

    Check if all the Series is composed of missing values

    Parameters
    ----------
    x:
        the Series to be checked
    """
    return x.isna().all()


def is_string(x: _pd.Series) -> bool:
    """Check the type of a Series to be composed of string.

    It checks Series (including data with np.nan) differently from
    pandas.api.types.is_string_dtype

    Parameters
    ----------
    x:
        the Series to be checked

    Examples
    --------
    >>> import pandas as pd
    >>> x = pd.Series(["a", pd.NA])
    >>> pd.api.types.is_string_dtype(x)
    False
    >>> is_string(x)
    True
    """
    return x.dtype in ["O", "string[pyarrow]"]


def is_bool(x: _pd.Series) -> bool:
    """Check the type of a Series to be composed of boolean.

    Parameters
    ----------
    x:
        the Series to be checked
    """
    return _pd.api.types.is_bool_dtype(x)


def is_integer(x: _pd.Series) -> bool:
    """Check the type of a Series to be composed of integers.

    Parameters
    ----------
    x:
        the Series to be checked
    """
    return _pd.api.types.is_integer_dtype(x)


def is_numeric(x: _pd.Series) -> bool:
    """Check the type of a Series to be composed of numerics.

    Parameters
    ----------
    x:
        the Series to be checked
    """
    return _pd.api.types.is_numeric_dtype(x)


def is_categorical(x: _pd.Series) -> bool:
    """Check the type of a Series to be composed of string.

    It checks Series (including data with np.nan) differently from
    pandas.api.types.is_string_dtype

    Parameters
    ----------
    x:
        the Series to be checked
    """
    return _pd.api.types.is_categorical_dtype(x)


def is_datetime(x: _pd.Series) -> bool:
    """Check the type of a Series to be composed of datetimes.

    Parameters
    ----------
    x:
        the Series to be checked
    """
    return _pd.api.types.is_datetime64_any_dtype(x)


def is_date(x: _pd.Series) -> bool:
    """Check the type of a Series to be composed of dates.

    Parameters
    ----------
    x:
        the Series to be checked
    """
    # If it's not a datetime it can't be a date
    if not is_datetime(x):
        return False

    # otherwise check if all the times are zero; fix na for the sake of god:
    # don't put in all the comparison based on NA
    zero_time = (x.dt.time == _dt.time(0, 0))
    zero_time = zero_time[~ x.isna()]
    return zero_time.all()





# -------------------------------------------------------------------------
# pii_erase
# ------------------------------------------------------------------------
# Searching by column name
def _columns_match(df_columns, searched):
    """Search in columns names, both exact match and contains match"""
    # coerce single string to list of one string
    if isinstance(searched, str):
        searched = [searched]
    perfect_match = [c in set(searched) for c in df_columns]
    return perfect_match



def _has_emails(x: _pd.Series) -> bool:
    """ Check if a Series has e-mail address

    Parameters
    ----------
    x:
        the Series to be checked

    """
    if is_string(x):
        check = _is_email(x)
        return bool(_np.any(check))
    else:
        return False



def _has_fiscal_codes(x: _pd.Series) -> bool:
    """Check if a Series has fiscal codes

    Parameters
    ----------
    x:
        the Series to be checked
    """
    if is_string(x):
        check = _is_fiscal_code(x)
        return bool(_np.any(check))
    else:
        return False



def _has_telephone_numbers(x: _pd.Series) -> bool:
    """Check if a Series has telephone numbers

    Parameters
    ----------
    x:
        the Series to be checked

    """
    if is_string(x):
        check = _is_telephone_number(x)
        return bool(_np.any(check))
    else:
        return False



def _has_mobile_numbers(x: _pd.Series) -> bool:
    """Check if a Series has mobile numbers

    Parameters
    ----------
    x:
        the Series to be checked
    """
    if is_string(x):
        check = _is_mobile_number(x)
        return bool(_np.any(check))
    else:
        return False


def pii_find(x: _pd.DataFrame) -> list[str]:
    """Find columns with probable piis (Personally Identifiable
    Informations) and return the colnames for further processing.

    Parameters
    ----------
    x:
        The DataFrame to check

    Returns
    -------
    A Python list of variable names with probable PII

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     "id" : [1,2,3],
    ...     "cognome": ["brazorv", "gigetti", "ginetti"],
    ...     "nome  " : [1,2,3],
    ...     "mail": ["lgasd@asdkj.com", " asòdlk@asd.com", "aaaa"],
    ...     "fc": ["nrgasd12h05h987z", "aaaa", "eee"],
    ...     "num": ["0654-6540123", "aa", "eee"],
    ...     "cel": ["3921231231", "aa", "eee"]
    ...     })
    >>>
    >>> probable_piis = pii_find(df)
    'cognome' matches 'surname'/'cognome'.
    'nome  ' matches 'name'/'nome'.
    mail probably contains emails.
    fc probably contains fiscal codes.
    num probably contains telephone numbers.
    cel probably contains mobile phones numbers.
    >>> probable_piis
    ['cognome', 'nome  ', 'mail', 'fc', 'num', 'cel']
    >>> if probable_piis:
    ...     df.drop(columns=probable_piis)
    ...
       id
    0   1
    1   2
    2   3
    """

    if not isinstance(x, _pd.DataFrame):
        msg = "x must be a pd.DataFrame"
        raise ValueError(msg)

    col = list(x.columns.values)

    # name and surname (looking at columns names)
    col_clean = [c.lower().strip() for c in col]
    surname_match = _columns_match(col_clean, ["cognome", "surname"])
    name_match = _columns_match(col_clean, ["nome", "name"])

    # finding other pii loking at data
    has_mails = [_has_emails(x[c]) for c in col]
    has_fcs = [_has_fiscal_codes(x[c]) for c in col]
    has_telephones = [_has_telephone_numbers(x[c]) for c in col]
    has_mobiles = [_has_mobile_numbers(x[c]) for c in col]

    probable_pii = []
    zipped = zip(
        col,
        surname_match,
        name_match,
        has_mails,
        has_fcs,
        has_telephones,
        has_mobiles,
    )
    for (
        var,
        is_surname,
        is_name,
        has_mail,
        has_fc,
        has_telephone,
        has_mobile,
    ) in zipped:
        pii_sum = (
            is_surname
            + is_name
            + has_mail
            + has_fc
            + has_telephone
            + has_mobile
        )
        if pii_sum:
            probable_pii.append(var)
            if is_surname:
                print(f"'{var}' matches 'surname'/'cognome'.")
            if is_name:
                print(f"'{var}' matches 'name'/'nome'.")
            if has_mail:
                print(f"{var} probably contains emails.")
            if has_fc:
                print(f"{var} probably contains fiscal codes.")
            if has_telephone:
                print(f"{var} probably contains telephone numbers.")
            if has_mobile:
                print(f"{var} probably contains mobile phones numbers.")
    return probable_pii


# -------------------------------------------------------------------------
# preprocessing varnames (from shitty excel): fix_columns
# -------------------------------------------------------------------------


def _compose(f, g):
    return lambda x: f(g(x))


def _replace_unwanted_chars(s):
    keep = _string.ascii_lowercase + _string.digits
    for ch in s:
        if ch not in keep:
            s = s.replace(ch, "_")
    return s


def _replace_accents(s):
    tmp = _re.sub("à", "a", s)
    tmp = _re.sub("è", "e", tmp)
    tmp = _re.sub("é", "e", tmp)
    tmp = _re.sub("ì", "i", tmp)
    tmp = _re.sub("ù", "u", tmp)
    return tmp


def _remove_duplicated_underscore(s):
    return _re.sub("_+", "_", s)


def _remove_external_underscore(s):
    return _re.sub("^_", "", _re.sub("_$", "", s))


def _add_x_if_first_is_digit(s):
    if s.startswith(tuple(_string.digits)):
        return "x" + s
    else:
        return s


def _fix_varnames_worker(vnames: list[str],
                         make_unique: bool) -> list[str]:
    funcs = [
        lambda s: str(s),
        lambda s: s.lower().strip(),
        lambda s: _replace_accents(s),
        lambda s: _replace_unwanted_chars(s),
        lambda s: _remove_duplicated_underscore(s),
        lambda s: _remove_external_underscore(s),
        lambda s: _add_x_if_first_is_digit(s),
    ]
    # sotto serve dato che compose applica prima la funzione a destra
    # e poi quella a sx (come in math) mentre vogliamo tenere l'ordine
    # di sopra
    funcs.reverse()
    worker = _functools.reduce(_compose, funcs)
    mod = [worker(s) for s in vnames]
    # handle duplicated names by adding numeric postfix
    has_duplicates = len(mod) != len(set(mod))
    if has_duplicates and make_unique:
        seen = {}
        uniq = []
        for v in mod:
            if v not in seen:
                seen[v] = 0
                uniq.append(v)
            else:
                seen[v] += 1
                uniq.append(f"{v}_{seen[v]}")
    else:
        uniq = mod
    # se ci sono doppi nei nomi di partenza meglio evitare i dict se no i
    # doppi vengono considerati solo una volta
    # rename_dict = {}
    # for o, m in zip(original, uniq_mod):
    #     rename_dict.update({o: m})
    # if it was a string that was passed, return a string, not a list
    return uniq


def fix_varnames(x: str | list[str] | _pd.Series | _pd.DataFrame | dict[str, _pd.DataFrame],
                 return_tfd: bool = False,
                 make_unique: bool = True,
                 ):
    """The good-old R preprocess_varnames, working with strings,
    lists, pd.DataFrame or dicts of pd.DataFrames.

    Parameters
    ----------
    x:
        string, list of strigs/varnames, series, dataframe or dict of dataframes
    return_tfd:
        bool, return a dict of to/from descriptions
    make_unique:
        bool, assure returned varnames are unique by adding a progressive number as postfix

    Examples
    --------
    >>> fix_varnames("  asd 98n2 3")
    'asd_98n2_3'
    >>> fix_varnames([" 98n2 3", " L< KIAFJ8 0_________"])
    ['x98n2_3', 'l_kiafj8_0']
    >>> fix_varnames(["àsd", "foo0", "asd"])
    ['asd', 'foo0', 'asd_1']

    """

    if isinstance(x, str):
        x = [x]

    if isinstance(x, list):
        from_name = x
        to_name = _fix_varnames_worker(from_name, make_unique=make_unique)
        to_name = to_name if len(to_name) > 1 else to_name[0]
        if return_tfd:
            tf = {t: f for t, f in zip(to_name, from_name)}
            return to_name, tf
        else:
            return to_name
    elif isinstance(x, _pd.Series):
        from_name = x.to_list()
        to_name = _fix_varnames_worker(from_name, make_unique=make_unique)
        rval = _pd.Series(to_name, index=x.index).astype(_pd.ArrowDtype(_pa.string()))
        if return_tfd:
            tf = {t: f for t, f in zip(to_name, from_name)}
            return rval, tf
        else:
            return rval
    elif isinstance(x, _pd.DataFrame):
        from_name = list(x.columns.values)
        to_name = _fix_varnames_worker(from_name, make_unique=make_unique)
        df = x.copy()
        df.columns = to_name
        if return_tfd:
            tf = {t: f for t, f in zip(to_name, from_name)}
            return df, tf
        else:
            return df
    elif isinstance(x, dict):
        dfs = {}
        tfs = {}
        for k, v in x.items():
            from_name = list(v.columns.values)
            to_name = _fix_varnames_worker(from_name, make_unique=make_unique)
            df = v.copy()
            df.columns = to_name
            tf = {t: f for t, f in zip(to_name, from_name)}
            dfs[k] = df
            tfs[k] = tf
        if return_tfd:
            return dfs, tfs
        else:
            return dfs
    else:
        msg = "Only str and list are allowed, see sanitize_varnames for DataFrame or dict of DataFrames."
        raise ValueError(msg)




# -------------------------------------------------------------------------
# Coercion stuff below
# -------------------------------------------------------------------------
# decorators
def _verboser(f):
    def transformer(x: _pd.Series):
        coerced = f(x)
        report = _pd.DataFrame({"original": x, "coerced": coerced})
        new_na = (~_pd.isna(x)) & (_pd.isna(coerced))
        if _np.any(new_na):
            print("Please check if the following coercions are ok:")
            print(report[new_na])
        return coerced
    return transformer


# --------------- coercion workers ----------------------------------------

def identity(x):
    """The identity function to coerce nothing

    Parameters
    ----------
    x: Any
      any data

    Returns
    -------
    the object x unchanged
    """
    return x


def to_bool(x=None) -> _pd.Series:
    """Coerce to a boolean pd.Series

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced

    Examples
    --------
    >>> import pandas as pd
    >>> to_bool([1,0,1,0])
    0     True
    1    False
    2     True
    3    False
    dtype: bool[pyarrow]
    >>> to_bool(pd.Series([1,0.,1,0.]))
    0     True
    1    False
    2     True
    3    False
    dtype: bool[pyarrow]
    >>> to_bool([1,0,1,0, pd.NA])
    0     True
    1    False
    2     True
    3    False
    4     <NA>
    dtype: bool[pyarrow]
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)
    nas = _pd.isna(x)
    rval = x.astype("boolean[pyarrow]" if _default_dtype_backend == "pyarrow" else "boolean")
    rval[nas] = _pd.NA
    return rval


def _replace_comma(x: _pd.Series):
    if is_string(x):
        # nas = x.isin(["", _pd.NA, _np.nan])
        nas = (x.isna()) | (x == "")
        rval = x.astype("str").str.replace(",", ".")
        rval[nas] = _pd.NA
        return rval
    else:
        return x


# actually to_integer is used only by tteep to ensure, otherwise to_numeric
# with pyarrow backend should handle both integers and floats gracefully and
# there's no need for another function
def to_integer(x=None) -> _pd.Series:
    """Coerce a pd.Series to integer (if possible)

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced

    Examples
    --------
    >>> import numpy as np
    >>> to_integer([1., 2., 3., 4., 5., 6., np.nan])
    0       1
    1       2
    2       3
    3       4
    4       5
    5       6
    6    <NA>
    dtype: Int64
    >>> to_integer(["2001", "2011", "1999", ""])
    0    2001
    1    2011
    2    1999
    3    <NA>
    dtype: Int64
    >>> # to_integer(["1.1", "1,99999", "foobar"]) # fails because of 1.99
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)
    s = _replace_comma(x)
    # return _np.floor(_pd.to_numeric(s, errors='coerce')).astype('Int64')
    # mi fido piu di quella di sotto anche se fallisce con i numeri con virgola
    # (che ci può stare, per i quale bisogna usare np.floor)
    return _pd.to_numeric(
        s,
        # dtype_backend = _default_dtype_backend,
        errors="coerce").astype(
            "Int64"
            # "int64[pyarrow]" if _default_dtype_backend == 'pyarrow' else "Int64"
            # _pd.ArrowDtype(_pa.int64()) if _default_dtype_backend == 'pyarrow' else "Int64"
        )


def to_numeric(x=None) -> _pd.Series:
    """Coerce a pd.Series using pd.to_numeric

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced

    Examples
    --------
    >>> to_numeric([1, 2, 3])
    0    1
    1    2
    2    3
    dtype: int64[pyarrow]
    >>> to_numeric([1., 2., 3., 4., 5., 6.])
    0    1.0
    1    2.0
    2    3.0
    3    4.0
    4    5.0
    5    6.0
    dtype: double[pyarrow]
    >>> to_numeric(["2001", "2011", "1999"])
    0    2001
    1    2011
    2    1999
    dtype: int64[pyarrow]
    >>> to_numeric(["1.1", "2,1", "asd", ""])
    0     1.1
    1     2.1
    2    <NA>
    3    <NA>
    dtype: double[pyarrow]
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)
    s = _replace_comma(x)
    return _pd.to_numeric(s, errors="coerce",
                          dtype_backend=_default_dtype_backend)


def to_datetime(x=None, *args, **kwargs) -> _pd.Series:
    """Coerce to a datetime a pd.Series

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced
    args:
        other arguments passed to pd.to_datetime
    kwargs:
        other arguments passed to pd.to_datetime
    
    Examples
    --------
    >>> to_datetime(['2025-03-01 10:02:22.756611'] * 2)
    0   2025-03-01 10:02:22.756611
    1   2025-03-01 10:02:22.756611
    dtype: datetime64[ns]
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)
    return _pd.to_datetime(x, errors="coerce", *args, **kwargs)


def to_date(x=None, *args, **kwargs) -> _pd.Series:
    """Coerce to a date a pd.Series

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced
    args:
        other arguments passed to pd.to_datetime
    kwargs:
        other arguments passed to pd.to_datetime

    Examples
    --------
    >>> to_date(["2020-01-02", "2021-01-01", "2022-01-02"] * 2)
    0   2020-01-02
    1   2021-01-01
    2   2022-01-02
    3   2020-01-02
    4   2021-01-01
    5   2022-01-02
    dtype: datetime64[ns]
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)
    return to_datetime(x, *args, **kwargs).dt.floor("D")


def _extract_dates_worker(x):
    if isinstance(x, str): # handle missing values (sono float)
        polished = _dates_polish.sub("", x)
        return _pd.to_datetime(polished)
    else:
        # return _np.nan
        return _pd.NA


def extract_dates(x=None) -> _pd.Series:
    """Try to extract dates from shitty strings and convert them to proper

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced

    Examples
    --------
    >>> extract_dates(["2020-01-02", "01/01/1956", "asdasd 12-01-02"] * 2)
    0   2020-01-02
    1   1956-01-01
    2   2002-12-01
    3   2020-01-02
    4   1956-01-01
    5   2002-12-01
    dtype: datetime64[ns]
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)
    return x.apply(_extract_dates_worker)


def to_categorical(x=None,
                   levels=None,
                   labels=None,
                   ordered: bool = False) -> _pd.Categorical:
    """Coerce to categorical a pd.Series with R's factor API

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced
    levels: list
        labels to be considered as valid groups, if missing modalities by
        decreasing frequencies will be considered
    labels: list
        labels to be applied to the levels (if missing, will be replaced by
        levels)
    ordered: bool
        make an ordered categorical?

    Examples
    --------
    >>> import numpy as np
    >>> to_categorical([1, 2, 1, 2, 3, np.nan])
    [1.0, 2.0, 1.0, 2.0, 3.0, NaN]
    Categories (3, float64): [1.0, 2.0, 3.0]
    >>> to_categorical(["AA", "BB", "asd", "aa", "", np.nan],
    ...                levels=["AA", "BB"])
    ['AA', 'BB', NaN, NaN, NaN, NaN]
    Categories (2, object): ['AA', 'BB']
    >>> to_categorical(["AA", "BB", "asd", "aa", "", np.nan],
    ...                levels=["AA", "BB"], labels = ["x", "y"])
    ['x', 'y', NaN, NaN, NaN, NaN]
    Categories (2, object): ['x', 'y']
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)
    if levels is None:
        # take levels as from frequencies
        levels = x.value_counts(sort=True, ascending=False).index.to_list()
    if labels is None:
        labels = levels

    if len(levels) != len(labels):
        raise ValueError("levels and labels must have the "
                         "same number of elements")

    levlabs_mapping = {lev: lab for lev, lab in zip(levels, labels)}
    recoded = x.map(levlabs_mapping)
    # ensure labels are unique, https://stackoverflow.com/questions/480214
    unique_labels = list(dict.fromkeys(labels))
    return _pd.Categorical(recoded, categories=unique_labels, ordered=ordered)


def mc(levels=None,
       labels=None,
       ordered: bool = False):
    """Function factory to make categorical variables

    Parameters
    ----------
    levels:
        levels as in to_categorical
    labels:
        labels as in to_categorical
    ordered: bool
        labels as in to_categorical

    Returns
    -------
    a function which coerce to a categorical with specified categories/ordered

    Examples
    --------
    >>> import pylbmisc as lb
    >>> scuola = lb.dm.mc(['Scuola Media Inferiore', 'Scuola Media Superiore',
    ...                    'Laurea', 'Altro'])
    >>> coercer = {
    ...    scuola: ["titolo_istruzione"],
    ... }
    >>>
    """
    def f(x):
        return to_categorical(x=x,
                              levels=levels,
                              labels=labels,
                              ordered=ordered)
    return f


def to_noyes(x=None) -> _pd.Categorical:
    """Coerce to no/yes a string pd.Series

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced

    Examples
    --------
    >>> import numpy as np
    >>> to_noyes(["","yes","no","boh", "si", np.nan])
    [NaN, 'yes', 'no', NaN, 'yes', NaN]
    Categories (2, object): ['no', 'yes']
    >>> to_noyes([1,0,0, np.nan])
    ['yes', 'no', 'no', NaN]
    Categories (2, object): ['no', 'yes']
    >>> to_noyes([1.,0.,0., np.nan])
    ['yes', 'no', 'no', NaN]
    Categories (2, object): ['no', 'yes']
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)
    if is_string(x):
        # take only the first character and map to n/y
        tmp = x.str.strip().str.lower().str[0]
        tmp[tmp == "s"] = "y"
        tmp = tmp.replace({"0": "n", "1": "y"})  # 0/1 for strings
    else:
        # try to convert to boolean and map to n/y
        tmp = to_bool(x).map({False: "n", True: "y"})

    return to_categorical(tmp.map({"n": "no", "y": "yes"}),
                          levels=["no", "yes"])


def to_sex(x=None) -> _pd.Categorical:
    """Coerce to male/female a pd.Series of strings (Mm/Ff)

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced

    Examples
    --------
    >>> import numpy as np
    >>> to_sex(["","m","f"," m", "Fm", np.nan])
    [NaN, 'male', 'female', 'male', 'female', NaN]
    Categories (2, object): ['male', 'female']
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)
    if not is_string(x):
        msg = "to_sex only for strings vectors"
        raise Exception(msg)

    # take the first letter (Mm/Ff)
    tmp = x.str.strip().str.lower().str[0]
    tmp = tmp.map({"m": "male", "f": "female"})
    return to_categorical(tmp, levels=["male", "female"])


def to_recist(x=None) -> _pd.Categorical:
    """Coerce to recist categories a pd.Series of strings

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced

    Examples
    --------
    >>> import numpy as np
    >>> to_recist(["RC", "PD", "SD", "PR", "RP", "boh", np.nan])
    ['CR', 'PD', 'SD', 'PR', 'PR', NaN, NaN]
    Categories (4, object): ['CR', 'PR', 'SD', 'PD']
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)
    if not is_string(x):
        msg = "to_recist only for strings vectors"
        raise Exception(msg)

    # rm spaces and uppercase and take the first two letters
    tmp = x.str.strip().str.upper().str[:2]
    # uniform italian to english
    ita2eng = {"RC": "CR", "RP": "PR"}
    return to_categorical(tmp.replace(ita2eng),
                          levels=["CR", "PR", "SD", "PD"])


def to_other_specify(x=None) -> _pd.Categorical:
    """Try to polish a bit a free-text variable and create a categorical one

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced

    Examples
    --------
    >>> to_other_specify(["asd", "asd", "", "prova", "ciao", 3]+ ["bar"]*4)
    ['asd', 'asd', NaN, 'prova', 'ciao', '3', 'bar', 'bar', 'bar', 'bar']
    Categories (5, object): ['bar', 'asd', 'prova', 'ciao', '3']
    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)

    nas = (x.isna()) | (x == "")
    tmp = x.copy().astype("str").str.strip().str.lower()
    tmp[nas] = _pd.NA
    # categs ordered by decreasing counts
    categs = list(tmp.value_counts().index)
    return to_categorical(tmp, levels=categs)


def to_string(x=None) -> _pd.Series:
    """Coerce the pd.Series passed to a string Series

    Parameters
    ----------
    x: Series or something coercible to
        data to be coerced

    Examples
    --------
    >>> to_string([1,2,3])
    0    1
    1    2
    2    3
    dtype: object

    """
    if x is None:
        msg = "x must be a Series or something coercible to, not None."
        raise ValueError(msg)
    if not isinstance(x, _pd.Series):
        x = _pd.Series(x)

    nas = x.isna()
    rval = x.astype(_pd.ArrowDtype(_pa.string()))
    rval[nas] = _pd.NA
    return rval


# --------------- coercion class ----------------------------------------
class Coercer:
    """Coercer of a pandas DataFrame.

    Given directives as a dict (variable name as key, function/coercer
    as value) it applies all the function on a copy of the DataFrame
    and return it.  If verbose print a report of the introduced
    missing values with the coercion for check

    Parameters
    ----------
    df:
        The DataFrame to be coerced
    fv:
        function-variable dict: key can be a function or a string containing
        name of the function, variables is a list of strings with name
        of variables to apply the function to
    verbose:
        be verbose about operations applied

    Examples
    --------
    >>> import pylbmisc as lb
    >>> import pandas as pd
    >>> import numpy as np
    >>>
    >>> # ------------------------------------------------
    >>> # Function as key
    >>> # ------------------------------------------------
    >>> raw = pd.DataFrame({
    ...     "idx" :  [1., 2., 3., 4., 5., 6., "2,0", "", np.nan],
    ...     "sex" :  ["m", "maschio", "f", "female", "m", "M", "", "a", np.nan],
    ...     "date":  ["2020-01-02", "2021-01-01", "2022-01-02"] * 2  + [np.nan, "", "a"],
    ...     "state": ["Ohio", "Ohio", "Ohio", "Nevada", "Nevada", "Nevada"] + [np.nan, "", "a"],
    ...     "ohio" : [1, 1, 1, 0, 0, 0] + [np.nan] * 3 ,
    ...     "year":  [str(y) for y in [2000, 2001, 2002, 2001, 2002, 2003]] + [np.nan, "", "a"],
    ...     "pop":   [str(p) for p in [1.5, 1.7, 3.6, np.nan, 2.9]]  + ["3,2", np.nan, "", "a"],
    ...     "recist" : ["", "pd", "sd", "pr", "rc", "cr"] + [np.nan, "", "a"],
    ...     "other" : ["b"]*3 + ["a"]*2 + ["c"] + [np.nan, "", "a"]
    ... })
    >>> directives = {
    ...     lb.dm.to_integer: ["idx", "year"],
    ...     lb.dm.to_sex : ["sex"],
    ...     lb.dm.to_date: ["date"],
    ...     lb.dm.to_categorical: ["state"],
    ...     lb.dm.to_bool: ["ohio"],
    ...     lb.dm.to_numeric: ["pop"],
    ...     lb.dm.to_recist: ["recist"],
    ...     lb.dm.to_other_specify: ["other"]
    ... }
    >>>
    >>> cleaned1 = lb.dm.Coercer(raw, fv = directives, verbose = False).coerce()
    >>> raw
       idx      sex        date   state  ohio  year  pop recist other
    0  1.0        m  2020-01-02    Ohio   1.0  2000  1.5            b
    1  2.0  maschio  2021-01-01    Ohio   1.0  2001  1.7     pd     b
    2  3.0        f  2022-01-02    Ohio   1.0  2002  3.6     sd     b
    3  4.0   female  2020-01-02  Nevada   0.0  2001  nan     pr     a
    4  5.0        m  2021-01-01  Nevada   0.0  2002  2.9     rc     a
    5  6.0        M  2022-01-02  Nevada   0.0  2003  3,2     cr     c
    6  2,0                  NaN     NaN   NaN   NaN  NaN    NaN   NaN
    7             a                       NaN
    8  NaN      NaN           a       a   NaN     a    a      a     a
    >>> cleaned1
        idx     sex       date   state   ohio  year   pop recist other
    0     1    male 2020-01-02    Ohio   True  2000   1.5    NaN     b
    1     2    male 2021-01-01    Ohio   True  2001   1.7     PD     b
    2     3  female 2022-01-02    Ohio   True  2002   3.6     SD     b
    3     4  female 2020-01-02  Nevada  False  2001  <NA>     PR     a
    4     5    male 2021-01-01  Nevada  False  2002   2.9     CR     a
    5     6    male 2022-01-02  Nevada  False  2003   3.2     CR     c
    6     2     NaN        NaT     NaN   <NA>  <NA>  <NA>    NaN   NaN
    7  <NA>     NaN        NaT     NaN   <NA>  <NA>  <NA>    NaN   NaN
    8  <NA>     NaN        NaT       a   <NA>  <NA>  <NA>    NaN     a
    >>>
    >>> # ------------------------------------------------
    >>> # It's possilbe to specify string as key as well
    >>> # ------------------------------------------------
    >>>
    >>> directives2 = {
    ...     "lb.dm.to_categorical": ["state"],
    ...     "lb.dm.to_date": ["date"],
    ...     "lb.dm.to_integer": ["idx", "year"],
    ...     "lb.dm.to_noyes": ["ohio"],
    ...     "lb.dm.to_numeric": ["pop"],
    ...     "lb.dm.to_other_specify": ["other"],
    ...     "lb.dm.to_recist": ["recist"],
    ...     "lb.dm.to_sex" : ["sex"]
    ... }
    >>>
    >>> # same results after ...
    """

    def __init__(
        self,
        df: _pd.DataFrame,
        fv: dict,
        verbose: bool = True,
    ):
        self._df = df
        self._verbose = verbose
        if fv is None:
            msg = "fv can't be None"
            raise ValueError(msg)
        else:
            # Experimental below
            parent_frame = _inspect.currentframe().f_back
            # put it in the vf_dict format evaluating the f in
            # parent frame variable dict
            reversed = {}
            for f, vars in fv.items():
                # if f is a string change it to function taking from the enclosing
                # environment
                f = (
                    eval(f, parent_frame.f_locals, parent_frame.f_globals)
                    if isinstance(f, str)
                    else f
                )
                for v in vars:
                    reversed.update({v: f})
            self._directives = reversed

    def coerce(self, keep_coerced_only: bool = False) -> _pd.DataFrame:
        """Method to apply programmed coercions

        Parameters
        ----------
        keep_coerced_only:
            if True keep only variables in fv dictionary, after coercion
        """
        # do not modify the input data
        df = self._df.copy()
        # keep order of the input variables
        varorder = df.columns.to_list()
        directives = self._directives
        # make verbose all the functions by decorating them
        if self._verbose:
            for var in directives.keys():
                directives[var] = _verboser(directives[var])
        # apply the coercers, but first modify the pd printing options temporarily to
        # handle long reporting of changes
        old_nrows = _pd.get_option("display.max_rows")
        _pd.set_option("display.max_rows", None)
        for var, fun in directives.items():
            if var not in df.columns:
                msg = f"{var} not in df.columns, aborting."
                raise ValueError(msg)
            if self._verbose:
                print(f"Processing {var}.")
            df[var] = fun(df[var])
        _pd.set_option("display.max_rows", old_nrows)
        # return results
        if keep_coerced_only:
            keep = list(directives.keys())
            kept_in_order = [v for v in varorder if v in keep]
            return df[kept_in_order]
        else:
            return df[varorder]


@_singledispatch
def group_prog_id(x):
    """Count the number of times each id was already seen

    Parameters
    ----------
    x: list or np.array or pd.Dataframe
        group indicator

    Examples
    --------
    >>> # no missings
    >>> group_prog_id(3)
    >>> group_prog_id([0, 1, 1, 1, 2, 0, 2, 0])
    >>> group_prog_id(np.array([0, 1, 1, 1, 2, 0, 2, 0]))
    >>> group_prog_id(pd.Series([0, 1, 1, 1, 2, 0, 2, 0]))
    >>> # with missing
    >>> group_prog_id(np.array([1, 1, 0, np.nan, np.nan]))
    >>> group_prog_id(pd.Series([1, 1, 0, pd.NA, pd.NA]))
    """
    raise NotImplementedError(f"{type(x)} is not handled.")


def _group_prog_id_worker(x):
    seen = _Counter()
    rval = []
    for elem in x:
        seen[elem] += 1
        rval.append(seen[elem])
    return rval


@group_prog_id.register
def _(x: list):
    return _group_prog_id_worker(x)


@group_prog_id.register
def _(x: _np.ndarray):
    res = _np.array(_group_prog_id_worker(x))
    return _np.where(_np.isnan(x), _np.nan, res)


@group_prog_id.register
def _(x: _pd.Series):
    rval = _pd.Series(_group_prog_id_worker(x))
    rval[_pd.isna(x)] = _pd.NA
    return to_integer(rval)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
