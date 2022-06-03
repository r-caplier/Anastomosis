import os

import spacy
import pandas as pd

from tqdm.auto import tqdm

from knowledge_graphs.extract_ner import build_merged_entities_df
from knowledge_graphs.manual_models import names_et_al

ROOT_PATH = os.path.dirname(os.getcwd())

DATA_CLEAN_PATH = os.path.join(ROOT_PATH, "data", "data_clean")
ENTITIES_PATH = os.path.join(ROOT_PATH, "data", "entities")

if not os.path.exists(ENTITIES_PATH):
    os.mkdir(ENTITIES_PATH)

ner_models = [
    {"type": "Spacy", "name": "SciSpacy MD", "prio": 0, "model": spacy.load("en_core_sci_md")},
    {"type": "Spacy", "name": "Spacy SM", "prio": 1, "model": spacy.load("en_core_web_sm")},
    {"type": "Manual", "name": "Names et al.", "prio": -1, "model": names_et_al}
]
ner_models.sort(key=lambda x: x["prio"])

for filename in tqdm(os.listdir(DATA_CLEAN_PATH)):

    entities_df = build_merged_entities_df(filename, ner_models)

    with open(os.path.join(ENTITIES_PATH, filename.split(".")[0] + ".csv"), "wb") as f:
        entities_df.to_csv(f)
