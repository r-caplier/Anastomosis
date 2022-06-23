import os
import pandas as pd

from tqdm.auto import tqdm

from knowledge_graphs.extract_relations import build_relations_from_filename

from constants import *

if not os.path.exists(RELATIONS_PATH):
    os.mkdir(RELATIONS_PATH)

for filename in tqdm(os.listdir(ENTITIES_PATH)):

    relations_df = build_relations_from_filename(filename)

    with open(os.path.join(RELATIONS_PATH, filename.split(".")[0] + "_RE.csv"), "wb") as f:
        relations_df.to_csv(f)
