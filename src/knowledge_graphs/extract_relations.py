import os
import pandas as pd

from constants import *

MAX_DIST = 20

relations_dicts = []


with open(os.path.join(ROOT_PATH, "data", "2021AB_SN", "SRSTRE1")) as f:
    umls_relations_df = pd.read_csv(f, delimiter='|', names=["FirstTUI", "RelationTUI", "EndTUI"], index_col=False)


def get_UMLS_score(StartTUI, EndTUI, umls_relations_df):
    return len(umls_relations_df["RelationTUI"].loc[umls_relations_df["FirstTUI"]
                                                    == StartTUI].loc[umls_relations_df["EndTUI"] == EndTUI])


def build_relations_from_filename(filename):

    with open(os.path.join(ENTITIES_PATH, filename), "r") as f:
        entities_df = pd.read_csv(f).drop("Unnamed: 0", axis=1)

    relations_dicts = []

    for i in range(len(entities_df)):
        forward_df = entities_df.iloc[i + 1:].loc[entities_df["Sentence"] == entities_df.iloc[i]["Sentence"]]
        valid_relations = forward_df.loc[forward_df["EndWord"] <= entities_df["StartWord"].iloc[i] + MAX_DIST]
        for j in range(len(valid_relations)):
            relations_dicts.append({"First": i,
                                    "End": i + j + 1,
                                    "FirstWord": entities_df.iloc[i]["Word"],
                                    "EndWord": valid_relations.iloc[j]["Word"],
                                    "FirstTUI": entities_df.iloc[i]["TUI"],
                                    "EndTUI": valid_relations.iloc[j]["TUI"],
                                    "FirstGroup": entities_df.iloc[i]["Group"],
                                    "EndGroup": valid_relations.iloc[j]["Group"],
                                    "Distance": valid_relations.iloc[j]["StartWord"] - entities_df.iloc[i]["EndWord"],
                                    "ScoreUMLS": get_UMLS_score(entities_df.iloc[i]["TUI"], entities_df.iloc[j]["TUI"], umls_relations_df)})

    return pd.DataFrame(relations_dicts)
