import argparse
import csv
import genanki
import glob
import os
import pandas as pd
import random
import re
import sqlite3
import sys
import pprint

from dataclasses import dataclass
from pathlib import Path
from pybtex.database import parse_file

from ..io import data_export
from ..utils import argparser as my_argparse

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
        latex_envirs: list[str] = ["thm", "cor", "lem", "prop", "proof", "defn", "es", "rmk"],
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

    def to_xlsx(self, path: str | Path) -> None:
        '''Export to a xlsx'''
        if path is None:
            path = Path("/tmp/flashcards.xlsx")
        else:
            path = Path(path)
        data = []
        for card in self.__fc:
            side1, side2 = card.to_csv()
            data.append([side1, side2])
        df = pd.DataFrame(data, columns = ["side1", "side2"])
        data_export({"flashcards": df},  path= path)            
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
        if ext == '.xlsx':
            self.to_xlsx(path=outfile)
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





tex_default_preamble = \
'''
\\documentclass[a4paper]{article}
\\usepackage[T1]{fontenc}
\\usepackage[utf8]{inputenc}
\\usepackage[english, italian]{babel}
\\usepackage{amsmath}
\\usepackage{amsfonts}
\\usepackage{amssymb}
\\usepackage{mathrsfs}
\\usepackage{amsthm}
\\usepackage{tikz}
\\usepackage{mypkg}
\\usepackage{hyperref}
''' 

def make_unique_list(x):
    if x is None:
        return([])
    if not isinstance(x, list):
        x = [x]
    x  = list(set(x))
    return(x)


class Database(object):
    '''Class to create a database (sqlite3) file'''
    
    __exercise_re = re.compile(r'\\begin{exercise}.+?\\end{exercise}')
    __id_re       = re.compile(r'\\id{(.+?)}')
    __page_re     = re.compile(r'\\page{(.+?)}')
    __source_re   = re.compile(r'\\source{(.+?)}')
    __topic_re    = re.compile(r'\\topic{(.+?)}')
    __question_re = re.compile(r'\\begin{question}(.+?)\\end{question}')
    __hint_re     = re.compile(r'\\begin{hint}(.+?)\\end{hint}')
    __solution_re = re.compile(r'\\begin{solution}(.+?)\\end{solution}')

    __sql_create_ex_table =  '''CREATE TABLE exercises
    (id text, page int, source text, topic text, question text, 
    hint text, solution text)'''
    __sql_create_biblio_table = '''CREATE TABLE sources
    (key text, title text, author text, subject text)'''
    __sql_insert_ex_table =  '''INSERT INTO exercises VALUES
    (?, ?, ?, ?, ?, ?, ?)'''
    __sql_insert_biblio_table =  '''INSERT INTO sources VALUES
    (?, ?, ?, ?)'''

    def __init__(self):
        # list like this [(), ()] which are easy to handle with sqlite3
        self.exercises_list = []
        self.biblio_list = []
        self.__parsed = set() # already parsed paths

    # ------------
    # main methods
    # ------------
    def feed(self, paths = None, paths_f = None, biblio_dirs = None):
        '''Read exercises from comma separated paths (directory/files)
        and/from files of paths'''
        if paths is None:
            paths = []
        if paths_f: # se non è None aggiungi i path inseriti nei file
            paths_f_paths = []
            for pf in paths_f:
                pf = Path(pf).expanduser()
                if pf.is_file():
                    with open(pf, 'r') as f:
                        # keep it if not comment or blank line
                        paths_f_paths += [l for l in f.read().splitlines() \
                                          if ((not l.startswith("#")) and (l.strip() != ""))]
            paths += paths_f_paths
        if biblio_dirs is None:
            biblio_dirs = ["~/src/other/exercises/biblio"]
        paths += biblio_dirs
        if not paths:
            raise Exception("Cosa strana che non vi sian elementi qui ne da paths ne da list")
        # now start parsing recursively: if file, parse it; if dir: go recursive
        for p in paths:
            p = Path(p).expanduser()
            # controllo che non sia gia stato parsato per evitare cicli infiniti
            if p in self.__parsed:
                print(p, 'è già stato parsato, lo salto.')
                continue
            if p.is_dir():
                self.__parse_dir(d = p)
                self.__parsed.add(p)
            elif p.is_file():
                self.__parse_file(f = p)
                self.__parsed.add(p)
            else:
                print(p, 'non è ne una directory ne un file, lo salto.')
        print("Processed files:")
        pprint.pprint(self.__parsed)
        print("Extracted exercises:", len(self.exercises_list))
        return(self)

    
    def __parse_dir(self, d):
        # effettua lo stesso ciclo di feed sul contenuto della singola directory
        # if file: parse it
        # if dir: go recursive on each entry
        # else do nothing
        for p in d.iterdir():
            if p in self.__parsed:
                print(p, 'è già stato parsato, lo salto.')
                continue
            if p.is_dir():
                self.__parse_dir(d = p)
                self.__parsed.add(p)
            elif p.is_file():
                self.__parse_file(f = p)
                self.__parsed.add(p)
            else:
                print(p, 'non è ne una directory ne un file, lo salto.')

                
    def __parse_file(self, f):
        # parsa un singolo file in base all'estensione
        ext = f.suffix
        if ext in {".tex"}:
            self.__parse_tex(path = f)
        elif ext in {".bib"}:
            self.__parse_bib(path = f)
        else:
            print(f, 'non è un file .tex o .bib; ignoro.')
        
    
    def write(self, f = None):
        'Write exercises to a sqlite3 file'
        # erase old version
        f = os.path.expanduser(f)
        if (os.path.isfile(f)):
            os.remove(f)
        # create exercise table
        con = sqlite3.connect(f)
        c = con.cursor()
        c.execute(self.__sql_create_ex_table)
        c.execute(self.__sql_create_biblio_table)
        # fill exercise table
        c.executemany(self.__sql_insert_ex_table,
                      self.exercises_list)
        c.executemany(self.__sql_insert_biblio_table,
                      self.biblio_list)
        con.commit()
        con.close()
        return(self)
    
    # ----------------
    # helper functions
    # ----------------
    def __parse_tex(self, path = None):
        # reading
        with open(path, 'r') as f:
            data = f.read()
        data = data.replace('\n', '')
        data = re.sub( '\s+', ' ', data)
        # parsing
        # 1) split by exercise
        exercises = self.__exercise_re.findall(data)
        # 2) extract and save
        for ex in exercises:
            self.exercises_list.append(
                self.__parse_exercise(ex = ex, f = path))


    def __get_regex_value(self, re, x):
        found = re.search(x)
        if found:
            res = found.group(1).strip()
            # TODO fix here
            # return(re.sub(' +', ' ', res))
            return(res)
        else:
            return(None)

        
    def __parse_exercise(self, ex = None, f = None):
        ID       = self.__get_regex_value(self.__id_re, ex)
        page     = self.__get_regex_value(self.__page_re, ex)
        source   = self.__get_regex_value(self.__source_re, ex)
        topic    = self.__get_regex_value(self.__topic_re, ex)
        question = self.__get_regex_value(self.__question_re, ex)
        hint     = self.__get_regex_value(self.__hint_re, ex)
        solution = self.__get_regex_value(self.__solution_re, ex)
        try:
            page = int(page)
        except ValueError:
            page = None
            print('Invalid integer page in ' + str(f) + '. Setting it to None')
        return((ID, page, source, topic, question, hint, solution))
        

    def __parse_bib(self, path = None):
        bib_data = parse_file(path)
        for entry in bib_data.entries.values():
            # keep only those with a subject
            if 'subject' in entry.fields:
                cognomi = []
                for author in entry.persons["author"]:
                    cognomi.append(str(author.last_names[0]))
                self.biblio_list.append(
                    (entry.key,
                     entry.fields['title'],
                     ", ".join(cognomi),
                     entry.fields['subject'])
                )
        

