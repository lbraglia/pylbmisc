import argparse
import calendar
import datetime as dt

# ----------
# dati vari
# ----------
giorni = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
mesi_ita = ["", "gennaio", "febbraio", "marzo", "aprile", "maggio",
            "giugno", "luglio", "agosto", "settembre", "ottobre",
            "novembre", "dicembre"]

# orari di ciascun mese
ora_reggio = ["16-19"] * 4 + ["16.30-19.30", "17-20", "20-23", "16.30-19.30"] + ["16-19"] * 3
ora_modena = ["16-19"] * 3 + ["17-20"] *2  + ["20-22.30", "20.30-23.30"] + ["vedi_ora"]*4
location_reggio = ["PDM"]*5 + ["M7L"]*2 + ["PDM"]*4
location_modena = ["PM"]*5 + ["PDP"]*2 + ["PM"]*4

def av_datecubianno():
    """
    av_datecubianno 2024
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("anno")
    args = parser.parse_args()
    anno = int(args.anno)
    data_reggio = []
    for month in [1,2,3,4,5,6,7,9,10,11,12]: # avoid august
        m = calendar.monthcalendar(anno, month)
        for week in m:
            sab = week[calendar.SATURDAY]
            if sab:
                data_reggio.append(dt.date(anno, month, sab))
                break
    data_modena = [d + dt.timedelta(days=14) for d in data_reggio]
    print("```")
    # for LR, DR, OR, LM, DM, OM in zip(location_reggio, data_reggio, ora_reggio, location_modena, data_modena, ora_modena):
    #     print("Reggio ({}), {}, {}".format(LR, DR.strftime("%d-%m"), OR))
    #     print("Modena ({}), {}, {}".format(LM, DM.strftime("%d-%m"), OM))
    for DR, OR, DM, OM in zip(data_reggio, ora_reggio, data_modena, ora_modena):
        print("Reggio, {}, {}".format(DR.strftime("%d-%m"), OR))
        print("Modena, {}, {}".format(DM.strftime("%d-%m"), OM))
    print("```")
    # print("""
    # **Legenda**:
    # PDM = Piazza del Monte,
    # M7L = Piazza Martiri del 7 Luglio,
    # PM  = Piazza Matteotti (Via Emilia)
    # PDP = Piazza della Pomposa
    # """)
