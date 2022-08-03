import os
import pandas as pd

SN_path = os.path.join("/", "home", "romainc", "Desktop", "2021AB", "SRDEF")

with open(SN_path, "r") as f:
    all_df = pd.read_csv(f, delimiter='|', header=None)

all_df.dropna(how='all', axis=1, inplace=True)
all_df.columns = ["Record Type", "UI", "Name", "Tree Number", "Definition", "Usage Notes", "NH", "Abbreviation", "Inverse"]

rel_df = all_df.loc[all_df["Record Type"] == "RL"]

tree_nodes = list(rel_df["Tree Number"].apply(lambda x: x.split(".")).values)
rel_df["Tree Ids"] = tree_nodes

tree_nodes = sorted(tree_nodes)
good_nodes = []

for elem in tree_nodes:
    if elem[0] == 'R' or elem[0] == 'H':
        good_nodes.append(elem)
    elif len(elem) == 1:
        continue
    else:
        if (elem[0] == 'R3' and int(elem[1]) < 5) or (elem[0] == 'R5' and elem[1] == '3'):
            if len(elem) == 2:
                continue
            else:
                good_nodes.append(elem)
        else:
            good_nodes.append(elem)
keep = rel_df["Tree Ids"].apply(lambda x: x in good_nodes)

good_rel_df = rel_df.loc[keep].drop("Tree Ids", axis=1).reset_index(drop=True)
print(good_rel_df)
