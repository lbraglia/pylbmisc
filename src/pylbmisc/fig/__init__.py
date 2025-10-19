import matplotlib.pyplot as _plt
import numpy as _np
import pandas as _pd
from collections.abc import Callable as _Callable
from pathlib import Path as _Path
from matplotlib.figure import Figure as _Figure
from matplotlib.axes import Axes as _Axes
from typing import Optional as _Optional
from typing import Tuple as _Tuple
from pylbmisc.stats import p_format as _p_format


def fun2d(f: _Callable = lambda x: x**2,
          xlim: list[int | float] = [-5, 5],
          ylim: _Optional[list[int | float]] = None,
          npoints: int = 1000,
          show: bool = True,
          save: _Optional[str | _Path] = None,
          fig: _Optional[_Figure] = None,
          ax: _Optional[_Axes] = None
          ) -> _Tuple[_Figure, _Axes]:
    """Plot a 2d function

    Parameters
    ----------
    f : Callable
        function to be applied to x
    xlim: list[int | float]
        range of x
    ylim: list[int | float] | None
        range of y plotted
    npoints: int
        number of points to plot
    show: bool
        plot at the end of figure composition
    fig: matplotlib.figure.Figure | None
        fig used for plotting or if None a new will be created
    ax: matplotlib.axes.Axes | None
        ax used for plotting or if None a new will be created

    Returns
    -------
    fig: matplotlib.figure.Figure
        fig used for plotting
    ax: matplotlib.axes.Axes
        ax used for plotting

    Examples
    --------
    >>> fig, ax = fun2d()

    """
    if (ax is None) or (fig is None):
        fig, ax = _plt.subplots()
    x = _np.linspace(start=xlim[0], stop=xlim[1], num=npoints)
    npf = _np.frompyfunc(f, 1, 1)
    y = npf(x)
    ax.plot(x, y)
    if ylim is not None:
        ax.set_ylim(bottom=ylim[0], top=ylim[1])
    if show:
        _plt.show(block=False)
    if save is not None:
        fig.savefig(save)
    return fig, ax


def fun3d(f: _Callable = lambda x, y: x**2 + y**2,
          xlim: list[int | float] = [-5, 5],
          ylim: list[int | float] = [-5, 5],
          zlim: _Optional[list[int | float]] = None,
          npoints: int = 100,
          show: bool = True,
          save: _Optional[str | _Path] = None,
          fig: _Optional[_Figure] = None,
          ax: _Optional[_Axes] = None
          ) -> _Tuple[_Figure, _Axes]:
    """Plot a 2d function

    Parameters
    ----------
    f : Callable
        function to be applied to x
    xlim: list[int | float]
        range of x
    ylim: list[int | float]
        range of y
    zlim: list[int | float] | None
        range of z plotted
    npoints: int
        number of points to plot
    show: bool
        plot at the end of figure composition
    fig: matplotlib.figure.Figure | None
        fig used for plotting or if None a new will be created
    ax: matplotlib.axes.Axes | None
        ax used for plotting or if None a new will be created

    Returns
    -------
    fig: matplotlib.figure.Figure
        fig used for plotting
    ax: matplotlib.axes.Axes
        ax used for plotting

    Examples
    --------
    >>> fig, ax = fun3d()

    """
    if (ax is None) or (fig is None):
        fig, ax = _plt.subplots(subplot_kw={"projection": "3d"})
    x = _np.arange(start=xlim[0],
                   stop=xlim[1],
                   step=(xlim[1] - xlim[0])/(npoints - 1))
    y = _np.arange(start=ylim[0],
                   stop=ylim[1],
                   step=(ylim[1] - ylim[0])/(npoints - 1))
    x, y = _np.meshgrid(x, y)
    npf = _np.frompyfunc(f, nin=2, nout=1)
    z = npf(x, y)
    ax.plot_surface(x, y, z)
    if zlim is not None:
        ax.set_zlim(bottom=zlim[0], top=zlim[1])
    if show:
        _plt.show(block=False)
    if save is not None:
        fig.savefig(save)
    return fig, ax


