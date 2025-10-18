import re


def main():
    with open("doc_export.Rout", "r") as f:
        doc = f.read()

    doc_splitted = doc.split("\n$")[1:]
    name_re = re.compile("^(.+)\n")
    # filename = name_re.match(doc_splitted[1]).group(0).replace("\n","")  + ".txt"
    # # name_re.sub(r"\1", doc_splitted[1])
    # actual_doc = name_re.sub(r"", doc_splitted[1])

    for man in doc_splitted:
        fname = name_re.match(man).group(0).replace("\n","")  + ".txt"
        actual_doc = name_re.sub(r"", man)
        with open(fname, "w") as f:
            print(actual_doc, file=f)


if __name__ == "__main__":
    main()
