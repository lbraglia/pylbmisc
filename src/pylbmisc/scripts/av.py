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
ora_reggio = ["16.00-19.00"] * 4 + ["16.30-19.30", "20.30-23.30", "20.30-23.30", "16.30-19.30"] + ["16.00-19.00"] * 3
location_reggio = ["P. del Monte"]*5 + ["P. Martiri 7 Luglio"]*2 + ["P. del Monte"]*4

def av_datecubianno():
    """
    av_datecubianno 2024
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("anno")
    args = parser.parse_args()
    anno = int(args.anno)
    data_reggio = []
    giorno_reggio = []
    for month in [1,2,3,4,5,6,7,9,10,11,12]: # avoid august
        m = calendar.monthcalendar(anno, month)
        for week in m:
            if (month in [6,7]):
                select = calendar.SATURDAY
                giorno_reggio.append("Sab")
            else:
                select = calendar.SUNDAY
                giorno_reggio.append("Dom")
            giorno = week[select]
            if giorno:
                data_reggio.append(dt.date(anno, month, giorno))
                break
    print("```")
    for GR, DR, OR, LR in zip(giorno_reggio, data_reggio, ora_reggio, location_reggio):
        print("{} {}, {}, {}".format(GR, DR.strftime("%d/%m"), OR, LR))
    print("```")
