import argparse
from ..dnd import spell


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("spell", type=str, help="spell to be printed")
    args = argparser.parse_args()
    spell(args.spell)
