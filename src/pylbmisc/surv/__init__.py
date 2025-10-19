"""
surv
========================================
Survival analysis function and utilities.
"""

import numpy as _np
import pandas as _pd
import matplotlib.pyplot as _plt

from lifelines import KaplanMeierFitter as _KaplanMeierFitter
from lifelines import CoxPHFitter as _CoxPHFitter
from lifelines.plotting import add_at_risk_counts as _add_at_risk_counts
from lifelines.statistics import multivariate_logrank_test \
    as _multivariate_logrank_test
from lifelines.utils import qth_survival_times as _qth_survival_times
from pylbmisc.dm import to_integer as _to_integer
from pylbmisc.stats import p_format as _p_format
from warnings import warn as _warn


def _estquant(fit, quantiles):
    """Return estimates and quantiles of survival function with confidence
    intervals"""
    estimates = _pd.concat([fit.survival_function_, fit.confidence_interval_],
                           axis="columns")
    quant = _qth_survival_times(quantiles, estimates)
    quant = quant.reset_index()
    quant.columns = ["Quantile", "Estimate", "Lower", "Upper"]
    estimates = estimates.reset_index()  # take time as variable
    estimates.columns = ["time", "Estimate", "Lower", "Upper"]
    return estimates, quant


def km(time,
       status,
       group=None,
       plot=True,
       plot_censored=True,
       plot_censored_style={"ms": 5,  "marker": "|"},
       plot_legend_loc=None, # TODO IMPLEMENT
       plot_logrank=True,
       ylim=(-0.05, 1.05),
       ylab="Survival probability",
       xlab="Time",
       counts=["Events"],
       xticks=None,
       ci_alpha=0.3,
       quantiles=[0.5]):
    """Kaplan-Meier estimates, logrank test and Hazard ratios.

    Does the Kaplan-Meier plot with logrank

    Parameters
    ----------
    time: time
        the time
    status: dichotomic
        the event indicator
    group: categorical variable
        a grouping variable used to create different survival groups/function
    plot: logical
        wether to do the plot or not (just return estimates)
    plot_censored: logical
        plot ticks of censored observations
    plot_censored_style: dict
        dict of configs given to matplotlib.lines.Line2D
    plot_legend_loc: None, str or pair of floats
        positioning of legend: can None (use defaults: no plotting for one
        curve, "best" for 2+), "none": dont plot, any loc parameter for
        ax.legend (eg "lower center"), "outside": bbox_to_anchor to the right
        by default upper-right if two or more groups are
        available, none if only one group is plotted
    plot_logrank: bool
         add logrank to the plot
    ylim: tuple
        as in R
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
         list of quantiles of survival function to be returned (def: median)

    Returns
    -------
    dict
        dict with some results

    """
    if plot:
        fig, ax = _plt.subplots()
        plot_at_risk = bool(counts)
    if group is None:  # --------------------single curve --------------------
        kmf = _KaplanMeierFitter()
        df = _pd.DataFrame({"time": time, "status": status}).dropna()  # handle
        fit = kmf.fit(df["time"], df["status"])
        estimates, quants = _estquant(fit, quantiles)
        if plot:
            # https://lifelines.readthedocs.io/en/latest/fitters/univariate/KaplanMeierFitter.html
            ax = fit.plot_survival_function(
                loc=xticks,
                show_censors=plot_censored,
                censor_styles=plot_censored_style,
                ci_alpha=ci_alpha)
            ax.set_ylim(ylim)
            ax.set_ylabel(ylab)
            ax.set_xlabel(xlab)
            # legend: avoid by default for 1 group
            if (plot_legend_loc is None or plot_legend_loc == "none"):
                lgnd = ax.legend()
                lgnd.set_visible(False)
            elif (plot_legend_loc == "outside"):
                lgnd = ax.legend(bbox_to_anchor=(1, 1), loc="upper left")
            else:
                lgnd = ax.legend(loc=plot_legend_loc)
            # number at risk
            if plot_at_risk:
                _add_at_risk_counts(fit, labels=["All"],
                                    rows_to_show=counts,
                                    ax=ax, fig=fig)
                _plt.tight_layout()
            fig.show()
        return {
            "fit": fit,
            "estimates": estimates,
            "quantiles": quants
        }
    else:  # ---------------------- several curves ----------------------------
        try:
            categs = group.cat.categories.to_list()
        except AttributeError:
            msg = f"Group must be a pandas categorical variable: now {group.dtype}"
            raise AttributeError(msg)

        if len(categs) < 2:
            msg = "Group must have at least two categories."
            raise Exception(msg)

        # do fit for all categories
        fits = {}               # fits
        estimates = {}          # survival estimates
        quants = []             # quantiles

        df = _pd.DataFrame({
            "time": time,
            "status": status,
            "group": group}).dropna()
        df["group"] = df.group.cat.remove_unused_categories()
        new_categs = df.group.cat.categories.to_list()

        if len(new_categs) < len(categs):
            removed_categ = set(categs) - set(new_categs)
            removed_categ_str = ", ".join(removed_categ)
            msg = "Some categories were removed due" \
                f" to missingness: {removed_categ_str}."
            _warn(msg)

        # Kaplan-meier fit and quantiles
        for categ in new_categs:
            kmf = _KaplanMeierFitter(label=ylab)
            mask = df["group"] == categ
            fits[categ] = f = kmf.fit(df.loc[mask, "time"],
                                      df.loc[mask, "status"],
                                      label=categ)
            e, q = _estquant(f, quantiles)
            estimates[categ] = e
            q.insert(0, "Group", categ)
            quants.append(q)
            if plot:
                kmf.plot_survival_function(
                    ax=ax,
                    show_censors=plot_censored,
                    censor_styles=plot_censored_style,
                    loc=xticks,
                    ci_alpha=ci_alpha)
        quants = _pd.concat(quants)
        # lograng test
        lr = _multivariate_logrank_test(df["time"], df["group"], df["status"])
        # Cox HR:
        # need to construct dummies https://stackoverflow.com/questions/60114847
        dummies = _pd.get_dummies(df.group, drop_first=True)
        df_cox = _pd.concat([df[["time", "status"]], dummies], axis=1)
        cph = _CoxPHFitter().fit(df_cox, 'time', 'status')
        cox_keep = ['coef', 'coef lower 95%', 'coef upper 95%', 'p']
        cox_res = cph.summary[cox_keep]
        cox_res.iloc[:, 0:3] = cox_res.iloc[:, 0:3].apply(_np.exp)
        cox_res.columns = ["HR", "lower.95", "upper.95", "p"]
        cox_res.index = cox_res.index.set_names("group")
        # aggiungo numerosità e gruppo di base per forest plot
        freqs = _pd.DataFrame({"n": df.group.value_counts(dropna=True, sort=False)})
        freqs.index = freqs.index.set_names("group")
        cox_res = _pd.merge(freqs, cox_res,
                            left_index=True, right_index=True,
                            how="left")
        cox_res.iloc[0, 1] = 1 # HR for base group
        
        # plotting
        if plot:
            ax.set_ylim(ylim)
            ax.set_ylabel(ylab)
            ax.set_xlabel(xlab)

            # legend: by default best for more than 1 group
            if (plot_legend_loc is None):
                lgnd = ax.legend(loc="best")
            elif ("none" == plot_legend_loc):
                lgnd = ax.legend()
                lgnd.set_visible(False)
            elif ("outside" == plot_legend_loc):
                lgnd = ax.legend(bbox_to_anchor=(1, 1), loc="upper left")
            else:
                lgnd = ax.legend(loc=plot_legend_loc)
            # number at ris
            if plot_at_risk:
                _add_at_risk_counts(*list(fits.values()),
                                    rows_to_show=counts,
                                    ax=ax, fig=fig)
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
            "logrank": lr,
            "hr": cox_res
        }