# -------------------------------------------------------------------

class Worksheet(object):
    '''Class to extract exercises from a database file'''

    def __init__(self):
        # list like this [(), ()] which are easy to handle with sqlite3
        self.exercises_list = []

    def select(self, files = None,
               select_where = '',
               random = False,
               n = -1):
        'Do a sql select on a sqlite3 database and save rows in exercises_list'

        # avoid duplicated file names
        files = make_unique_list(files)

        # row selection
        if isinstance(select_where, str) and select_where != '':
            where = " and " + select_where
        else:
            where = ""

        # random order
        if isinstance(random, bool) and random is True:
            order_by = " order by random() "
        else:
            order_by = ""

        # setup limit
        if isinstance(n, int) and n >= 0:
            limit = " limit " + str(n)
        else:
            limit = ""

        sql = '''select id, page, source, topic, question,
                        hint, solution, subject
                 from   exercises, sources
                 where  exercises.source = sources.key ''' + \
                     where + \
                     order_by + \
                     limit

        anydb = False
        for f in files:
            f = os.path.expanduser(f)
            if os.path.isfile(f):
                con = sqlite3.connect(f)
                c = con.cursor()
                try:
                    c.execute(sql)
                except sqlite3.OperationalError:
                    print("Errore nell'esecuzione di:\n ",
                          "              ", sql)
                self.exercises_list += c.fetchall()
                con.close()
                anydb = True
            else:
                print(f, ' does not exists. Skipping\n')
        if not anydb:
            raise Exception("No useful db files were provided")
        return(self)

    def to_tex(self,
               tex = '/tmp/worksheet.tex',
               preamble = tex_default_preamble,
               show_topic = True,
               show_hint = True
    ):
        '''Export exercises_list in a .tex'''
        tex = os.path.expanduser(tex)
        doc = [preamble, '''\\begin{document}'''] + \
              ['\\tableofcontents'] + \
              self.__format_exercises(show_topic = show_topic,
                                      show_hint = show_hint) + \
              ['''\\end{document}''']
        # here replace None with ''
        for i in range(0, len(doc)):
            if doc[i] is None:
                doc[i] = ""
        # and output to .tex file
        with open(tex, 'w') as f:
            f.write('\n'.join(doc))
        return(self)

    def __format_exercises(self, show_topic, show_hint):
        ex_section  = []
        res_section = []

        column = {'id'       : 0,
                  'page'     : 1,
                  'source'   : 2,
                  'topic'    : 3,
                  'question' : 4, 
                  'hint'     : 5,
                  'solution' : 6,
                  'subject'  : 7}
        
        index_list = list(range(0, len(self.exercises_list)))
        for i in index_list:
            ex_id = (self.exercises_list[i])[column['id']]
            page = (self.exercises_list[i])[column['page']]
            source = (self.exercises_list[i])[column['source']]
            topic = (self.exercises_list[i])[column['topic']]
            question = (self.exercises_list[i])[column['question']]
            hint = (self.exercises_list[i])[column['hint']]

            if show_hint and (hint is not None):
                hint = '\\emph{Suggerimento}: ' + hint
            else:
                hint = ''

            header_tail = ex_id + ' pag.~' + str(page) + \
                          ' (' + str(source) + ')' + '}'

            if show_topic and (topic is not None):
                header_es = '\\paragraph{' + topic + ': es.~' + header_tail
            else:
                header_es = '\\paragraph{Es.~' + header_tail
            
            header_sol = '\\paragraph{Sol.~es.~' + header_tail
            
            if question is not None or question == '':
                soluzione = (self.exercises_list[i])[column['solution']]
                ex_section += ([header_es] + [question] + [hint])
                if soluzione is not None or soluzione == '':
                    res_section += ([header_sol] + [soluzione])
        return(['''\\section{Esercizi}'''] + \
               ex_section + \
               ['''\\newpage'''] + \
               ['''\\section{Soluzioni}'''] + \
               res_section)





