import os
import pandas as pd

SN_path = os.path.join("/", "home", "romainc", "Desktop", "2021AB", "SRDEF")

with open(SN_path, "r") as f:
    all_df = pd.read_csv(f, delimiter='|', header=None)

all_df.dropna(how='all', axis=1, inplace=True)
all_df.columns = ["Record Type", "UI", "Name", "Tree Number", "Definition", "Usage Notes", "NH", "Abbreviation", "Inverse"]

rel_df = all_df.loc[all_df["Record Type"] == "RL"]

print(rel_df.loc[rel_df["Tree Number"][1] == "1"])
