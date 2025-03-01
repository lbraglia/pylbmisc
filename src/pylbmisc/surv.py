"""
surv
========================================
Survival analysis function and utilities.
"""

import numpy as _np
import pandas as _pd
import matplotlib.pyplot as _plt

from lifelines import KaplanMeierFitter as _KaplanMeierFitter
from lifelines.plotting import add_at_risk_counts as _add_at_risk_counts
from lifelines.statistics import multivariate_logrank_test as _multivariate_logrank_test
from lifelines.utils import qth_survival_times as _qth_survival_times
from pylbmisc.dm import to_date as _to_date
from pylbmisc.dm import to_integer as _to_integer
from pylbmisc.stats import p_format as _p_format
from warnings import warn as _warn


def _estquant(fit, quantiles):
    "Return estimates and quantiles of survival function with confidence intervals"
    estimates = _pd.concat([fit.survival_function_, fit.confidence_interval_],
                           axis = "columns")
    quant = _qth_survival_times(quantiles, estimates)
    quant = quant.reset_index()
    quant.columns = ["Quantile", "Estimate", "Lower", "Upper"]
    estimates = estimates.reset_index() # take time as variable
    estimates.columns = ["time", "Estimate", "Lower", "Upper"]
    return estimates, quant


def km(time,
       status,
       group=None,
       plot=True,
       ylab="Survival probability",
       xlab="Time",
       counts=["Events"],
       xticks=None,
       ci_alpha=0.3,
       quantiles=[0.5],
       plot_logrank=True):
    """Kaplan-Meier estimates and logrank test.

    Does the Kaplan-Meier plot with logrank

    Parameters
    ----------
    time: time
        the time
    status: dichotomic
        the event indicator
    group: categorical variable
        a grouping variable used to create different survival groups/function
    ylab: ylab
        as in R
    xlab: xlab
        as in R
    counts: list
         containing ["At risk", "Events", "Censored"]
    xticks: a slice
         slice used for plotting (loc) eg slice(5) plots up to time = 5
    ci_alpha: percentage
         shading (alpha) for confidence interval  (set to 0 for no CI)
    quantiles: list[float]
         a list of quantiles of survival function to be returned (by default median)
    plot_logrank: bool
         add logrank to the plot

    Returns
    -------
    dict
        dict with some results

    """
    if plot:
        fig, ax = _plt.subplots()
        plot_at_risk = bool(counts)
    if group is None: #----------------------single curve -----------------------------
        kmf = _KaplanMeierFitter()
        df = _pd.DataFrame({"time": time, "status": status}).dropna() # handle
        fit = kmf.fit(df["time"], df["status"])
        estimates, quants = _estquant(fit, quantiles)
        if plot:
            ax = fit.plot_survival_function(loc = xticks, ci_alpha = ci_alpha)
            ax.set_ylabel(ylab)
            ax.set_xlabel(xlab)
            # avoid legend for 1 group
            lgnd = ax.legend()
            lgnd.set_visible(False)
            if plot_at_risk:
                _add_at_risk_counts(fit, labels = ["All"],
                                   rows_to_show = counts,
                                   ax = ax, fig = fig)
                _plt.tight_layout()
            fig.show()
        return {
            "fit": fit,
            "estimates": estimates,
            "quantiles": quants
        }
    else:  #---------------------- several curves -----------------------------
        try:
            categs = group.cat.categories.to_list()
        except AttributeError:
            msg = "Group must be a pandas categorical variable."
            print(msg)
        if len(categs) < 2:
            msg = "Group must have at least two categories."
            raise Exception(msg)
        # do fit for all categories
        fits = {}               # fits
        estimates = {}          # survival estimates
        quants = []             # quantiles
        df = _pd.DataFrame({"time": time, "status": status, "group": group}).dropna() # handle
        df["group"] = df.group.cat.remove_unused_categories()
        new_categs = df.group.cat.categories.to_list()
        if len(new_categs) < len(categs):
            removed_categ = set(categs) - set(new_categs)
            removed_categ_str = ", ".join(removed_categ)
            msg = f"Some categories were removed due to missingness: {removed_categ_str}."
            _warn(msg)
        for categ in new_categs:
            kmf = _KaplanMeierFitter(label = ylab)
            mask = df["group"] == categ
            fits[categ] = f = kmf.fit(df.loc[mask, "time"], df.loc[mask, "status"], label = categ)
            e, q = _estquant(f, quantiles)
            estimates[categ] = e
            q.insert(0, "Group", categ)
            quants.append(q)
            if plot:
                kmf.plot_survival_function(ax = ax,
                                           loc = xticks,
                                           ci_alpha = ci_alpha)
        quants = _pd.concat(quants)
        lr = _multivariate_logrank_test(df["time"], df["group"], df["status"])
        if plot:
            ax.set_ylabel(ylab)
            ax.set_xlabel(xlab)
            lgnd = ax.legend(loc = "upper right")
            # lgnd.set_visible(False)

            if plot_at_risk:
                _add_at_risk_counts(*list(fits.values()),
                                   rows_to_show = counts,
                                   ax = ax, fig = fig)
                _plt.tight_layout()
            if plot_logrank:
                lr_string = (f"logr: {lr.test_statistic:.3f}, "
                             f"df: {lr.degrees_of_freedom}, "
                             f"p: {_p_format(lr.p_value)}")
                ax.set_title(lr_string)
            fig.show()
        return {
            "fit": fits,
            "estimates": estimates,
            "quantiles": quants,
            "logrank": lr
        }


