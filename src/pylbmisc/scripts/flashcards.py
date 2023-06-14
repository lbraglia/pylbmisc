import argparse
import csv
import re
import sys

from pathlib import Path
# from ..utils import argparser

preamble = r"""\documentclass[avery5371, grid]{flashcards}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[english, italian]{babel}
\usepackage{minitoc}
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

ending = r"\end{document}"


def flash(s1, s2):
    res = (
        (r"\begin{flashcard}{%s}" % s1)
        + "   "
        + s2
        + "   "
        + r"\end{flashcard}"
    )
    return res




class Flashcards(object):

    def __init__(
            self,
            path: str | Path,
            latex_envirs: list[str] = ["defn", "thm", "proof", "es"]
    ):

        # initialization: flashcards list (lista di tuple) e regex per gli env
        # latex
        self.__fc = []
        paste = "|".join(latex_envirs)
        fmt = (paste, paste)
        self.__env_re = re.compile(r"\\begin{(%s)}(\[.+?\])?(.+?)\\end{(%s)}" % fmt)
        # load data from files given in the path
        path = Path(path)
        if path.is_dir():
            files = [f for f in path.iterdir()
                     if ((f.suffix in ('.tex', '.Rnw', '.csv'))
                         and f.name != "_region_.tex")]
        else:
            files = [path]
        for f in files:
            if f.suffix in ('.tex', '.Rnw'):
                self.add_from_tex(f)
            elif f.suffix == '.csv':
                self.add_from_csv(f)

        
    def add_from_tex(
            self,
            path: str|Path,
    ) -> None:
        path = Path(path)
        # import as list of tuples
        with path.open() as t:
            tmp = t.readlines()
            # rm commented stuff and join
            tmp = [l for l in tmp if not l.lstrip().startswith("%")]
            tmp = " ".join(tmp)
            # remove newline and duplicate spaces
            tmp = tmp.replace("\n", "")
            tmp = re.sub(r"\\label{.+?}", "", tmp)
            tmp = re.sub("\s+", " ", tmp)
            matches = self.__env_re.findall(tmp)
            for match in matches:
                if len(match) == 3: # no [] for the environment, only content
                    side1 = "[{0}]".format(match[0]) # name of the environment
                    content = match[1]
                elif len(match) == 4: # both [] and environment content
                    rm_paren = match[1].replace("[", "").replace("]", "")
                    side1 = "[{0}]".format(match[0])  + " " + rm_paren
                    content = match[2]
                self.__fc.append((side1, content))


    def add_from_csv(
            self,
            path: str|Path
    ) -> None:
        path = Path(path)
        with path.open() as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.__fc.append((row[0], row[1]))


    def to_tex(
            self,
            path: str|Path
    ) -> None:
        if path is None:
            path = Path("/tmp/flashcards.tex")
        else:
            path = Path(path)
        with path.open(mode="w") as f:
            print(preamble, file=f)
            for elem in self.__fc:
                print(flash(elem[0], elem[1]), "\n", file=f)
            print(ending, file=f)
        print("All done, now run:\n\t pdflatex " + str(path))


    def to_csv(
            self,
            path: str|Path
    ) -> None:
        '''Export to a csv'''
        if path is None:
            path = Path("/tmp/flashcards.csv")
        else:
            path = Path(path)
        with path.open(mode='w') as f:
            dataset = csv.writer(f,
                                 delimiter = ';',
                                 quotechar = '"',
                                 quoting = csv.QUOTE_NONNUMERIC)
            for x in self.__fc:
                dataset.writerow(x)
        print("All done, exported to: " + str(path))

    
def flashcards2tex():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        raise FileNotFoundError(str(path) + " does not exists.")
    fc = Flashcards(path)
    fc.to_tex("/tmp/flashcards.tex")

def flashcards2csv():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        raise FileNotFoundError(str(path) + " does not exists.")
    fc = Flashcards(path)
    fc.to_csv("/tmp/flashcards.csv")
    
