def save(fig, base_path,
         scale = 1, caption = "", label = ""):
    """
    Save to png, eps and pdf and include in Latex an image; intended to be used inside pythontex pycode

    fig: a matplotlib fig
    base_path: the path (without extension) to be used
    scale: LaTeX includegraphics scale
    caption: LaTeX caption
    label: LaTeX label
    """
    # save figures to hard drive
    eps_path =  base_path + ".eps"
    png_path =  base_path + ".png"
    pdf_path =  base_path + ".pdf"
    fig.savefig(eps_path)
    fig.savefig(png_path, dpi = 600)
    fig.savefig(pdf_path)
    # latex include
    latex = "\\begin{figure} \\centering \\includegraphics[scale=%(scale).2f]{%(base_path)s} \\caption{%(caption)s} \\label{%(label)s} \\end{figure}"
    subs = {"scale" : scale, "base_path" : base_path , "caption" : caption, "label" : label}
    print(latex % subs)
