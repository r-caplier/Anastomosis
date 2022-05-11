import subprocess
import os

filename = "21769467.pdf"  # DO NOT CHANGE
fileloc = os.path.join("data", filename)

raw_text = subprocess.run(["pdf2txt.py", fileloc], stdout=subprocess.PIPE).stdout.decode("utf-8")

start_id_1 = raw_text.find("ABSTRACT")
start_id_2 = raw_text.find("Abstract")

test = raw_text[start_id:1000].split(".\n")[0]

test_real = ""
for part in test.split("\n"):
    if len(part) != 0 and part[-1] == "-":
        part = part[:-1]
    test_real += " " + part

print(test_real + ".")
