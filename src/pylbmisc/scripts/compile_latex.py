#!/usr/bin/env python3

import argparse
import os
import subprocess

from pathlib import Path

preamble = r"""
\usepackage[T1]{fontenc}
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
\begin{document}
"""

outro = r"\end{document}"

def worker(what):
    argparser = argparse.ArgumentParser()
    argparser.add_argument("path", type = str, help="path to a tex or a dir")
    args = argparser.parse_args()
    inpath = Path(args.path)
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
    output = r"""\documentclass{%s}""" % what + preamble + content + outro
    outdir = Path("/tmp")    
    os.chdir(outdir)
    outfile = Path("%s.tex" % what)
    with outfile.open("w") as f:
        f.write(output)
    subprocess.run(["pdflatex", outfile])


def article():
    worker("article")

def book():
    worker("book")
    
if __name__ == "__main__":
    book()
