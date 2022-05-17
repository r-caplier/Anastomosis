# List of dictonnaries, pattern is a regex expression, type is either pattern or block
# Parenthesis : Right now doesn't take into account the possibility of a multi line parenthesis

BAD_PATTERNS = [
    {"pattern": "[fF]ig ?\.\s*[0-9]?", "type": "pattern"},  # Fig.1 for example
    {"pattern": "[fF]igure", "type": "block"},  # Fig.1 for example
    {"pattern": "^[http|https]:\/\/\S+(\/\S+)*(\/)?$", "type": "pattern"},
    {"pattern": "\((.*)\)", "type": "pattern"},  # Removing parenthesis and everything inside
    {"pattern": "\((.*)", "type": "pattern"},  # Case for parenthesis ending on the next line
    {"pattern": "(.*)\)", "type": "pattern"},  # Case for parenthesis started earlier and ending here
    {"pattern": r"[A-Za-z0-9]*@[A-Za-z]*\.?[A-Za-z0-9]*", "type": "block"}, # Email adress
    {"pattern": "\[[0-9,\-– ]+\]", "type": "pattern"},  # Reference hooks
    {"pattern": "[\x0c\x0b]", "type": "block"},  # Big string of spaces (text placement in pdf)
    {"pattern": "^[0-9]+$", "type": "block"},  # Lines with only numbers
    {"pattern": "^ ?[a-zA-Z0-9] ?$", "type": "pattern"},  # Weird patterns ?
]
