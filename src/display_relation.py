import os
import argparse

import pandas as pd

from termcolor import colored

from constants import *

CHARS_TO_SHOW = 50

parser = argparse.ArgumentParser(description="Displaying a given word's relations")
parser.add_argument("file_id")
parser.add_argument("word")

args = parser.parse_args()

filename_text = os.path.join(DATA_CLEAN_PATH, args.file_id + ".txt")
filename_entities = os.path.join(ENTITIES_PATH, args.file_id + ".csv")
filename_relations = os.path.join(RELATIONS_PATH, args.file_id + "_RE.csv")

with open(filename_text, "r") as f:
    text = f.read()

with open(filename_entities, "r") as f:
    entities_df = pd.read_csv(f).drop("Unnamed: 0", axis=1)

with open(filename_relations, "r") as f:
    relations_df = pd.read_csv(f).drop("Unnamed: 0", axis=1)

with open(os.path.join(ROOT_PATH, "data", "2021AB_SN", "SRDEF"), "r") as f:
    umls_def_df = pd.read_csv(f, delimiter='|', names=["Record Type", "TUI", "Name", "Tree Number", "Definition",
                                                       "Examples", "Usage note", "non-human flag ?", "Abbreviation", "Inverse"], index_col=False)
    umls_def_df.drop(["Examples", "Usage note", "non-human flag ?"], axis=1, inplace=True)

with open(os.path.join(ROOT_PATH, "data", "2021AB_SN", "SRSTRE1")) as f:
    umls_relations_df = pd.read_csv(f, delimiter='|', names=["FirstTUI", "RelationTUI", "EndTUI"], index_col=False)


found_entities_df = entities_df.loc[entities_df["Word"] == args.word]

for ent in found_entities_df.itertuples():
    found_relations_df = relations_df.loc[relations_df["First"] == ent.Index]

    print("Main Entity:", ent.Word)
    print("Semantic Type:", umls_def_df.loc[umls_def_df["TUI"] == ent.TUI]["Name"].values[0], f"({ent.TUI})")
    print("------------")

    for rel in found_relations_df.itertuples():
        second_ent = entities_df.iloc[rel.End]
        highlighted_text = text[max(0, ent.StartChar - CHARS_TO_SHOW): ent.StartChar] + colored(ent.Word, "red") + \
            text[ent.EndChar: int(second_ent["StartChar"])] + colored(second_ent["Word"], "red") + \
            text[int(second_ent["EndChar"]): min(len(text), ent.StartChar + 3 * CHARS_TO_SHOW)]
        print(highlighted_text)
        print("Entity:", second_ent["Word"])
        print("Semantic Type:", umls_def_df.loc[umls_def_df["TUI"] == second_ent["TUI"]]
              ["Name"].values[0], f"({second_ent['TUI']})")
        for p_rel in umls_relations_df["RelationTUI"].loc[umls_relations_df["FirstTUI"]
                                                                        == ent.TUI].loc[umls_relations_df["EndTUI"] == second_ent["TUI"]].values:
            print(umls_def_df.loc[umls_def_df["TUI"] == p_rel]["Name"].values[0], f"({p_rel})")
        print("------------")

    print("")
