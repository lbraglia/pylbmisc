"""Handy confidence intervals"""

import pandas as _pd
from pylbmisc.r import match_arg as _match_arg
from scipy import stats as _stats


def ci_prop(x, n=None, nas=0, confidence_level=0.95,
            method="exact",
            alternative="two-sided"
            ):
    """Confidence interval for single proportion

    It's 95% two-sided exact Clopper-Pearson by default.

    Parameters
    ----------
    x: int or pd.Categorical with two categories
        variable or count of successes
    n: int
        if x is integer, number of trials
    nas: int
        if x is integer, number of missing values out of n
    confidence_level: float
        confidence level for confidence interval
    method: str
        one between "exact" (default Clopper-Pearson), "wilson" (Wilson without
        continuity correction) "ccwilson" (Wilson with continuity correction)
        or any of their abbreviations
    alternative: str
        one between "two-sided", "greater", "less" or their abbreviations

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
    method = _match_arg(method, ["exact", "wilson", "ccwilson"])
    alternative = _match_arg(alternative, ["two-sided", "greater", "less"])
    # move to scipy.stats._result_classes.BinomTestResult.proportion_ci naming
    # wilsoncc
    if method == "ccwilson":
        method = "wilsoncc"

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
            n=first_group_n + second_group_n,
            alternative=alternative
        )
        ci = binom_test.proportion_ci(
            confidence_level=confidence_level,
            method=method
        )
    except Exception:  # fix this someday
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
