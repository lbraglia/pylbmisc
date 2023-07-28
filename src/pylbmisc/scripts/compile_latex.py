#!/usr/bin/env python3

import argparse
import os
import subprocess

from pathlib import Path

preamble = r"""
\setcounter{tocdepth}{3}
\setcounter{secnumdepth}{3}
\usepackage[utf8]{inputenc}
\usepackage[english, italian]{babel}
\usepackage{mypkg}
\usepackage{tikz}
\usetikzlibrary{arrows,snakes,backgrounds,calc}
\usepackage{wrapfig}
\usepackage{subfig}
\usepackage{rotating}
\usepackage{cancel}
\usepackage{hyperref}
\usepackage[usefamily=R]{pythontex}
\begin{document}
\tableofcontents
"""

outro = r"\end{document}"


def worker(what):
    argparser = argparse.ArgumentParser()
    argparser.add_argument("path", type=str, help="path to a tex or a dir")
    args = argparser.parse_args()
    inpath = Path(args.path)
    outfname = inpath.stem
    tmp = Path("/tmp")
    tmptex = Path("tmp_%s.tex" % outfname)
    tmppdf = Path("tmp_%s.pdf" % outfname)
    finalpdf = Path("%s.pdf" % outfname)
    if not inpath.exists():
        raise FileNotFoundError
    if inpath.is_dir():
        files = [f for f in list(inpath.iterdir()) if f.suffix == '.tex']
    else:
        files = [inpath]
    contents = []
    for tex in sorted(files):
        with tex.open() as f:
            contents.append(f.read())
    content = "\n".join(contents)
    full_content = (
        r"""\documentclass{%s}""" % what + preamble + content + outro
    )
    with tmptex.open("w") as f:
        f.write(full_content)
    # # here clean if there are old shit in /tmp
    # old_files = tmp / tmp_shit
    # run pdflatex with output in /tmp
    pdflatex_cmd = ["pdflatex", "-output-directory", tmp, tmptex]
    subprocess.run(pdflatex_cmd)
    # # if pythontex code file exists, run pythontex before the next pdflatex
    # pythontexcodef = tmp / tex.with_stem(".pytxcode")
    # if pythontexcodef.exists():
    #     subprocess.run(["pythontex", tmp/tex.stem])
    subprocess.run(pdflatex_cmd)
    # cleaning and renaming (removing "tmp_")
    tmptex.unlink()
    subprocess.run(["mv", tmp / tmppdf, tmp / finalpdf])
    print("""All done, open the final file with:

    okular {}
    """.format(tmp / finalpdf))


def article():
    worker("article")


def book():
    worker("book")


if __name__ == "__main__":
    book()
