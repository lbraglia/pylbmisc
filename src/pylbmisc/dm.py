"""Data management utilities for pandas Series/DataFrame"""

import functools as _functools
import inspect as _inspect
import numpy as _np
import pandas as _pd
import re as _re
import string as _string
import subprocess as _subprocess
import tempfile as _tempfile

from pprint import pprint as _pprint
from pathlib import Path as _Path

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


# -------------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------------
def view(df: _pd.DataFrame = None) -> None:
    """View a pd.DataFrame using LibreOffice.

    Parameters
    ----------
    df: dataframe
        the dataframe to be visualized

    Examples
    --------
    lb.dm.view(df)
    """
    if not isinstance(df, _pd.DataFrame):
        msg = "Only dataframes are visualized."
        raise Exception(msg)
    tempfile = _tempfile.mkstemp(suffix=".xlsx")
    fname = tempfile[1]
    df.to_excel(fname)
    _subprocess.Popen(["libreoffice", fname])
    return None


def table2df(df: _pd.DataFrame = None) -> _pd.DataFrame:
    """Transform a pd.DataFrame representing a two-way table (es
    crosstable, correlation matrix, p.val matrix) in a
    pd.DataFrame with long format.

    Parameters
    ----------
    df: DataFrame
       the crosstabulation to be put in long form
    """
    if not isinstance(df, _pd.DataFrame):
        msg = "Only dataframes are processed."
        raise Exception(msg)
    x = df.copy()
    x = x.stack().reset_index()
    return x.rename(columns={0: "x"})


def dump_unique_values(dfs: _pd.DataFrame | dict[str, _pd.DataFrame],
                       fpath: str | _Path = "data/uniq_"):
    """Save unique value of a (dict of) dataframe for inspection and monitor
    during time.
    """
    if not isinstance(dfs, (_pd.DataFrame, dict)):
        msg = "x deve essere un pd.DataFrame o un dict di pd.DataFrame"
        raise ValueError(msg)

    # normalize single dataframe
    if isinstance(dfs, _pd.DataFrame):
        dfs = {"df": dfs}

    for df_lab, df in dfs.items():
        outfile = _Path(str(fpath) + df_lab + ".txt")
        with outfile.open("w") as f:
            for col in df:
                # Header
                print(f"DataFrame: '{df_lab}' "
                      f"Column: '{col}', "
                      f"Dtype: {df[col].dtype}, "
                      f"Unique values:",
                      file=f)
                # Dati: non sortati perché ci sono problemi se i dati sono metà
                # numerici e meta stringa
                # _pprint(df[col].sort_values().unique().tolist(), stream = f,
                # compact=True)
                _pprint(df[col].unique().tolist(), stream=f, compact=True)
                print(file=f)


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


is_email = _np.vectorize(lambda x: bool(_mail_re.match(x)))


def _is_string(x: _pd.Series) -> bool:
    """
    Check if a Series is a string (including data with np.nan) differently from
    pandas.api.types.is_string_dtype

    Examples
    --------
    >>> x = pd.Series(["a", np.nan])
    >>> pd.api.types.is_string_dtype(x)
    >>> _is_string(x)
    """
    return x.dtype == "O"


def _has_emails(x: _pd.Series) -> bool:
    if _is_string(x):
        check = is_email(x)
        return _np.any(check)
    else:
        return False


# Fiscal code
is_fiscal_code = _np.vectorize(lambda x: bool(_fc_re.match(x)))


def _has_fiscal_codes(x: _pd.Series) -> bool:
    if _is_string(x):
        check = is_fiscal_code(x)
        return _np.any(check)
    else:
        return False


# Telephone number:
is_telephone_number = _np.vectorize(lambda x: bool(_tel_re.match(x)))


def _has_telephone_numbers(x: _pd.Series) -> bool:
    if _is_string(x):
        check = is_telephone_number(x)
        return _np.any(check)
    else:
        return False


# Mobile number
is_mobile_number = _np.vectorize(lambda x: bool(_mobile_re.match(x)))


def _has_mobile_numbers(x: _pd.Series) -> bool:
    if _is_string(x):
        check = is_mobile_number(x)
        return _np.any(check)
    else:
        return False