def exercises_db():
    opts = (
        # (param, help, default, type)
        # --paths
        ('paths',
         'str: comma separated list of exercise paths (source directories/files)',
         # '~/src/other/exercises',
         None,
         str),
        # --lists
        ('lists',
         'str: comma separated list of file having a lists of paths (dir/files) one per line',
         None,
         str),
        # --outfile
        ('outfile',
         'str:  sqlite3 db to save',
         None,
         # '~/.exercises.db',
         str))

    args = my_argparse(opts)
    paths = args['paths']
    lists = args['lists']
    outfile = args['outfile']
    # se sono entrambi a none c'è qualcosa che non torna
    if ((paths is None) and (lists is None)):
        raise Exception("uno tra --paths e --lists deve essere specificato")
    if outfile is None:
        raise Exception("Bisogna specificare  il file sqlite3 su cui esportare mediante --outfile")
    # da qui in poi dovrebbe essere a posto
    if isinstance(paths, str):
        paths = paths.split(',')
    if isinstance(lists, str):
        lists = lists.split(',')
    ex = Database()
    # print(paths, lists)
    ex.feed(paths = paths, paths_f = lists).write(outfile)
    return(0)

def exercises_ws():
    opts = (
        # (param, help, default, type)
        # --dbs
        ('dbs',
         'str: comma separated list of db produced by exercises_db',
         # '~/.exercises_dbs',
         None,
         str),
        # --select_where
        ('select_where',
         'char: sql where statement used to select rows from the database',
         '',
         str),
        # --random
        ('random',
         'bool: random ordering? (default: False)',
         False,
         bool),
        # --n
        ('n',
         'int: n. of records (if negative - the default - take them all)',
         -1, # 
         int),
        # --show_topic
        ('show_topic',
         'bool: show exercise topic? (default: True)',
         True,
         bool),
        # --show_hint
        ('show_hint',
         'bool: show exercise hint? (default: True)',
         True,
         bool),
        # --tex
        ('tex',
         'str:  output tex file',
         '/tmp/worksheet.tex',
         str))
    args = my_argparse(opts)
    dbs = args['dbs'].split(',')
    select_where = args['select_where']
    random = args['random']
    n = args['n']
    show_topic = args['show_topic']
    # print(show_topic)
    show_hint = args['show_hint']
    # print(show_hint)
    tex = args['tex']
    ws = Worksheet()
    ws.select(files = dbs,
              select_where = select_where,
              random = random,
              n = n)
    ws.to_tex(tex = tex,
              show_topic = show_topic,
              show_hint = show_hint)
    return(0)
