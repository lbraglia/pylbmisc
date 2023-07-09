import argparse
import csv
import genanki
import re
import sys

from dataclasses import dataclass
from pathlib import Path

# -----------
# latex stuff
# -----------

latex_packages = r"""\usepackage[T1]{fontenc}
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
"""

latex_preamble = r"\documentclass[avery5371, grid]{flashcards}" + latex_packages + r"\begin{document}"
latex_ending = r"\end{document}"

# ----------
# anki stuff
# ----------

# Aggiunta di preamboli latex custom

# To use the package with Anki, click "Add" in the main window, then
# click the note type selection button. Click the "Manage" button,
# then select the note type you plan to use and click "Options". The
# LaTeX header and footer are shown. The header will look something
# like:

# \documentclass[12pt]{article}
# \special{papersize=3in,5in}
# \usepackage{amssymb,amsmath}
# \pagestyle{empty}
# \setlength{\parindent}{0in}
# \begin{document}

# To use chemtex, you’d add the usepackage line in the earlier example, so it looks like:

# \documentclass[12pt]{article}
# \special{papersize=3in,5in}
# \usepackage{amssymb,amsmath}
# \usepackage{chemtex}
# \pagestyle{empty}
# \setlength{\parindent}{0in}
# \begin{document}

# After that, you should be able to include lines like the following in your Anki cards:

# Per quanto riguarda le API di genanki per creare il modello di carta fare riferimento a

# https://github.com/kerrickstaley/genanki/blob/master/genanki/model.py
anki_latex_preamble = "\\documentclass[12pt]{article}\n" + latex_packages + "\\begin{document}"
model_id = 1607392319
deck_id = 2059400110
card_model_name = 'model_with_my_latex_packages'

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
    latex_pre=anki_latex_preamble
)


@dataclass
class Card:
    s1: str = ""
    s2: str = ""

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

    def to_anki(self, add_latex_tags):
        s1 = (
            "[latex] {} [/latex]".format(self.s1)
            if add_latex_tags
            else self.s1
        )
        s2 = (
            "[latex] {} [/latex]".format(self.s2)
            if add_latex_tags
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
                self.__fc.append(Card(row[0], row[1]))

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
                self.__fc.append(Card(side1, content))

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
            print(latex_preamble, file=f)
            for card in self.__fc:
                print(card.to_tex(), "\n", file=f)
            print(latex_ending, file=f)
        print("All done, now run:\n\t pdflatex " + str(path))

    def to_anki(self, path: str | Path | None, deck_name: str | None, add_latex_tags: bool):
        """Export to anki"""
        if deck_name is None:
            deck_name = "test"
        if path is None:
            path = Path("/tmp/flashcards.apkg")
        else:
            path = Path(path)
        deck = genanki.Deck(deck_id, deck_name)
        for card in self.__fc:
            elem = card.to_anki(add_latex_tags=add_latex_tags)
            note = genanki.Note(model=card_model, fields=[elem[0], elem[1]])
            deck.add_note(note)
        genanki.Package(deck).write_to_file(path)

    def export(self, outfile: str | Path, infile_ext: str):
        outfile = Path(outfile)
        ext = outfile.suffix
        if ext == '.csv':
            self.to_csv(path=outfile)
        if ext == '.tex':
            self.to_tex(path=outfile)
        if ext == '.apkg':
            add_latex_tags = True if infile_ext == '.tex' else False
            self.to_anki(path=outfile, deck_name=outfile.stem, add_latex_tags=add_latex_tags)


def flashcards():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("outfile")
    args = parser.parse_args()
    infile = Path(args.infile).resolve()
    infile_ext = infile.suffix
    outfile = Path(args.outfile).resolve()
    if not infile.exists():
        raise FileNotFoundError(str(infile) + " does not exists.")
    fc = Flashcards(infile)
    fc.export(outfile, infile_ext)

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