# --------------------------------------------------------------------------------------


def _date_check(x: _pd.Series, name: str = "date", can_be_none: bool = False):
    if (x is None) and (not can_be_none):
        msg = f"{name} can't be None"
        raise Exception(msg)
    allowed = _pd.api.types.is_datetime64_dtype(x) 
    if not allowed:
        msg = f"{name} must be an allowed type (numeric or datetime)"
        raise Exception (msg)


def _check_sequential_dates(x: _pd.DataFrame):
    int_dates = x.apply(_to_integer, axis = 1)
    na_dates = x.isna()
    int_dates[na_dates] = _pd.NA
    not_sequential = (int_dates.diff(axis=1) < 0)
    not_sequential_mask = not_sequential.any(axis=1)
    if not_sequential_mask.any():
        msg = "Some dates are not sequential."
        _warn(msg)
        with _pd.option_context("display.max_rows", None, "display.max_columns", None):
            print(_pd.concat([x, not_sequential], axis = 1).loc[not_sequential_mask, :])

            
def _check_negative_times(s, t, outcome):
    status = s.copy()
    time = t.copy()
    neg_times = time < 0
    if neg_times.any():
        msg = f"Some {outcome} times are < 0. Setting to NA both time and status below. Please fix the dates."
        _warn(msg)
        with _pd.option_context("display.max_rows", None, "display.max_columns", None):
            print(_pd.DataFrame({"status": status, "time": time}).loc[neg_times, :])
        status[neg_times] = _pd.NA
        time[neg_times] = _pd.NA
    return status, time

        
def tteep(start_date = None,
          prog_date = None,
          death_date = None,
          last_fup = None,
          ep=["os", "pfs", "ttp"]# ,
          # comprisk=True
          ):
    """This function calculates common oncology time to event end-points
    (Overall Survival, Progression Free Survival, Time to Relapse).

    Overall survival (OS) is computed as time from {start_date} to
    {death_date}. Time of patients who did not experienced the event (with missing
    {death_date}) is censored at the time of last follow up ({last_fup}).

    Progression free survival (PFS) is calculated as time from {start_date}
    to {prog_date} or {death_date}, whichever comes first. Time of
    patients who did not experienced any event (missing both {prog_date} and
    {death_date}) is censored at the time of last follow up ({last_fup}).

    Time to progression (TTP) is computed as time from {start_date} to
    {prog_date}. Time of patients who did not experienced the event
    (missing {prog_date}) is censored at the time of last follow up
    ({last_fup}) or death ({death_date}) whichever comes first.

    Parameters
    ----------
    start_date: Date
        starting follow up date
    prog_date: Date
        progression date
    death_date: Date
        death date
    last_fup: Date
        last follow up date
    ep:
        which end points to calculate, default to ["os","pfs","ttp"]

    Examples
    --------
    >>> # date input
    >>> df = pd.DataFrame({"start_date" : lb.dm.to_date(pd.Series(["1900-01-01", "1900-01-01", "1900-01-01", "1900-01-01",        pd.NA, "1900-01-01", "1900-04-01", pd.NA])),
    >>>                    "prog_date"  : lb.dm.to_date(pd.Series(["1900-03-01", "1900-03-01",        pd.NA,        pd.NA,        pd.NA,        pd.NA, "1900-02-01", pd.NA])),
    >>>                    "death_date" : lb.dm.to_date(pd.Series(["1900-06-01",        pd.NA, "1900-06-01",        pd.NA,        pd.NA,        pd.NA, "1900-06-01", pd.NA])),
    >>>                    "last_fup"   : lb.dm.to_date(pd.Series(["1900-06-01", "1900-12-31", "1900-06-01", "1900-12-31", "1900-12-31",        pd.NA, "1900-06-01", pd.NA]))
    >>> })
    >>> print(df)
    >>> tteep(df.start_date, df.prog_date, df.death_date, df.last_fup)

    Reference
    ----------
    Guidance for Industry, Clinical Trial Endpoints for the approval of cancer
    drugs and biologics, FDA, May 2007

    """
    
    _date_check(x = start_date, name = "start_date", can_be_none = False)
    _date_check(x = last_fup, name = "last_fup", can_be_none = False)
    _date_check(x = prog_date, name = "prog_date", can_be_none = True)
    _date_check(x = death_date, name ="death_date", can_be_none = True)

    n = len(start_date)
    
    # Create indicator variables based on dates
    prog = (~prog_date.isna()) if (prog_date is not None) else _pd.Series([_pd.NA] * n)
    death = (~death_date.isna()) if (death_date is not None) else _pd.Series([_pd.NA] * n)

    # dates dataframe for checks and other
    all_dates = _pd.DataFrame({
        "start_date": start_date,
        "prog_date": prog_date,
        "death_date": death_date,
        "last_fup": last_fup
    })
    
    # Check sequential dates
    _check_sequential_dates(all_dates)

    rval = {}
    if "os" in ep:
        os_status = _to_integer(death)
        os_last_date = _np.where(os_status, death_date, last_fup)
        os_time = (os_last_date - start_date).dt.days
        os_status[os_time.isna()] = _pd.NA
        s, t = _check_negative_times(os_status, os_time, "OS")
        rval["os_status"] = s
        rval["os_time"] = t
        
    if "pfs" in ep:
        pfs_status = _to_integer(death | prog)
        min_prog_death = _pd.concat([death_date, prog_date], axis=1).min(axis=1)
        pfs_last_date = _np.where(pfs_status, min_prog_death, last_fup)
        pfs_time = (pfs_last_date - start_date).dt.days
        pfs_status[pfs_time.isna()] = _pd.NA
        s, t = _check_negative_times(pfs_status, pfs_time, "PFS")
        rval["pfs_status"] = s
        rval["pfs_time"] = t
            
    if "ttp" in ep:
        ttp_status = _to_integer(prog)
        min_death_lfup = _pd.concat([death_date, last_fup], axis=1).min(axis=1)
        ttp_last_date = _np.where(ttp_status, prog_date, min_death_lfup)
        ttp_time = (ttp_last_date - start_date).dt.days
        ttp_status[ttp_time.isna()] = _pd.NA
        s, t = _check_negative_times(ttp_status, ttp_time, "TTP")
        rval["ttp_status"] = s
        rval["ttp_time"] = t


    return _pd.DataFrame(rval)



