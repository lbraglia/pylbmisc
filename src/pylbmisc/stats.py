"""Statistical utilities/routines"""

import pandas as _pd
import numpy as _np
from pylbmisc.r import match_arg as _match_arg
from scipy import stats as _stats


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
    elif p == 1:
        return "0.999"
    else:
        tmp = f"{p:.3f}"
        return tmp if tmp != "nan" else ""


def p_star(p):
    """The unholy p-value stars"""
    if isinstance(p, float):
        return _pstar_worker(p)
    elif isinstance(p, _pd.Series):
        return p.map(_pstar_worker)
    else:
        return None


def p_format(p):
    """Pretty print (format) p-value for publication"""
    if isinstance(p, float):
        return _pformat_worker(p)
    elif isinstance(p, _pd.Series):
        return p.map(_pformat_worker)
    else:
        return None


def p_adjust(p, method="holm"):
    """A quick/simple port of p.adjust with main methods used by me

    See scipy.stats for FDR/BH methods

    Examples
    --------
    >>> # without missing
    >>> # > wikipedia = c(0.01, 0.04, 0.03, 0.005)
    >>> # > p.adjust(wikipedia)
    >>> # [1] 0.03 0.06 0.06 0.02
    >>> wikipedia = [0.01, 0.04, 0.03, 0.005]
    >>> p_adjust(wikipedia)
    >>>
    >>> # with missing
    >>> # > wikipedia_miss = c(0.01, NA, 0.04, 0.03, 0.005, NA)
    >>> # > p.adjust(wikipedia_miss)
    >>> # [1] 0.03   NA 0.06 0.06 0.02   NA
    >>> wikipedia_miss = [0.01, np.nan, 0.04, 0.03, 0.005, np.nan]
    >>> p_adjust(wikipedia_miss)
    """
    if isinstance(p, list):
        x = _np.array(p)
    elif isinstance(p, _pd.Series):
        x = p.values
    elif isinstance(p, _np.ndarray):
        x = p
    else:
        msg = "x must be list, series or array"
        raise ValueError(msg)

    # checking content type
    if not _np.issubdtype(x.dtype, _np.floating):
        msg = "p-values must be a float."
        raise ValueError(msg)

    # checking method requested
    allowed_methods = ["none", "bonferroni", "holm"]
    method = _match_arg(method, allowed_methods)

    # methods implementation
    n = len(x)
    n_nonmiss = (~_np.isnan(x)).sum()
    if method == "none":
        p_adj = x
    elif method == "bonferroni":
        p_adj = x * n_nonmiss
        for i, pa in enumerate(p_adj):
            if pa > 1:
                p_adj[i] = 1
    elif method == "holm":
        p_adj = _np.empty(n)
        values = [(pval, prog_id) for prog_id, pval in enumerate(x)]
        # ordino sulla base dei p.value, i missing finiscono alla fine ma ho
        # tenuto l'ordine dove compaiono nel secondo elemento ora per poter
        # ordinare sulla base dei p, in presenza di missing è necessario usare
        # np.sort che richiede uno structured array (vedi np.sort)
        dtype = [("pval", float), ("prog_id", int)]
        values = _np.array(values, dtype=dtype)
        sa = _np.sort(values, order="pval")
        pmax = 0  # initialize so the first maximum
        for k, vals in enumerate(sa, start=1):
            pval, prog_id = vals
            if not _np.isnan(pval):
                res = pval * (n_nonmiss - k + 1)
                res = res if res < 1 else 1
                pmax = res if res > pmax else pmax
                p_adj[prog_id] = pmax
            else:
                p_adj[prog_id] = _np.nan
    else:
        msg = "method uncorrectly specified"
        raise ValueError(msg)

    # exiting
    return p_adj


def ci_prop(x, n=None, nas=0, confidence_level=0.95, method="exact"):
    """Exact Clopper-Pearson confidence interval

    Parameters
    ----------
    x: int or pd.Categorical with two categories
        variable or count of successes
    n: int
        if x is integer, number of trials
    nas: int
        if x is integer, number of missing values out of n

    Examples
    --------
    >>> # single variable
    >>> ci_prop(df.adesione_intervento_proposto)
    >>> ci_prop(27, 27+21, 34)

    >>> # several variables stratified by time
    >>> main_vars = ['adesione_intervento_posto_di_lavoro', 'proposta_posto_di_lavoro',
    ...              'adesione_intervento_proposto', 'follow_up', 'soddisfazione',
    ...              'rtw_continuazione_del_lavoro_alla_fine_del_follow_up']
    >>>
    >>> res = {}
    >>> for var in main_vars:
    ...     res[var] = (
    ...           df.loc[:, var].groupby(df.time).apply(lambda x: ci_prop(x=x))
    ...                         .reset_index().drop(columns = ["level_1"])
    ... )
    """
    if n is None:
        # caso in cui passo una serie: guarda le labels (la seconda,
        # tipicamente "Yes" sarà usata per il numeratore)
        groups = x.cat.categories
        first_group = groups[0]
        second_group = groups[1]
        na = x.isna().sum()
        first_group_n = x.isin([first_group]).sum()
        second_group_n = x.isin([second_group]).sum()
    else:
        # caso in cui passo delle conte già fatte
        first_group = "unsuccesses"
        second_group = "successes"
        na = nas
        first_group_n = n - x - na
        second_group_n = x

    try:
        binom_test = _stats.binomtest(
            k=second_group_n,
            n=first_group_n + second_group_n
        )
        ci = binom_test.proportion_ci(
            confidence_level=confidence_level,
            method=method
        )
    except Exception:
        est = _pd.NA
        lower = _pd.NA
        upper = _pd.NA
    else:
        est = binom_test.statistic
        lower = ci.low
        upper = ci.high

    return _pd.DataFrame({
        "n": [na + first_group_n + second_group_n],
        "NA": [na],
        first_group: [first_group_n],
        second_group: [second_group_n],
        "perc": [est * 100],
        "ci_lower": [lower * 100],
        "ci_upper": [upper * 100]
    })