# --------------------------------------------------------------------------------------


def _date_check(x: _pd.Series, name: str = "date", can_be_none: bool = False):
    if (x is None) and (not can_be_none):
        msg = f"{name} can't be None"
        raise Exception(msg)
    allowed = _pd.api.types.is_datetime64_dtype(x)
    if not allowed:
        msg = f"{name} must be an allowed type (numeric or datetime)"
        raise Exception(msg)


def _check_sequential_dates(x: _pd.DataFrame):
    int_dates = x.apply(_to_integer, axis=1)
    na_dates = x.isna()
    int_dates[na_dates] = _pd.NA
    not_sequential = (int_dates.diff(axis=1) < 0)
    not_sequential_mask = not_sequential.any(axis=1)
    if not_sequential_mask.any():
        msg = "Some dates are not sequential."
        _warn(msg)
        with _pd.option_context("display.max_rows", None,
                                "display.max_columns", None):
            print(_pd.concat([x, not_sequential],
                             axis=1).loc[not_sequential_mask, :])


def _check_negative_times(s, t, outcome, verbose=True):
    status = s.copy()
    time = t.copy()
    neg_times = time < 0
    if neg_times.any():
        status[neg_times] = _pd.NA
        time[neg_times] = _pd.NA
        if verbose:
            msg = f"Some {outcome} times are < 0. Setting to NA" \
                " both time and status below. Please fix the dates."
            _warn(msg)
            with _pd.option_context("display.max_rows", None,
                                    "display.max_columns", None):
                print(_pd.DataFrame({"status": status,
                                     "time": time}).loc[neg_times, :])
    return status, time


