import os
import argparse

import pandas as pd

from knowledge_graphs.display_ner import print_colored_text

ROOT_PATH = os.path.dirname(os.getcwd())

DATA_CLEAN_PATH = os.path.join(ROOT_PATH, "data", "data_clean")
ENTITIES_PATH = os.path.join(ROOT_PATH, "data", "entities")

parser = argparse.ArgumentParser(description="Gimme thy name!")
parser.add_argument("--filename", help="Name of the file to display")
parser.add_argument('--corrected', action='store_true')
parser.set_defaults(corrected=False)

args = parser.parse_args()
filename = args.filename

with open(os.path.join(DATA_CLEAN_PATH, filename), "r") as f:
    text = f.read()

with open(os.path.join(ENTITIES_PATH, filename.split(".")[0] + ".csv"), "r") as f:
    entities_df = pd.read_csv(f)

print_colored_text(text, entities_df)
