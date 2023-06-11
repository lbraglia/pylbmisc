import argparse
import csv
from pathlib import Path

# from ..utils import argparser

preamble = r"\documentclass[avery5371, grid]{flashcards} \begin{document}"
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


def main():
    '''A csv 2 latex flashcard creator'''

    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    args = parser.parse_args()

    # arguments checking
    infile = Path(args.infile)
    if not infile.exists():
        raise FileNotFoundError(str(infile) + " does not exists.")

    # gogogo
    outfile = infile.with_suffix('.tex')
    with open(outfile, mode="w") as out:
        print(preamble, file=out)
        with open(infile) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                print(flash(row[0], row[1]), "\n", file=out)
        print(ending, file=out)

    print("All done, now run:\n\t pdflatex " + str(outfile))
    return
