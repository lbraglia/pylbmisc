import os as _os
import tempfile as _tempfile

def save(fig,
         label = "",
         caption = "",
         fdir = "outputs",
         fname = "",
         scale = 1):
    """
    Save to png, eps and pdf and include in Latex an image; intended to be used inside pythontex pycode.

    fig: a matplotlib fig
    label: LaTeX label to be put after "fig:"
    caption: LaTeX caption, if "" a pretty version of label is set
    fdir: the directory where to save, if not existent, save in /tmp"
    fname: basename of the file to be used (otherwise, non "" label will be used or a tempfile will be created)
    scale: LaTeX includegraphics scale
    """
    # fdir not existing, using /tmp
    if not _os.path.isdir(fdir):
        fdir = '/tmp'

    # default filename to be set as label, if available or a temporary one
    if fname == "":
        if label != "":
            fname = label
        else:
            tempfile = _tempfile.mkstemp(dir = fdir)
            fname = _os.path.basename(tempfile[1])
    
    # produce the file paths
    base_path = _os.path.join(fdir, fname)
    eps_path =  base_path + ".eps"
    png_path =  base_path + ".png"
    pdf_path =  base_path + ".pdf"

    # save figures to hard drive
    fig.savefig(eps_path)
    fig.savefig(png_path)#, dpi = 600)
    fig.savefig(pdf_path)

    # latex stuff
    latex_label = 'fig:' + label
    caption = label.capitalize().replace("_", " ") if caption == "" else caption
    latex = "\\begin{figure} \\centering \\includegraphics[scale=%(scale).2f]{%(base_path)s} \\caption{%(caption)s} \\label{%(label)s} \\end{figure}"
    subs = {"scale" : scale, "base_path" : base_path ,
            "caption" : caption, "label" : latex_label}
    print(latex % subs)
