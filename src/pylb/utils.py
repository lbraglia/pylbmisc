import argparse
import math
import re
import readline
readline.parse_and_bind('set editing-mode emacs')

def argparser(opts):
    'Helper function for argument parsing.'
    parser = argparse.ArgumentParser()
    defaults = {}
    for i in opts:
        optname = i[0]
        optdescription = i[1]
        optdefault = i[2]
        opttype = i[3]
        # create help string and add argument to parsing
        help_string = '{0} (default: {1})'.format(optdescription,
                                                  str(optdefault))
        parser.add_argument('--' + optname, help = help_string, type = str)
    # do parsing
    args = vars(parser.parse_args()) #vars to change to a dict
    # defaults settings and types management
    for i in opts:
        optname = i[0]
        optdescription = i[1]
        optdefault = i[2]
        opttype = i[3]
        # se il valore è a none in args impostalo al valore di default
        # specificato
        if (args[optname] is None):
            args[optname] = optdefault
        # se il tipo è logico sostituisci un valore possibile true con
        # l'equivalente python
        if (opttype == bool):
            # mv to character if not already (not if used optdefault)
            args[optname] = str(args[optname])
            true_values = ('true', 'True', 'TRUE', 't', 'T', '1', 'y', 'Y',
                           'yes', 'Yes', 'YES') 
            if (args[optname] in true_values):
                args[optname] = 'True'
            else:
                args[optname] = ''
        # converti il tipo a quello specificato
        args[optname] = opttype(args[optname])
    return(args)



def import_logical(x):
    """
    Function to import logical values saved in csv
    """
    if ((x == "TRUE") or (x == "True") or (x == True)):
        return True
    elif (x == "NA") or (x == None) or (x == ""):
        return None
    else:
        return False

    
def import_character(x):
    """
    Function to import characters values saved in csv
    """
    if (x == "" or x == "NA"):
        return None
    else:
        return str(x)


def match_arg(arg, choices):
    res = [expanded for expanded in choices \
           if expanded.startswith(arg)]
    l = len(res)
    if l == 0:
        raise ValueError("Parameter ", arg, "must be one of ", choices)
    elif l > 1:
        raise ValueError(arg, "matches multiple choices from ", choices)
    else:
        return res[0]


def unique(items):
    seen = set()
    for item in items:
        if item in seen:
            pass
        else:
            seen.add(item)
            yield item


def ascii_header(x):
    l = len(x)
    header = ("=" * l)
    print(header)
    print(x.upper())
    print(header, '\n')
    
 
def line_to_numbers(x):
    """ transform a string of positive numbers "1 2-3, 4, 6-10" to a list [1,2,3,4,6,7,8,9,10] """
    # replace comma with white chars
    x = x.replace(",", " ")
    # keep only digits, - and white spaces
    x = re.sub(r'[^\d\- ]', '', x)
    # split by whitespaces
    spl = x.split(" ")
    # change ranges to proper
    expanded = []
    single_page_re = re.compile("^\d+$")
    pages_range_re = re.compile("^(\d+)-(\d+)$")
    for i in range(len(spl)):
        # Check if the single element match one of the regular expression
        single_page = single_page_re.match(spl[i])
        pages_range =  pages_range_re.match(spl[i])
        if single_page:
            # A) One single page: append it to results
            expanded.append(spl[i])
        elif pages_range:
            # B) Pages range: append a list of (expanded) pages to results
            first = int(pages_range.group(1))
            second = int(pages_range.group(2))
            # step is 1 if first is less than or equal to second or -1
            # otherwise 
            step = 1 * int(first <= second)  - 1 * int(first > second)
            if step == 1:
                second += 1
            elif step == -1:
                second -= 1
            else:
                # do nothing (ignore if they don't match)
                pass
            expanded_range = [str(val) for \
                              val in range(first, second, step)]
            expanded += expanded_range
        else:
            ValueError(str(spl[i]) + "does not match a single page re nor a pages range re.")
    # coerce to integer expanded
    for i in range(len(expanded)):
        expanded[i] = int(expanded[i])
    return(expanded)

def menu(choices  = None,
         title    = "",
         multiple = False,
         repeated = False,
         strict   = True):
    """ 
    Return a single choice, a list of selected choiches or None if nothing
    was choosed
    """
    available_ind = [i + 1 for i in range(len(choices))]
    avail_with_0  = [0] + available_ind
    the_menu = "\n".join([str(i) + '. '+ str(c)
                          for i, c in zip(available_ind, choices)])
    if multiple:
        select_msg = "Selection (values as '1, 2-3, 6') or 0 to exit: "
    else:
        select_msg = "Selection (0 to exit): "
    if title:
        ascii_header(title)
    print(the_menu, '\n')
    ind = line_to_numbers(input(select_msg))
    # normalize to list (for single selections, for now)
    if not isinstance(ind, list):
        ind = list(ind)
    if strict:
        # continue asking for input until all index are between the selectable
        while not all([i in avail_with_0 for i in ind]):
            not_in = [i for i in ind if i not in avail_with_0]
            print("Not valid insertion: ", not_in, "\n")
            ind = line_to_numbers(input(select_msg))
            if not isinstance(ind, list):
                ind = list(ind)
    else:
        # keep only the input in avail_with_0
        allowed = [i for i in ind if i in avail_with_0]
        any_not_allowed = not all(allowed)
        if any_not_allowed:
            print("Removed some values (not 0 or specified possibilities): ",
                  list(set(ind) - set(allowed)), ".")
            ind = allowed
    # make unique if not allowed repetitions
    if not repeated:
        ind = list(unique(ind))
    # obtain the selection
    rval = [choices[i - 1] for i in ind if i != 0]
    # return always a list should simplify the code
    return rval



if __name__ == '__main__':
    # # test argparse
    # opts = (
    #     ('download', 'a True default', True, bool),
    #     ('another_option', 'a false default', False, bool),
    #     ('years', 'integer: years to be downloaded (PagesList)', 1998, int),
    #     ('eds', 'str: edition/s to be downloaded (comma separated)',
    #      'SE,SSE', str), 
    # )
    # args = argparser(opts)
    # print(args)

    # test menu
    print(menu(choices  = ["a", "b", "c"],
               title    = "Test menu multiple/repeated",
               multiple = True,
               repeated = False))