def tteep(start_date=None,
          prog_date=None,
          death_date=None,
          last_fup=None,
          ep=["os", "pfs", "ttp"],
          verbose=True
          ):
    """This function calculates common oncology time to event end-points
    (Overall Survival, Progression Free Survival, Time to Relapse).

    Overall survival (OS) is computed as time from start_date to
    death_date. Time of patients who did not experienced the event (with
    missing death_date) is censored at the time of last follow up
    (last_fup).

    Progression free survival (PFS) is calculated as time from start_date
    to prog_date or death_date, whichever comes first. Time of
    patients who did not experienced any event (missing both prog_date and
    death_date) is censored at the time of last follow up (last_fup).

    Time to progression (TTP) is computed as time from start_date to
    prog_date. Time of patients who did not experienced the event (missing
    prog_date) is censored at the time of last follow up (last_fup) or death
    (death_date) whichever comes first.

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
    >>> import pandas as pd
    >>> from pylbmisc.dm import to_date
    >>> df = pd.DataFrame({
    ...    "start_date" : to_date(["1900-01-01", "1900-01-01", "1900-01-01",
    ...                            "1900-01-01", pd.NA, "1900-01-01",
    ...                            "1900-04-01", pd.NA]),
    ...    "prog_date"  : to_date(["1900-03-01", "1900-03-01", pd.NA,
    ...                            pd.NA, pd.NA, pd.NA, "1900-02-01", pd.NA]),
    ...    "death_date" : to_date(["1900-06-01",  pd.NA, "1900-06-01",
    ...                            pd.NA, pd.NA, pd.NA, "1900-06-01", pd.NA]),
    ...    "last_fup"   : to_date(["1900-06-01", "1900-12-31", "1900-06-01",
    ...                            "1900-12-31", "1900-12-31", pd.NA,
    ...                            "1900-06-01", pd.NA])
    ... })
    >>> print(df)
      start_date  prog_date death_date   last_fup
    0 1900-01-01 1900-03-01 1900-06-01 1900-06-01
    1 1900-01-01 1900-03-01        NaT 1900-12-31
    2 1900-01-01        NaT 1900-06-01 1900-06-01
    3 1900-01-01        NaT        NaT 1900-12-31
    4        NaT        NaT        NaT 1900-12-31
    5 1900-01-01        NaT        NaT        NaT
    6 1900-04-01 1900-02-01 1900-06-01 1900-06-01
    7        NaT        NaT        NaT        NaT
    >>> tteep(df.start_date, df.prog_date, df.death_date, df.last_fup,
    ...       verbose=False)
       os_status  os_time  pfs_status  pfs_time  ttp_status  ttp_time
    0          1    151.0           1      59.0           1      59.0
    1          0    364.0           1      59.0           1      59.0
    2          1    151.0           1     151.0           0     151.0
    3          0    364.0           0     364.0           0     364.0
    4       <NA>      NaN        <NA>       NaN        <NA>       NaN
    5       <NA>      NaN        <NA>       NaN        <NA>       NaN
    6          1     61.0        <NA>       NaN        <NA>       NaN
    7       <NA>      NaN        <NA>       NaN        <NA>       NaN

    Reference
    ----------
    Guidance for Industry, Clinical Trial Endpoints for the approval of cancer
    drugs and biologics, FDA, May 2007

    """

    _date_check(x=start_date, name="start_date", can_be_none=False)
    _date_check(x=last_fup, name="last_fup", can_be_none=False)
    _date_check(x=prog_date, name="prog_date", can_be_none=True)
    _date_check(x=death_date, name="death_date", can_be_none=True)

    n = len(start_date)

    # Create indicator variables based on dates
    prog = (~prog_date.isna()) if (prog_date is not None) \
        else _pd.Series([_pd.NA] * n)
    death = (~death_date.isna()) if (death_date is not None) \
        else _pd.Series([_pd.NA] * n)

    # dates dataframe for checks and other
    all_dates = _pd.DataFrame({
        "start_date": start_date,
        "prog_date": prog_date,
        "death_date": death_date,
        "last_fup": last_fup
    })

    # Check sequential dates
    if verbose:
        _check_sequential_dates(all_dates)

    rval = {}
    if "os" in ep:
        os_status = _to_integer(death)
        os_last_date = _np.where(os_status, death_date, last_fup)
        os_time = (os_last_date - start_date).dt.days
        os_status[os_time.isna()] = _pd.NA
        s, t = _check_negative_times(os_status, os_time,
                                     "OS", verbose=verbose)
        rval["os_status"] = s
        rval["os_time"] = t

    if "pfs" in ep:
        pfs_status = _to_integer(death | prog)
        min_prog_death = _pd.concat([death_date, prog_date], axis=1).min(axis=1)
        pfs_last_date = _np.where(pfs_status, min_prog_death, last_fup)
        pfs_time = (pfs_last_date - start_date).dt.days
        pfs_status[pfs_time.isna()] = _pd.NA
        s, t = _check_negative_times(pfs_status, pfs_time,
                                     "PFS", verbose=verbose)
        rval["pfs_status"] = s
        rval["pfs_time"] = t

    if "ttp" in ep:
        ttp_status = _to_integer(prog)
        min_death_lfup = _pd.concat([death_date, last_fup], axis=1).min(axis=1)
        ttp_last_date = _np.where(ttp_status, prog_date, min_death_lfup)
        ttp_time = (ttp_last_date - start_date).dt.days
        ttp_status[ttp_time.isna()] = _pd.NA
        s, t = _check_negative_times(ttp_status, ttp_time,
                                     "TTP", verbose=verbose)
        rval["ttp_status"] = s
        rval["ttp_time"] = t

    return _pd.DataFrame(rval)