if __name__ == "__main__":

    df = _pd.DataFrame({
        "start_date" : _to_date(_pd.Series(["1900-01-01", "1900-01-01", "1900-01-01", "1900-01-01",        _pd.NA, "1900-01-01", "1900-04-01", _pd.NA])),
        "prog_date"  : _to_date(_pd.Series(["1900-03-01", "1900-03-01",        _pd.NA,        _pd.NA,        _pd.NA,        _pd.NA, "1900-05-01", _pd.NA])),
        "death_date" : _to_date(_pd.Series(["1900-06-01",        _pd.NA, "1900-06-01",        _pd.NA,        _pd.NA,        _pd.NA, "1900-06-01", _pd.NA])),
        "last_fup"   : _to_date(_pd.Series(["1900-06-01", "1900-12-31", "1900-06-01", "1900-12-31", "1900-12-31",        _pd.NA, "1900-06-01", _pd.NA]))
    })

    # some wrong insertions
    df2 = _pd.DataFrame({
        "start_date" : _to_date(_pd.Series(["1900-01-01", "1900-01-01", "1900-01-01", "1900-01-01",        _pd.NA, "1900-01-01", "1900-04-01", _pd.NA])),
        "prog_date"  : _to_date(_pd.Series(["1899-03-01", "1900-03-01",        _pd.NA,        _pd.NA,        _pd.NA,        _pd.NA, "1900-02-01", _pd.NA])),
        "death_date" : _to_date(_pd.Series(["1900-06-01",        _pd.NA, "1900-06-01",        _pd.NA,        _pd.NA,        _pd.NA, "1900-06-01", _pd.NA])),
        "last_fup"   : _to_date(_pd.Series(["1900-06-01", "1900-12-31", "1900-06-01", "1900-12-31", "1900-12-31",        _pd.NA, "1900-06-01", _pd.NA]))
    })


    print(tteep(df.start_date, df.prog_date, df.death_date, df.last_fup)) # ok
    print(tteep(df2.start_date, df2.prog_date, df2.death_date, df2.last_fup)) # some wrong




# if False:
    
#     # Competing risk endpoint
#     if comprisk:
#         all_dates2_n = all_dates.apply(lambda x: x.astype('int64') // 10**9)

#         first_event_date = all_dates2_n.min(axis=1)
#         first_event_time = (first_event_date - all_dates2_n['start_date'])
        
#         first_event_status_labels = ['Progression', 'Death', 'FUP exit']
#         first_event_status_codes = all_dates2_n.apply(lambda row: row.idxmin(), axis=1).map(lambda x: first_event_status_labels.index(x))
        
#         first_event_status_codes[first_event_time.isna()] = _pd.NA
        
#         neg_times = (first_event_time < 0)
#         if neg_times.any():
#             print("some first times are < 0")
#             if sequential_strict:
#                 first_event_time[neg_times] = _pd.NA
#                 first_event_status_codes[neg_times] = _pd.NA
        
#         rval_df["first_event_time"] = first_event_time
#         rval_df["first_event_status"] = _pd.Categorical.from_codes(first_event_status_codes, categories=first_event_status_labels)
