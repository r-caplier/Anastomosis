# List of dictonnaries, pattern is a regex expression, type is either pattern or block

BAD_PATTERNS = [
    {"pattern":"[fF]ig\.\s*[0-9]", "type": "pattern"} # Fig.1 for example
    {"pattern": "^[http|https]:\/\/\S+(\/\S+)*(\/)?$", "type": "pattern"}
]
