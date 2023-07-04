""" Utils for DND """
import pprint as _pprint

mesi = [
    "",
    "Hammer",  #  1
    "Alturiak",  #  2
    "Ches",  #  3
    "Tarsakh",  #  4
    "Mirtul",  #  5
    "Kythorn",  #  6
    "Flamerule",  #  7
    "Eleasis",  #  8
    "Eleint",  #  9
    "Marpenoth",  # 10
    "Uktar",  # 11
    "Nightal",  # 12
]


_dnd_cache = {}


def eng2ita(x: str):
    """Traduttore da inglese a italiano di termini dnd"""
    if "terms" not in _dnd_cache:
        print("Importing translation dictionary.")
        from .data.dnd_terms import translate_df

        _dnd_cache["terms"] = translate_df

    rows = (_dnd_cache["terms"]).eng.str.contains(x)
    sel = (_dnd_cache["terms"]).loc[rows, ["eng", "ita"]]
    print("\n", sel.to_string(index=False), "\n")


def ita2eng(x: str):
    """Traduttore da italiano a inglese di termini dnd"""
    if "terms" not in _dnd_cache:
        print("Importing dictionary.")
        from .data.dnd_terms import translate_df

        _dnd_cache["terms"] = translate_df

    rows = (_dnd_cache["terms"]).ita.str.contains(x)
    sel = (_dnd_cache["terms"]).loc[rows, ["ita", "eng"]]
    print("\n", sel.to_string(index=False), "\n")


def spell(x: str):
    """Stampa la spell in inglese"""
    if "spells" not in _dnd_cache:
        print("Importing spells data.")
        from .data.dnd_spells import spells

        _dnd_cache["spells"] = spells

    sel = [s for s in _dnd_cache["spells"] if x.lower() in s["name"].lower()]
    _pprint.pprint(sel, sort_dicts=False)


def dividi_loot(
    MO: int = 0, MA: int = 0, MR: int = 0, MP: int = 0, ME: int = 0, n: int = 7
):
    """Divide loot in monete di vario tipo in parti uguali tra n PG"""
    tot_in_MO = (MP * 10) + MO + (ME / 2) + (MA / 10) + (MR / 100)
    return {
        "MO a testa": int(tot_in_MO // n),
        "resto in MO": tot_in_MO % n,
        "pg": n,
    }
