import pandas as _pd
import matplotlib.pyplot as _plt
from pylbmisc.stats import p_format as _p_format
from lifelines import KaplanMeierFitter as _KaplanMeierFitter
from lifelines.plotting import add_at_risk_counts as _add_at_risk_counts
from lifelines.statistics import multivariate_logrank_test as _multivariate_logrank_test
from lifelines.utils import qth_survival_times as _qth_survival_times
from warnings import warn as _warn


def _estquant(fit, quantiles):
    "Return estimates and quantiles of survival function with confidence intervals"
    estimates = _pd.concat([fit.survival_function_,
                           fit.confidence_interval_],
                          axis = 'columns')
    quant = _qth_survival_times(quantiles, estimates)
    quant = quant.reset_index()
    quant.columns = ["Quantile", "Estimate", "Lower", "Upper"]
    estimates = estimates.reset_index() # take time as variable
    estimates.columns = ["time", "Estimate", "Lower", "Upper"]
    return estimates, quant


def km(time, status, group = None,
       plot = True,
       ylab = "Survival probability",
       xlab = "Time",
       counts = ["Events"],
       xticks = None,
       ci_alpha = 0.3,
       quantiles = [0.5],
       plot_logrank = True):
    """Kaplan-Meier estimates and logrank test

Parameters
----------    
    time: time
    status: dichotomic
    group: categorical variable
    ylab: ylab
    xlab: xlab
    counts: a list containing ["At risk", "Events", "Censored"]
    xticks: slice used for plotting (loc) eg slice(5) plots up to time = 5
    ci_alpha: confidence interval alpha shading (set to 0 for no CI)
    quantiles: list[float] a list of quantiles by default [0.5], eg the median
    add_logrank: bool = True
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
