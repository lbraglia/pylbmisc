import os as _os
import tempfile as _tempfile


def dump(
    fig,
    label: str = "",
    caption: str = "",
    fdir: str = "outputs",
    fname: str = "",
    scale: float = 1,
):
    """Dump a figure (save to file, include in LaTeX)

    Save to png, eps and pdf and include in Latex an image;
    intended to be used inside pythontex pycode.

    Args:
       fig (matplotlib.figure.Figure): the fig
       label (str): posta dopo "fig:" in LaTeX
       caption (str): caption LaTeX, se mancante viene riadattata label
       fdir (str): directory dove salvare, se mancante si usa /tmp
       fname (str): basename del file da salvare, se mancante si prova
          a riusare label oppure a creare un file temporaneo
       scale (float): scale di includegraphics di LaTeX

    Returns:
       None: nothing interesting here
    """
    # fdir not existing, using /tmp
    if not _os.path.isdir(fdir):
        fdir = '/tmp'

    # default filename to be set as label, if available or a temporary one
    if fname == "":
        if label != "":
            fname = label
        else:
            tmp = _tempfile.mkstemp(dir=fdir)
            fname = _os.path.basename(tmp[1])

    # produce the file paths
    base_path = _os.path.join(fdir, fname)
    eps_path = base_path + ".eps"
    png_path = base_path + ".png"
    pdf_path = base_path + ".pdf"

    # save figures to hard drive
    fig.savefig(eps_path)
    fig.savefig(png_path)  # , dpi = 600)
    fig.savefig(pdf_path)

    # latex stuff
    latex_label = 'fig:' + label
    caption = label.capitalize().replace("_", " ") if caption == "" else caption
    latex = (
        "\\begin{figure} \\centering "
        + "\\includegraphics[scale=%(scale).2f]{%(base_path)s}"
        + " \\caption{%(caption)s} \\label{%(label)s} \\end{figure}"
    )
    subs = {
        "scale": scale,
        "base_path": base_path,
        "caption": caption,
        "label": latex_label,
    }
    print(latex % subs)
