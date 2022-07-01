import os
import argparse

import pickle
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

from pyvis.network import Network

from tqdm.auto import tqdm

from constants import *


parser = argparse.ArgumentParser()
parser.add_argument("--overwrite", action="store_true")
parser.set_defaults(overwrite=False)

args = parser.parse_args()

total_sum = 0
num_entries = 0
max_dist = 0
cnt_files = 0
shitty_quantile = 0
p = 0.9

for filename in os.listdir(RELATIONS_PATH):

    if filename.split(".")[-1] != "csv":
        continue

    cnt_files += 1
    with open(os.path.join(RELATIONS_PATH, filename), "r") as f:
        relations_df = pd.read_csv(f).drop("Unnamed: 0", axis=1)

    max_dist = max(max_dist, relations_df["Distance"].max())
    total_sum += sum(relations_df["Distance"])
    num_entries += len(relations_df)
    shitty_quantile += relations_df["Distance"].quantile(p)

THRESHOLD_SCORE = 500
THRESHOLD_COUNT = int(shitty_quantile / cnt_files)

SCORE_UMLS_MULT = 10
STANDARD_SCORE = 1
DIST_CST = 10  # Value used in the exponential, increase to make the distance less impactful

score_dict = {}
count_dict = {}

print(THRESHOLD_COUNT)

with open(os.path.join(ROOT_PATH, "data", "2021AB_SN", "SRSTRE1")) as f:
    umls_relations_df = pd.read_csv(f, delimiter='|', names=["FirstTUI", "RelationTUI", "EndTUI"], index_col=False)


def get_score(distance, score_umls):

    if score_umls == 0:
        return STANDARD_SCORE * np.exp(-1 * distance / DIST_CST)
    else:
        return score_umls * SCORE_UMLS_MULT * np.exp(-1 * distance / DIST_CST)


if args.overwrite or not os.path.exists(os.path.join(RELATIONS_PATH, "dicts.pkl")):

    for filename in tqdm(os.listdir(RELATIONS_PATH)):
        with open(os.path.join(RELATIONS_PATH, filename), "r") as f:
            relations_df = pd.read_csv(f)

        with open(os.path.join(ENTITIES_PATH, filename.split("_")[0] + ".csv"), "r") as f:
            entities_df = pd.read_csv(f)

        if "FirstWord" in relations_df.columns and "EndWord" in relations_df.columns and "Distance" in relations_df.columns and "ScoreUMLS" in relations_df.columns and "Type" in entities_df.columns:

            # Only keeping edges between two ENTITY types
            typed_relations_df = relations_df.join(entities_df["Type"], on=["First"], rsuffix="_first")
            typed_relations_df = typed_relations_df.join(entities_df["Type"], on=["End"], rsuffix="_end")
            relations_df = relations_df.iloc[typed_relations_df.loc[typed_relations_df["Type"] ==
                                                                    "ENTITY"].loc[typed_relations_df["Type_end"] == "ENTITY"].index].reset_index(drop=True)

            for first_word, end_word, distance, score in list(relations_df[["FirstWord", "EndWord", "Distance", "ScoreUMLS"]].itertuples(index=False, name=None)):
                try:
                    first_word, end_word = tuple(sorted((first_word, end_word)))
                except:
                    continue
                if first_word and first_word not in score_dict.keys():
                    score_dict[first_word] = {}
                if end_word and end_word not in score_dict[first_word].keys():
                    score_dict[first_word][end_word] = get_score(distance, score)
                else:
                    score_dict[first_word][end_word] += get_score(distance, score)

                if first_word and first_word not in count_dict.keys():
                    count_dict[first_word] = {}
                if end_word and end_word not in count_dict[first_word].keys():
                    count_dict[first_word][end_word] = 1
                else:
                    count_dict[first_word][end_word] += 1

    with open(os.path.join(RELATIONS_PATH, "dicts.pkl"), "wb") as f:
        pickle.dump((score_dict, count_dict), f)

else:
    with open(os.path.join(RELATIONS_PATH, "dicts.pkl"), "rb") as f:
        score_dict, count_dict = pickle.load(f)

good_edges = []
for k in count_dict.keys():
    for k2 in count_dict[k].keys():
        if count_dict[k][k2] >= THRESHOLD_COUNT and score_dict[k][k2] >= THRESHOLD_SCORE and k != k2:
            good_edges.append({"source": k, "target": k2, "score": count_dict[k][k2]})

# MAX_DEPTH = 1
#
#
# def one_step(k1, cnt):
#     if cnt > MAX_DEPTH or k1 not in count_dict.keys():
#         return []
#     else:
#         edges = []
#         for k2 in count_dict[k1].keys():
#             if count_dict[k1][k2] >= THRESHOLD_COUNT and score_dict[k1][k2] >= THRESHOLD_SCORE:
#                 edges += [{"source": k1, "target": k2, "score": score_dict[k1][k2]}] + one_step(k2, cnt + 1)
#         return edges
#
#
# K = list(count_dict.keys())[5]
# print(K)
# good_edges = one_step(K, 0)

good_edges_df = pd.DataFrame(good_edges).dropna(axis=0)


G = nx.from_pandas_edgelist(good_edges_df,
                            source="source",
                            target="target",
                            edge_attr="score")
net = Network(height='600px', width='50%')
net.show_buttons(filter_=['physics'])
net.from_nx(G)
net.show("example.html")
