import argparse
from ..dnd import ita2eng

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("term", type=str, help="italian term to translate")
    args = argparser.parse_args()
    ita = args.term
    ita2eng(ita)
