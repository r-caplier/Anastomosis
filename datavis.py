import subprocess
import os
import spacy

from gensim.models import TfidfModel
from gensim.corpora import Dictionary
from gensim.models import LdaModel, LsiModel
from pprint import pprint


nlp = spacy.load('en_core_web_sm')


def get_clean_tokens(file):

    filename = os.path.join('data', file)

    raw_text = subprocess.run(['pdf2txt.py', filename], stdout=subprocess.PIPE).stdout.decode('utf-8').lower()
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


files = os.listdir('data')[:10]
corpus = []
for file in files:
    corpus.append(get_clean_tokens(file))
