import re

def names_et_al(text):

    pat = r"[A-Z][a-z][a-zA-Z]( [A-Z])? et al\.?"
    return re.findall(pat, text)
