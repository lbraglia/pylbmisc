import pandas as _pd

def _pstar_worker(p):
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    else:
        return ""

def _pformat_worker(p):
    if p < 0.001:
        return "< 0.001"
    else:
        return "%.3f" % p

def pstar(p):
    """ The unholy p-value stars """
    if isinstance(p, float):
        return _pstar_worker(p)
    elif isinstance(p, _pd.Series):
        return p.map(_pstar_worker)
    else:
        return None 
        
def pformat(p):
    """ Pretty print (format) p-value for publication """
    if isinstance(p, float):
        return _pformat_worker(p)
    elif isinstance(p, _pd.Series):
        return p.map(_pformat_worker)
    else:
        return None 