def coxph(df, time, status, formula, **kwargs):
    """ Fit a Cox proportional hazard model.

    Fit a Cox proportional hazard model, with check for proportionality
    assumption using Schoenfeld's residuals.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with variables
    time: chr
         variable name for time in df
    status: chr
         variable name for status in df
    formula: chr
         formula as per lifelines' CoxPHFitter
    kwargs: dict
         other parameters passed to CoxPHFitter.fit

    Returns
    -------
    mod: pd.DataFrame
         DataFrame with the estimated model's HR, ci and pretty printed p-values.

    """
    cph = _CoxPHFitter()
    cph.fit(df=df,
            duration_col=time,
            event_col=status,
            formula=formula,
            **kwargs)
    cols_kept = ['exp(coef)', 'exp(coef) lower 95%', 'exp(coef) upper 95%', 'p']
    mod = cph.summary[cols_kept]
    mod.columns = ["HR", "Low 95%CI", "Up 95%CI", "p"]
    mod["p"] = _p_format(mod["p"])
    # schoenfeld ph test
    cph.check_assumptions(df,
                          advice=False,
                          # p_value_threshold=0.05, # by default at 0.01
                          show_plots=False)
    # returning
    return mod


def median_fup(time, status, group=None):
    r"""
    Calculate median follow up using reverse Kaplan-Meier method

    Parameters
    ----------
    time: pd.Series only?
        the time variable
    status: pd.Series only?
        the status variable (eg os_status)
    group: None or categorical
        groups to calculate stratified medians

    References
    ----------
    Schemper, Michael, and Terry L. Smith. “A Note on Quantifying Follow-up in
    Studies of Failure Time.” Controlled Clinica Trials 17, no. 4 (1996):
    343–46. https://doi.org/10.1016/0197-2456(96)00075-X

    Examples
    --------
    >>> import pylbmisc as lb
    >>> ov = lb.datasets.load("ovarian.csv")
    >>> median_fup(time=ov.survtime/365.25, status=ov.surv)
       Quantile  Estimate     Lower      Upper
    0       0.5  9.604381  9.029432  10.110883
    >>> ov["group"] = lb.dm.to_categorical(ov.histo_cl)
    >>> median_fup(time=ov.survtime/365.25, status=ov.surv, group=ov.group)
            Group  Quantile  Estimate     Lower      Upper
    0      serous       0.5  9.637235  9.029432  10.234086
    0  not serous       0.5  9.366188  8.295688  10.390144
    """
    km_res = km(
        time=time,
        status=1-status,
        group=group,
        plot=False,
        quantiles=[0.5]
    )
    return km_res["quantiles"]