def forestplot(
    df,
    variable_col="variable",
    group_col="group",
    est_col="HR",
    ll_col="lower.95",
    hl_col="upper.95",
    n_col="n",
    pval_col="p",
    ci_digits=2,
    fontfamily="DejaVu Sans",
    fontsize=15,
    forest_xlim=(10**(-1.5), 10**1.5),
    log_scale=True,
    xlabel="Hazard ratios",
    forest_title="Overall survival",
    refline=1,
    refline_color="red",
    refline_style="--",
    dot_color="black",
    ci_color="black",
    row_height=0.55
):
    """
    Examples
    --------
    >>> import pylbmisc as lb
    >>> fig, ax = fun3d()
    >>> import numpy as np
    >>> nan = np.nan
    >>> inf = np.inf
    >>> os_flat = pd.DataFrame({'HR': [1.0, 0.8078596501254128, 1.0, 0.9276629617388676, 1.083148102276055,
    >>>         1.410879356833972, 1.0, 0.9132984204206765, 0.690306667065486,
    >>>         3.619033273498864, 1.0, 1.182346896367745, 1.928877100106704, 1.0,
    >>>         0.2495388668068113, 0.7802993699197853, 4.819819623454819e-07,
    >>>         5.618010353736118, 1.0, 2.761579895556096, 1.0, 2.251540997105791, 1.0,
    >>>         0.6317149418796589, 1.391470021361166, 1.0, 2.450908443888874,
    >>>         1.845714125925274, 2.734585278092313, 1.0, 3.566961223209396, 1.0,
    >>>         7.047547494513447, 2.686379735217062, 6.034625373539202,
    >>>         3.693700054306441],
    >>>  'group': ['male', 'female', '(48.3, 65.3]', '(65.3, 71.9]', '(71.9, 76.4]',
    >>>            '(76.4, 85.9]', 'IgG', 'IgA', 'LC', 'Other', '1', '2', '3+', 'Rd',
    >>>            'VTd', 'Vd', 'VMP', 'Pd', 'no HiR features', 'HiR features', 'no',
    >>>            'yes', '0', '1-2', '3', '(0.8, 4.4]', '(4.4, 5.3]', '(5.3, 7.8]',
    >>>            '(7.8, 30.0]', '1-2', '3', 'SR', 'Non-1q HiRCAs', '+1q',
    >>>            '+1q+HiRCAs', None],
    >>>  'lower.95': [nan, 0.459753262045847, nan, 0.4080223189097797,
    >>>               0.4752521515046189, 0.6322469140653059, nan, 0.4310621390173041,
    >>>               0.3021957023990133, 1.091776016753074, nan, 0.5941364676239838,
    >>>               0.8447511914413539, nan, 0.03396574783737238, 0.3273138267395636,
    >>>               0.0, 2.16272156649981, nan, 1.314557817871279, nan,
    >>>               1.269892148793646, nan, 0.1751051111892889, 0.5327921539120398,
    >>>               nan, 0.5733200703278137, 0.4127226251463592, 0.7003493239886236,
    >>>               nan, 1.71806312084743, nan, 1.979165276456984, 0.7205870869270733,
    >>>               1.797006366220221, 1.285899707849024],
    >>>  'n': [88, 86, 44, 43, 43, 44, 101, 40, 28, 5, 80, 73, 21, 125, 21, 19, 2, 7,
    >>>        154, 20, 120, 54, 27, 29, 54, 26, 16, 19, 20, 97, 35, 43, 11, 18, 20,
    >>>        82],
    >>>  'p': [nan, 0.4581654702047059, nan, 0.8577977636500718, 0.8492832620467534,
    >>>        0.4006380332916023, nan, 0.8128508979186799, 0.3792091009044879,
    >>>        0.035416084331664, nan, 0.6333101510801474, 0.1188861421310271, nan,
    >>>        0.1724836065789395, 0.5757003918594448, 0.9957899407164232,
    >>>        0.0003945510104673111, nan, 0.007315940715285618, nan,
    >>>        0.005474671508132051, nan, 0.4829015839460461, 0.50000305574803, nan,
    >>>        0.226496794047904, 0.4225825089461596, 0.1477644150842377, nan,
    >>>        0.000644908637339989, nan, 0.00258237442308853, 0.1410526685080054,
    >>>        0.003634264049804077, 0.01522236870908805],
    >>>  'upper.95': [nan, 1.419537974339969, nan, 2.109096808433195, 2.468604945290432,
    >>>               3.14842273684017, nan, 1.935020335222294, 1.576869858876642,
    >>>               11.9964183437949, nan, 2.352900822501218, 4.40433456029561, nan,
    >>>               1.833307081751119, 1.86019366417318, inf, 14.59366791526791, nan,
    >>>               5.801436358188687, nan, 3.992021579520693, nan, 2.278995542069771,
    >>>               3.63404154158489, nan, 10.47748458708434, 8.254116510894042,
    >>>               10.67746678267756, nan, 7.405555834062594, nan, 25.09539060645614,
    >>>               10.01493950239945, 20.26520555715178, 10.61001881243547],
    >>>  'variable': ['Sex', nan, 'Age', nan, nan, nan, 'Paraprotein', nan, nan, nan,
    >>>               'Line of therapy', nan, nan, 'Daratumumab combination', nan, nan,
    >>>               nan, nan, 'HiR clinical features', nan, 'Renal insufficiency',
    >>>               nan, 'PET/CT lesions', nan, nan, 'PET/CT SUVmax', nan, nan, nan,
    >>>               'ISS stage', nan, 'Cytogenetic status', nan, nan, nan, nan]})
    >>>
    >>>
    >>> fp_os = lb.fig.forestplot(os_flat, forest_title = "OS")
    >>> lb.io.export_figure(fp_os, fdir="/tmp",fname = "fp_os")
    """
    # breakpoint()
    df = df.copy()
    n_rows = len(df)
    # replace NA with string NA for groups of blank for variables
    df.loc[df[variable_col].isna(), variable_col] = ""
    df.loc[df[group_col].isna(), group_col] = "<NA>"
    # graph parameters
    len_longest_variable = df[variable_col].str.len().max()
    variable_col_width = 0.19 * len_longest_variable
    len_longest_group = df[group_col].str.len().max()
    group_col_width = 0.19 * len_longest_group
    n_col_width = 1.3
    ci_col_width = 2.5
    pval_col_width = 1.4
    forest_col_width = 5
    width_ratios = [variable_col_width, group_col_width, n_col_width,
                    ci_col_width, pval_col_width, forest_col_width]
    fig_width = sum(width_ratios) + 1
    fig_height = row_height * n_rows + 1.5

    def ci_format(row):
        est = row[est_col]
        ll = row[ll_col]
        hl = row[hl_col]
        if _pd.isna(ll) and _pd.isna(hl):  # reference group with lower and upper
            rval = f"{est:.{ci_digits}f}"
        else:
            rval = f"{est:.{ci_digits}f} ({ll:.{ci_digits}f}-{hl:.{ci_digits}f})"
        return rval
    ci_texts = df.apply(ci_format, axis=1)
    pval_texts = _p_format(df[pval_col])
    n_texts = df[n_col].astype(int).astype(str)

    # figure setup
    fig = _plt.figure(figsize=(fig_width, fig_height))
    gs = fig.add_gridspec(1, 6, width_ratios=width_ratios, wspace=0.1)
    ax_variables = fig.add_subplot(gs[0, 0])
    ax_groups = fig.add_subplot(gs[0, 1], sharey=ax_variables)
    ax_n = fig.add_subplot(gs[0, 2], sharey=ax_variables)
    ax_ci = fig.add_subplot(gs[0, 3], sharey=ax_variables)
    ax_pval = fig.add_subplot(gs[0, 4], sharey=ax_variables)
    ax_forest = fig.add_subplot(gs[0, 5], sharey=ax_variables)
    yticks = _np.arange(n_rows)

    # axes without ticks (first/textual ones)
    for ax in [ax_variables, ax_groups, ax_n, ax_ci, ax_pval]:
        ax.set_yticks([])
        ax.set_xticks([])
        ax.tick_params(left=False, right=False, top=False, bottom=False)
        ax.spines[:].set_visible(False)

    # variable column
    ax_variables.set_ylim(-0.5, n_rows - 0.5)
    ax_variables.set_xlim(0, 1)
    ax_variables.invert_yaxis()
    ax_variables.set_title("Variables", fontsize=fontsize, pad=12, fontfamily=fontfamily, fontweight="bold", loc="left")
    for y, val in enumerate(df[variable_col]):
        ax_variables.text(0, y, str(val), fontfamily=fontfamily, fontsize=fontsize, va="center", ha="left")

    # groups column
    ax_groups.set_ylim(ax_variables.get_ylim())
    ax_groups.set_xlim(0, 1)
    ax_groups.set_title("Groups", fontsize=fontsize, pad=12, fontfamily=fontfamily, fontweight="bold", loc="left")
    for y, val in enumerate(df[group_col]):
        ax_groups.text(0, y, str(val), fontfamily=fontfamily, fontsize=fontsize, va="center", ha="left")

    # n column
    ax_n.set_ylim(ax_variables.get_ylim())
    ax_n.set_xlim(0, 1)
    ax_n.set_title("n", fontsize=fontsize, pad=12, fontfamily=fontfamily, fontweight="bold", loc="center")
    for y, val in enumerate(n_texts):
        ax_n.text(0.5, y, val, fontfamily=fontfamily, fontsize=fontsize, va="center", ha="center")

    # CI column
    ax_ci.set_ylim(ax_variables.get_ylim())
    ax_ci.set_xlim(0, 1)
    ax_ci.set_title("Est (CI)", fontsize=fontsize, pad=12, fontfamily=fontfamily, fontweight="bold",loc="left")
    for y, val in enumerate(ci_texts):
        ax_ci.text(0, y, val, fontfamily=fontfamily, fontsize=fontsize, va="center", ha="left")

    # pvalue column
    ax_pval.set_ylim(ax_variables.get_ylim())
    ax_pval.set_xlim(0, 1)
    ax_pval.set_title("p", fontsize=fontsize, pad=12, fontfamily=fontfamily, fontweight="bold", loc="right")
    for y, val in enumerate(pval_texts):
        ax_pval.text(1, y, val, fontfamily=fontfamily, fontsize=fontsize, va="center", ha="right")

    # forestplot column
    ax_forest.set_ylim(ax_variables.get_ylim())
    ax_forest.set_yticks(yticks)
    ax_forest.set_yticklabels([])
    if forest_title != "":
        ax_forest.set_title(forest_title, fontsize=fontsize, pad=12, fontfamily=fontfamily, fontweight="bold", loc="center")
    for y, (_, row) in enumerate(df.iterrows()):
        est = row[est_col]
        ll = row[ll_col]
        hl = row[hl_col]
        # confidence interval line plotting
        # print CI only if CI is actually available (and estimate is not 0)
        if isinstance(ll, float) and isinstance(hl, float):
            ax_forest.plot([ll, hl], [y, y], color=ci_color, lw=2.3, zorder=1)
        if est > 0.000001 and abs(est-1) > 0.000001:  # do not print 0 or 1
            ax_forest.plot(est, y, "o", color=dot_color, markersize=9, zorder=2)
        ax_forest.set_xlim(*forest_xlim)
        if log_scale:
            ax_forest.set_xscale('log')  # base 10
            # ax_forest.set_xscale('log', base=2)

    ax_forest.axvline(refline, color=refline_color, ls=refline_style, lw=2, zorder=0)
    ax_forest.tick_params(axis="y", left=False, right=False, labelleft=False)
    ax_forest.tick_params(axis="x", labelsize=fontsize - 2)
    ax_forest.set_xlabel(xlabel, fontsize=fontsize + 1, fontfamily=fontfamily)

    ax_forest.spines["left"].set_visible(False)
    ax_forest.spines["right"].set_visible(False)
    ax_forest.grid(axis="x", linestyle=":", alpha=0.7)
    fig.align_ylabels([ax_variables, ax_groups, ax_n, ax_ci, ax_pval, ax_forest])
    return fig
