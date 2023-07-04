import argparse
import csv
import genanki
import re
import sys

from dataclasses import dataclass
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


# anki stuff
# ----------
model_id = 1607392319
deck_id = 2059400110
card_model_name = 'card_model_test'
card_model = genanki.Model(
    model_id,
    card_model_name,
    fields=[
        {'name': 'Domanda'},
        {'name': 'Risposta'},
    ],
    templates=[
        {
            'name': 'Card 1',
            'qfmt': '{{Domanda}}',
            'afmt': '{{Risposta}}',
        },
    ],
)


@dataclass
class Card:
    s1: str = ""
    s2: str = ""
    source: str = ""

    def to_tex(self) -> None:
        return (
            (r"\begin{flashcard}{%s}" % self.s1)
            + "   "
            + self.s2
            + "   "
            + r"\end{flashcard}"
        )

    def to_csv(self) -> tuple:
        return (self.s1, self.s2)

    def to_anki(self):
        s1 = (
            "[latex] {} [/latex]".format(self.s1)
            if self.source == 'tex'
            else self.s1
        )
        s2 = (
            "[latex] {} [/latex]".format(self.s2)
            if self.source == 'tex'
            else self.s2
        )
        return (s1, s2)


class Flashcards(object):
    def __init__(
        self,
        path: str | Path,
        latex_envirs: list[str] = ["defn", "thm", "proof", "es"],
    ):
        # initialization: flashcards list (lista di tuple) e regex per
        # gli env latex
        self.__fc = []
        paste = "|".join(latex_envirs)
        fmt = (paste, paste)
        self.__env_re = re.compile(
            r"\\begin{(%s)}(\[.+?\])?(.+?)\\end{(%s)}" % fmt
        )
        # load data from files given in the path
        path = Path(path)
        if path.is_dir():
            files = [
                f
                for f in path.iterdir()
                if (
                    (f.suffix in ('.tex', '.Rnw', '.csv'))
                    and f.name != "_region_.tex"
                )
            ]
        else:
            files = [path]
        for f in files:
            if f.suffix in ('.tex', '.Rnw'):
                self.add_from_tex(f)
            elif f.suffix == '.csv':
                self.add_from_csv(f)

    def add_from_csv(self, path: str | Path) -> None:
        path = Path(path)
        with path.open() as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                self.__fc.append(Card(row[0], row[1], 'csv'))

    def add_from_tex(self, path: str | Path) -> None:
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
                if len(match) == 3:  # no [] for the environment, only content
                    side1 = "[{0}]".format(match[0])  # name of the environment
                    content = match[1]
                elif len(match) == 4:  # both [] and environment content
                    rm_paren = match[1].replace("[", "").replace("]", "")
                    side1 = "[{0}]".format(match[0]) + " " + rm_paren
                    content = match[2]
                self.__fc.append(Card(side1, content, 'tex'))

    def to_csv(self, path: str | Path) -> None:
        '''Export to a csv'''
        if path is None:
            path = Path("/tmp/flashcards.csv")
        else:
            path = Path(path)
        with path.open(mode='w') as f:
            dataset = csv.writer(
                f, delimiter=';', quotechar='"', quoting=csv.QUOTE_NONNUMERIC
            )
            for card in self.__fc:
                dataset.writerow(card.to_csv())
        print("All done, exported to: " + str(path))

    def to_tex(self, path: str | Path) -> None:
        if path is None:
            path = Path("/tmp/flashcards.tex")
        else:
            path = Path(path)
        with path.open(mode="w") as f:
            print(preamble, file=f)
            for card in self.__fc:
                print(card.to_tex(), "\n", file=f)
            print(ending, file=f)
        print("All done, now run:\n\t pdflatex " + str(path))

    def to_anki(self, path: str | Path | None, deck_name: str | None):
        """Export to anki"""
        if deck_name is None:
            deck_name = "test"
        if path is None:
            path = Path("/tmp/flashcards.apkg")
        else:
            path = Path(path)
        deck = genanki.Deck(deck_id, deck_name)
        for card in self.__fc:
            elem = card.to_anki()
            note = genanki.Note(model=card_model, fields=[elem[0], elem[1]])
            deck.add_note(note)
        genanki.Package(deck).write_to_file(path)

    def export(self, outfile: str | Path):
        outfile = Path(outfile)
        ext = outfile.suffix
        if ext == '.csv':
            self.to_csv(path=outfile)
        if ext == '.tex':
            self.to_tex(path=outfile)
        if ext == '.apkg':
            self.to_anki(path=outfile, deck_name=outfile.stem)


def flashcards():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("outfile")
    args = parser.parse_args()
    infile = Path(args.infile).resolve()
    outfile = Path(args.outfile).resolve()
    if not infile.exists():
        raise FileNotFoundError(str(infile) + " does not exists.")
    fc = Flashcards(infile)
    fc.export(outfile)


def flashcards2csv():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        raise FileNotFoundError(str(path) + " does not exists.")
    fc = Flashcards(path)
    fc.to_csv()


def flashcards2tex():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        raise FileNotFoundError(str(path) + " does not exists.")
    fc = Flashcards(path)
    fc.to_tex()


def flashcards2anki():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        raise FileNotFoundError(str(path) + " does not exists.")
    fc = Flashcards(path)
    fc.to_anki()

    # opts = (
    #     # (param, help, default, type)
    #     # --dirs
    #     (
    #         'dirs',
    #         'str: comma separated list of exercise source directories',
    #         '~/src/pypkg/exercises/db',
    #         str,
    #     ),
    #     # --lists
    #     (
    #         'lists',
    #         'str: comma separated list of file with lists of source dir',
    #         None,
    #         str,
    #     ),
    #     # --outfile
    #     ('outfile', 'str:  sqlite3 db to save', '~/.exercises.db', str),
    # )

    # args = lb.utils.argparser(opts)
    # dirs = args['dirs']
    # dirs = dirs.split(',')
    # lists = args['lists']
    # lists = lists.split(',')
    # outfile = args['outfile']
    # print({"dirs": dirs, "lists": lists, "outfile": outfile})