def pii_find(x: _pd.DataFrame) -> list[str]:
    """Find columns with probable piis (Personally Identifiable
    Informations) and return the colnames for further processing.

    Parameters
    ----------
    x: DataFrame
        The DataFrame to check

    Returns
    -------
    list of
    
    Examples
    --------
    >>> df = pd.DataFrame({
    >>>     "id" : [1,2,3],
    >>>     "cognome": ["brazorv", "gigetti", "ginetti"],
    >>>     "nome  " : [1,2,3],
    >>>     "mail": ["lgasd@asdkj.com", " asòdlk@asd.com", "aaaa"],
    >>>     "fc": ["nrgasd12h05h987z", "aaaa", "eee"],
    >>>     "num": ["0654-6540123", "aa", "eee"],
    >>>     "cel": ["3921231231", "aa", "eee"]
    >>>     })
    >>>
    >>> probable_piis = pii_find(df)
    >>> if probable_piis:
    >>>    df.drop(columns=probable_piis)

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
                print(f"{var} matches 'surname'/'cognome'.")
            if is_name:
                print(f"{var} matches 'name'/'nome'.")
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


def _remove_duplicated_underscore(s):
    return _re.sub("_+", "_", s)


def _remove_external_underscore(s):
    return _re.sub("^_", "", _re.sub("_$", "", s))


def _add_x_if_first_is_digit(s):
    if s.startswith(tuple(_string.digits)):
        return "x" + s
    else:
        return s


def fix_varnames(x: str | list[str]):
    """The good-old R preprocess_varnames, returns just the fixed strings. See
    sanitize_varnames for DataFrame or dict of DataFrames.

    Parameters
    ----------
    x: str or list of strings
        string or list of strig to be fixed

    Examples
    --------
    >>> fix_varnames("  asd 98n2 3")
    >>> fix_varnames([" 98n2 3", " L< KIAFJ8 0_________"])
    >>> fix_varnames(["asd", "foo0", "asd"])
    """
    if isinstance(x, str):
        original = [x]
    elif isinstance(x, list):
        original = x
    else:
        msg = "Only str and list are allowed, see sanitize_varnames for DataFrame or dict of DataFrames."
        raise ValueError(msg)
    # let's go functional: s is (should be) a str, the following are to be applied
    # in order
    funcs = [
        lambda s: str(s),
        lambda s: s.lower().strip(),
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
    mod = [worker(s) for s in original]
    # handle duplicated names by adding numeric postfix
    has_duplicates = len(mod) != len(set(mod))
    if has_duplicates:
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
    return uniq if not isinstance(x, str) else uniq[0]


def sanitize_varnames(x: _pd.DataFrame | dict[str, _pd.DataFrame],
                      return_tfd: bool = True):
    """Fix a DataFrame or a dict of DataFrames names using fix_varnames to
    obtain the cleaned ones.

    Parameters
    ----------
    x: dataframe or dict of dataframes
       the data to be fixed
    return_tfd: bool
       wheter to return or not (default return) the original and processed
    strings as dict

    """
    if isinstance(x, _pd.DataFrame):
        from_name = list(x.columns.values)
        to_name = fix_varnames(from_name)
        df = x.copy()
        df.columns = to_name
        tf = {t : f for t, f in zip(to_name, from_name)}
        if return_tfd:
            return df, tf
        else:
            return df
    elif isinstance(x, dict):
        dfs = {}
        tfs = {}
        for k, v in x.items():
            from_name = list(v.columns.values)
            to_name = fix_varnames(from_name)
            df = v.copy()
            df.columns = to_name
            tf = {t: f for t, f in zip(to_name, from_name)}
            dfs[k] = df
            tfs[k] = tf
        if return_tfd:
            return dfs, tfs
        else:
            return dfs



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

def to_bool(x: _pd.Series):
    """Coerce to boolean a pd.Series (numeric) using astype keeping NAs as NAs

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> to_bool(pd.Series([1,0,1,0]))
    >>> to_bool(pd.Series([1,0.,1,0.]))
    >>> to_bool(pd.Series([1,0,1,0, np.nan]))
    """
    nas = _pd.isna(x)
    rval = x.astype("boolean")
    rval[nas] = _pd.NA
    return rval


def _replace_comma(x: _pd.Series):
    if _is_string(x):
        # nas = x.isin(["", _pd.NA, _np.nan])
        nas = (x.isna()) | (x == "")
        rval = x.astype("str").str.replace(",", ".")
        rval[nas] = _pd.NA
        return rval
    else:
        return x


def to_integer(x: _pd.Series):
    """Coerce a pd.Series to integer (if possible)

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> to_integer(pd.Series([1., 2., 3., 4., 5., 6., np.nan]))
    >>> to_integer(pd.Series(["2001", "2011", "1999", ""]))
    >>> to_integer(pd.Series(["1.1", "1,99999", "foobar"])) # fails because of 1.99
    """
    s = _replace_comma(x)
    # return _np.floor(_pd.to_numeric(s, errors='coerce')).astype('Int64')
    # mi fido piu di quella di sotto anche se fallisce con i numeri con virgola
    # (che ci può stare, per i quale bisogna usare np.floor)
    return _pd.to_numeric(s, errors="coerce").astype("Int64")


def to_numeric(x: _pd.Series):
    """Coerce a pd.Series using pd.to_numeric

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> to_numeric(pd.Series([1, 2, 3]))
    >>> to_numeric(pd.Series([1., 2., 3., 4., 5., 6.]))
    >>> to_numeric(pd.Series(["2001", "2011", "1999"]))
    >>> to_numeric(pd.Series(["1.1", "2,1", "asd", ""]))
    """
    s = _replace_comma(x)
    return _pd.to_numeric(s, errors="coerce").astype("Float64")


def to_datetime(x: _pd.Series):
    """Coerce to a datetime a pd.Series

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> import datetime as dt
    >>> to_datetime(pd.Series([str(dt.datetime.now())] * 6))
    """
    return _pd.to_datetime(x, errors="coerce")


def to_date(x: _pd.Series):
    """Coerce to a date a pd.Series

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> import datetime as dt
    >>> to_date(pd.Series([str(dt.datetime.now())] * 6))
    >>> to_date(pd.Series(["2020-01-02", "2021-01-01", "2022-01-02"] * 2))
    """
    return to_datetime(x).dt.floor("D")


_dates_re = _re.compile(r"[^/\d-]") # keep only numbers, - and /, and just hope for the best

def _extract_dates_worker(x):
    if isinstance(x, str): # handle missing values (sono float)
        polished = _dates_re.sub("", x)
        return _pd.to_datetime(polished)
    else:
        # return _np.nan
        return _pd.NA


def extract_dates(x: _pd.Series):
    """Try to extract dates from shitty strings and convert them to proper

    Parameters
    ----------
    x: Series
        The Series to be used

    Examples
    --------
    >>> extract_dates(pd.Series(["2020-01-02", "01/01/1956", "asdasd 12-01-02"] * 2))
    """
    return x.apply(_extract_dates_worker)


def to_categorical(x: _pd.Series,
                   categories: list[str] = None,
                   lowcase: bool = False):
    """Coerce to categorical a pd.Series, with blank values as missing

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> to_categorical(pd.Series([1, 2, 1, 2, 3]))
    >>> to_categorical(pd.Series([1, 2., 1., 2, 3, np.nan]))
    >>> to_categorical(pd.Series(["AA", "sd", "asd", "aa", "", np.nan]))
    >>> to_categorical(pd.Series(["AA", "sd", "asd", "aa", "", np.nan]), categories=["aa", "AA"]  )
    >>> to_categorical(pd.Series(["AA", "sd", "asd", "aa", ""]), lowcase = True)
    """
    if _is_string(x):
        # string preprocessing
        # rm spaces and uniform NAs
        x = x.str.strip()
        nas = (x.isna()) | (x == "")
        x[nas] = _pd.NA
        if lowcase:
            x = x.str.lower()
            if categories != None:
                categories = [c.lower() for c in categories]

    # categorical making
    return _pd.Categorical(x, categories=categories)


def to_noyes(x: _pd.Series):
    """Coerce to no/yes a string pd.Series

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> to_noyes(pd.Series(["","yes","no","boh", "si", np.nan]))
    >>> to_noyes(pd.Series([1,0,0, np.nan]))
    >>> to_noyes(pd.Series([1.,0.,0., np.nan]))
    """
    if _is_string(x):
        # take only the first character and map to n/y
        tmp = x.str.strip().str.lower().str[0]
        tmp[tmp == "s"] = "y"
        tmp = tmp.replace({"0": "n", "1": "y"}) # 0/1 for strings
    else:
        # try to convert to boolean and map to n/y
        tmp = to_bool(x).map({False: "n", True: "y"})


    return to_categorical(tmp.map({"n": "no", "y": "yes"}),
                          categories=["no", "yes"])




def to_sex(x: _pd.Series):
    """Coerce to male/female a pd.Series of strings (Mm/Ff)

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> to_sex(pd.Series(["","m","f"," m", "Fm", np.nan]))
    """
    if not _is_string(x):
        msg = "to_sex only for strings vectors"
        raise Exception(msg)

    # take the first letter (Mm/Ff)
    tmp = x.str.strip().str.lower().str[0]
    tmp = tmp.map({"m": "male", "f": "female"})
    return to_categorical(tmp, categories=["male", "female"])



def to_recist(x: _pd.Series):
    """Coerce to recist categories a pd.Series of strings

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> to_recist(pd.Series(["RC", "PD", "SD", "PR", "RP", "boh", np.nan]))
    """
    if not _is_string(x):
        msg = "to_recist only for strings vectors"
        raise Exception(msg)

    # rm spaces and uppercase and take the first two letters
    tmp = x.str.strip().str.upper().str[:2]
    # uniform italian to english
    ita2eng = {"RC": "CR", "RP": "PR"}
    return to_categorical(tmp.replace(ita2eng),
                          categories=["CR", "PR", "SD", "PD"])


def to_other_specify(x: _pd.Series):
    """Try to polish a bit a free-text variable and create a categorical one

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> x = pd.Series(["asd", "asd", "", "prova", "ciao", 3]+ ["bar"]*4)
    >>> to_other_specify(x)
    """
    nas = (x.isna()) | (x == "")
    tmp = x.copy().astype("str").str.strip().str.lower()
    tmp[nas] = _pd.NA
    # categs ordered by decreasing counts
    categs = list(tmp.value_counts().index)
    return to_categorical(tmp, categories=categs)


def to_string(x: _pd.Series):
    """Coerce the pd.Series passed to a string Series

    Parameters
    ----------
    x: Series
        The Series to be coerced

    Examples
    --------
    >>> x = pd.Series(["asd", "asd", "", "prova", "ciao", 3]+ ["bar"]*4)
    >>> to_string(x)
    """
    nas = x.isna()
    rval = x.astype("str")
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
    df: DataFrame
        The DataFrame to be coerced
    fv: dict
        function-variable dict: key can be a function or a string containing name of the function, variables is a list of strings with name of variables to apply the function to


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
    >>>     "idx" :  [1., 2., 3., 4., 5., 6., "2,0", "", np.nan],
    >>>     "sex" :  ["m", "maschio", "f", "female", "m", "M", "", "a", np.nan],
    >>>     "now":   [str(dt.datetime.now())] * 6 + [np.nan, "", "a"],
    >>>     "date":  ["2020-01-02", "2021-01-01", "2022-01-02"] * 2  + [np.nan, "", "a"],
    >>>     "state": ["Ohio", "Ohio", "Ohio", "Nevada", "Nevada", "Nevada"] + [np.nan, "", "a"],
    >>>     "ohio" : [1, 1, 1, 0, 0, 0] + [np.nan] * 3 ,
    >>>     "year":  [str(y) for y in [2000, 2001, 2002, 2001, 2002, 2003]] + [np.nan, "", "a"],
    >>>     "pop":   [str(p) for p in [1.5, 1.7, 3.6, np.nan, 2.9]]  + ["3,2", np.nan, "", "a"],
    >>>     "recist" : ["", "pd", "sd", "pr", "rc", "cr"] + [np.nan, "", "a"],
    >>>     "other" : ["b"]*3 + ["a"]*2 + ["c"] + [np.nan, "", "a"]
    >>> })
    >>> 
    >>> directives = {
    >>>     lb.dm.to_integer: ["idx", "year"],
    >>>     lb.dm.to_sex : ["sex"],
    >>>     lb.dm.to_datetime : ["now"],
    >>>     lb.dm.to_date: ["date"],
    >>>     lb.dm.to_categorical: ["state"],
    >>>     lb.dm.to_bool: ["ohio"],
    >>>     lb.dm.to_numeric: ["pop"],
    >>>     lb.dm.to_recist: ["recist"],
    >>>     lb.dm.to_other_specify: ["other"]
    >>> }
    >>> 
    >>> cleaned1 = lb.dm.Coercer(raw, fv = directives).coerce()
    >>> 
    >>> raw
    >>> cleaned1
    >>> 
    >>> # ------------------------------------------------
    >>> # String as key
    >>> # ------------------------------------------------
    >>>
    >>> directives2 = {
    >>>     "lb.dm.to_categorical": ["state"],
    >>>     "lb.dm.to_date": ["date"],
    >>>     "lb.dm.to_datetime" : ["now"],
    >>>     "lb.dm.to_integer": ["idx", "year"],
    >>>     "lb.dm.to_noyes": ["ohio"],
    >>>     "lb.dm.to_numeric": ["pop"],
    >>>     "lb.dm.to_other_specify": ["other"],
    >>>     "lb.dm.to_recist": ["recist"],
    >>>     "lb.dm.to_sex" : ["sex"]
    >>> }
    >>>
    >>>
    >>> coercer2 = lb.dm.Coercer(raw, fv = directives2)
    >>> cleaned2 = coercer2.coerce()
    """

    def __init__(
        self,
        df: _pd.DataFrame,
        fv: dict | None = None, # function: variables dict
        verbose: bool = True,
    ):
        self._df = df
        self._verbose = verbose
        if fv == None:
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

    def coerce(self, keep_only_coerced=False) -> _pd.DataFrame:
        # do not modify the input data
        df = self._df.copy()
        directives = self._directives
        verbose = self._verbose
        # make verbose all the functions by decorating them
        if verbose:
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
            if verbose:
                print(f"Processing {var}.")
            df[var] = fun(df[var])
        _pd.set_option("display.max_rows", old_nrows)
        # return results
        if keep_only_coerced:
            vars = list(directives.keys())
            df = df[vars]
        return df