def censor_at(time, status, censoring_time, name_prefix=""):
    r"""Censor observation at a given time

    Parameters
    ----------
    time: pd.Series
        time variable
    status: pd.Series
        status variable
    censoring_time: int
        integer where to censor
    name_prefix: char
        string to prefixto the outputted dataset (eg "os_")

    Examples
    --------
    >>> import pylbmisc as lb
    >>> ov = lb.datasets.load("ovarian.csv")
    >>> pd.concat([
    >>>    ov[["survtime","surv"]],
    >>>    censor_at(time=ov.survtime, status=ov.surv, censoring_time=500)
    >>> ], axis=1)
    >>>
    >>> time = pd.Series([100, 150, 200])
    >>> timena = pd.Series([100, 150, np.nan])
    >>> status = pd.Series([1, 0, 0])
    >>> statusna = pd.Series([0, 1, np.nan])
    >>> censor_at(time, statusna, 120)
    >>> censor_at(timena, status, 120)
    """
    to_censor = time > censoring_time
    time_censored = _np.where(to_censor, censoring_time, time)
    status_censored = _np.where(
        to_censor,
        _np.where(_pd.isna(status), _pd.NA, 0),
        status)
    time_varname = f"{name_prefix}time_cens{censoring_time}"
    status_varname = f"{name_prefix}status_cens{censoring_time}"
    rval = _pd.DataFrame({
        time_varname: time_censored,
        status_varname: _to_integer(status_censored)
    })
    return rval


if __name__ == "__main__":
    import doctest
    doctest.testmod()
