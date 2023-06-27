def pstar(p):
    def _pstar_worker(p):
        if p < 0.001:
            return "***"
        elif p < 0.01:
            return "**"
        elif p < 0.05:
            return "*"
        else:
            return ""

    if isinstance(p, float):
        return _pstar_worker(p)
    elif isinstance(p, pd.Series):
        return p.map(_pstar_worker)
    else:
        return None 
        
def pformat(p):
    def _pformat_worker(p):
        if p < 0.001:
            return "< 0.001"
        else:
            return "%.3f" % p
        
    if isinstance(p, float):
        return _pformat_worker(p)
    elif isinstance(p, pd.Series):
        return p.map(_pformat_worker)
    else:
        return None 
