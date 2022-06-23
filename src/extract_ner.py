import os

import spacy
import scispacy
import pandas as pd

from scispacy.linking import EntityLinker
from scispacy.abbreviation import AbbreviationDetector

from tqdm.auto import tqdm

from knowledge_graphs.extract_ner import build_merged_entities_df
from knowledge_graphs.manual_models import names_et_al

from constants import *

import warnings
warnings.filterwarnings("ignore")

if not os.path.exists(DATA_CLEAN_PATH):
    raise ValueError("No cleaned texts found, please create them first.")

if not os.path.exists(ENTITIES_PATH):
    os.mkdir(ENTITIES_PATH)

nlp_scispacy = spacy.load("en_core_sci_md")
nlp_scispacy.add_pipe("abbreviation_detector")
nlp_scispacy.add_pipe("scispacy_linker", config={"resolve_abbreviations": True,
                      "linker_name": "umls", "max_entities_per_mention": 1})

ner_models = [
    {"type": "Spacy", "name": "SciSpacy MD", "prio": 0, "model": nlp_scispacy},
    {"type": "Spacy", "name": "Spacy SM", "prio": 1, "model": spacy.load("en_core_web_md")},
    {"type": "Manual", "name": "Names et al.", "prio": -1, "model": names_et_al}
]

ner_models.sort(key=lambda x: x["prio"])

for filename in tqdm(os.listdir(DATA_CLEAN_PATH)):

    entities_df = build_merged_entities_df(filename, ner_models)
    entities_df.fillna(value="UNDEF", inplace=True)

    if len(entities_df) != 0:
        with open(os.path.join(ENTITIES_PATH, filename.split(".")[0] + ".csv"), "wb") as f:
            entities_df.to_csv(f)
