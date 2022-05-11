import subprocess
import os

from PyPDF2 import PdfFileReader


def get_clean_tokens(file):

    nlp = spacy.load("en_core_web_sm")

    raw_text = subprocess.run(["pdf2txt.py", filename], stdout=subprocess.PIPE).stdout.decode("utf-8").lower()
    document = nlp(raw_text)
    doc_no_names = " ".join([ent.text for ent in document if not ent.ent_type_])
    list_tokens = [ent.text for ent in document if (
        ent.text not in spacy.lang.en.stop_words.STOP_WORDS and not ent.ent_type_ and ent.text.isalpha() and len(ent.text) > 1)]

    start = False
    end = False
    for i in range(len(list_tokens)):
        if not start and list_tokens[i] == "abstract":
            start = True
            start_id = i + 1
        elif not end and list_tokens[i] == "references" or list_tokens[i] == "acknowledgements":
            end = True
            end_id = i - 1

    return list_tokens[start_id:end_id]


def extract_information(pdf_path):
    with open(pdf_path, 'rb') as f:
        pdf = PdfFileReader(f, strict=False)
        information = pdf.getDocumentInfo()

    return information


files = [os.path.join("data", file) for file in os.listdir("data")[:2]]
for file in files:
    info = extract_information(file)
    print(info.title)
