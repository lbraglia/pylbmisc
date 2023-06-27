""" Utils for DND """

def mese(x: int):
    """ Restituisce il nome del mese nei forgotten realms """
    mesi = ["Hammer",                   #  1
            "Alturiak",                 #  2
            "Ches",                     #  3
            "Tarsakh",                  #  4
            "Mirtul",                   #  5
            "Kythorn",                  #  6
            "Flamerule",                #  7
            "Eleasis",                  #  8
            "Eleint",                   #  9
            "Marpenoth",                # 10
            "Uktar",                    # 11
            "Nightal"                   # 12
    ]
    return mesi[x - 1]


def dividi_loot(MO: int = 0,
                MA: int = 0,
                MR: int = 0,
                MP: int = 0,
                ME: int = 0,
                n: int = 7):
    """ Divide loot in monete di vario tipo in parti uguali tra n PG """
    tot_in_MO = (MP * 10) + MO + (ME / 2) + (MA / 10) + (MR / 100)
    return {
        "MO a testa": int(tot_in_MO // n),
        "resto in MO" : tot_in_MO % n,
        "pg": n,
    }
