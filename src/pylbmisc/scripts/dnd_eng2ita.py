import argparse
from ..dnd import eng2ita


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("term", type=str, help="english term to translate")
    args = argparser.parse_args()
    eng = args.term
    eng2ita(eng)
