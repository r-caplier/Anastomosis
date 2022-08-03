import os
import pandas as pd

from constants import *

MAX_DIST = 20

relations_dicts = []


with open(os.path.join(ROOT_PATH, "data", "2021AB_SN", "SRSTRE1")) as f:
    umls_relations_df = pd.read_csv(f, delimiter='|', names=["FirstTUI", "RelationTUI", "EndTUI"], index_col=False)


def get_UMLS_score(StartTUI, EndTUI, startType, endType, umls_relations_df):
    if startType != "ENTITY" or endType != "ENTITY":
        return 1
    else:
        return len(umls_relations_df["RelationTUI"].loc[umls_relations_df["FirstTUI"]
                                                        == StartTUI].loc[umls_relations_df["EndTUI"] == EndTUI])


def build_relations_from_filename(filename):

    with open(os.path.join(ENTITIES_PATH, filename), "r") as f:
        entities_df = pd.read_csv(f).drop("Unnamed: 0", axis=1)

    relations_dicts = []

    for i in range(len(entities_df)):
        if entities_df.iloc[i]["Type"] not in ["ENTITY", "PERSON", "ORG"]:
            continue
        forward_df = entities_df.iloc[i + 1:].loc[entities_df["Sentence"] == entities_df.iloc[i]["Sentence"]]
        valid_relations = forward_df.loc[(forward_df["EndWord"] <= entities_df["StartWord"].iloc[i] +
                                          MAX_DIST) & (forward_df["Word"] != entities_df.iloc[i]["Word"])]
        for j in range(len(valid_relations)):
            if entities_df.iloc[i]["Word"] != entities_df.iloc[j]["Word"] and entities_df.iloc[j]["Type"] in ["ENTITY", "PERSON", "ORG"]:
                score = get_UMLS_score(entities_df.iloc[i]["TUI"], entities_df.iloc[j]["TUI"], entities_df.iloc[i]["Type"], entities_df.iloc[j]["Type"], umls_relations_df)
                if score > 0:
                    relations_dicts.append({"First": i,
                                            "End": i + j + 1,
                                            "FirstWord": entities_df.iloc[i]["Word"],
                                            "EndWord": valid_relations.iloc[j]["Word"],
                                            "FirstCUI": entities_df.iloc[i]["CUI"],
                                            "EndCUI": valid_relations.iloc[j]["CUI"],
                                            "Distance": valid_relations.iloc[j]["StartWord"] - entities_df.iloc[i]["EndWord"],
                                            "ScoreUMLS": score,
                                            "Sentence": entities_df.iloc[i]["Sentence"],
                                            "Document": entities_df.iloc[i]["Document"]})

    return pd.DataFrame(relations_dicts)
