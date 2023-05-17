import pandas as _pd

import rpy2.robjects as _ro
import rpy2.rinterface as _ri

from rpy2.robjects import pandas2ri as _pandas2ri      # traduzione data.frame
from rpy2.robjects.packages import importr as _importr # importazione pacchetti
from rpy2.robjects.packages import data    as _data    # importazione dati

from rpy2.rinterface_lib import na_values as _RNA


# -------------------------------------------------------------------------
# custom converter for dataframe per gestire gli NA
# https://stackoverflow.com/questions/72657405
_custom_converter = _ro.default_converter

@_custom_converter.rpy2py.register(_ri.IntSexpVector)
def _to_int(obj):
    return [int(v) if v != _RNA.NA_Integer else _pd.NA for v in obj]

@_custom_converter.rpy2py.register(_ri.FloatSexpVector)
def _to_float(obj):
    return [float(v) if v != _RNA.NA_Real else _pd.NA for v in obj]

@_custom_converter.rpy2py.register(_ri.StrSexpVector)
def _to_str(obj):
    return [str(v) if v != _RNA.NA_Character else _pd.NA for v in obj]

@_custom_converter.rpy2py.register(_ri.BoolSexpVector)
def _to_bool(obj):
    return [bool(v) if v != _RNA.NA_Logical else _pd.NA for v in obj]

# define the top-level converter
def _toDataFrame(obj):
    cv = _ro.conversion.get_conversion() # get the converter from current context
    return _pd.DataFrame(
        {str(k): cv.rpy2py(obj[i]) for i, k in enumerate(obj.names)}
    )

# associate the converter with R data.frame class
_custom_converter.rpy2py_nc_map[_ri.ListSexpVector].update(
    {"data.frame": _toDataFrame}
)
# -------------------------------------------------------------------------


def dataset(dataset, pkg = 'datasets'):
    '''
    Import an R dataset and convert it to a pandas DataFrame
    '''
    pkgobj = _importr(pkg)
    rdf = _data(pkgobj).fetch(dataset)[dataset]
    with (_custom_converter + _pandas2ri.converter).context():
        df = _ro.conversion.get_conversion().rpy2py(rdf)
    return df


def match_arg(arg, choices):
    '''
    An R's match.arg equivalent.
    '''
    res = [expanded for expanded in choices \
           if expanded.startswith(arg)]
    l = len(res)
    if l == 0:
        raise ValueError("Parameter ", arg, "must be one of ", choices)
    elif l > 1:
        raise ValueError(arg, "matches multiple choices from ", choices)
    else:
        return res[0]
