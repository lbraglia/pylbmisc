import matplotlib.pyplot as _plt
import numpy as _np
from collections.abc import Callable as _Callable
from pathlib import Path as _Path
from matplotlib.figure import Figure as _Figure
from matplotlib.axes import Axes as _Axes
from typing import Optional as _Optional
from typing import Tuple as _Tuple


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
