import pandas as pd

# rpy2 per rdataset
import rpy2.robjects as ro                 # tutto il resto ..
import rpy2.rinterface as ri

from rpy2.robjects import pandas2ri        # traduzione data.frame
from rpy2.robjects.packages import importr # importazione pacchetti
from rpy2.robjects.packages import data    # importazione dati

from rpy2.rinterface_lib import na_values
from rpy2.robjects.conversion import localconverter
from rpy2.robjects.conversion import get_conversion

# -------------------------------------------------------------------------
# custom converter for dataframe per gestire gli NA
# https://stackoverflow.com/questions/72657405
custom_converter = ro.default_converter

@custom_converter.rpy2py.register(ri.IntSexpVector)
def to_int(obj):
    return [int(v) if v != na_values.NA_Integer else pd.NA for v in obj]

@custom_converter.rpy2py.register(ri.FloatSexpVector)
def to_float(obj):
    return [float(v) if v != na_values.NA_Real else pd.NA for v in obj]

@custom_converter.rpy2py.register(ri.StrSexpVector)
def to_str(obj):
    return [str(v) if v != na_values.NA_Character else pd.NA for v in obj]

@custom_converter.rpy2py.register(ri.BoolSexpVector)
def to_bool(obj):
    return [bool(v) if v != na_values.NA_Logical else pd.NA for v in obj]

# define the top-level converter
def toDataFrame(obj):
    cv = get_conversion() # get the converter from current context
    return pd.DataFrame(
        {str(k): cv.rpy2py(obj[i]) for i, k in enumerate(obj.names)}
    )

# associate the converter with R data.frame class
custom_converter.rpy2py_nc_map[ri.ListSexpVector].update({"data.frame": toDataFrame})
# -------------------------------------------------------------------------


def dataset(dataset, pkg = 'datasets'):
    '''
    Import an R dataset and convert it to a pandas DataFrame
    '''
    pkgobj = importr(pkg)
    rdf = data(pkgobj).fetch(dataset)[dataset]
    # with (ro.default_converter + pandas2ri.converter).context():
    with (custom_converter + pandas2ri.converter).context():
        df = ro.conversion.get_conversion().rpy2py(rdf)
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
