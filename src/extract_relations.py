import os
import pandas as pd

from tqdm.auto import tqdm

from knowledge_graphs.extract_relations import build_relations_from_filename

RELATIONS_PATH = os.path.join("/home/romainc/code/Anastomosis/data/relations")
ENTITIES_PATH = os.path.join("/home/romainc/code/Anastomosis/data/entities")

if not os.path.exists(RELATIONS_PATH):
    os.mkdir(RELATIONS_PATH)

theo_rel = 0
total_rel = 0

for filename in tqdm(os.listdir(ENTITIES_PATH)):

    filename = filename.split('.')[0]

    # relations_df,  = build_relations_from_filename(filename)
    #
    # with open(os.path.join(RELATIONS_PATH, filename.split(".")[0] + "_RE.csv"), "wb") as f:
    #     relations_df.to_csv(f)

    with open(os.path.join(ENTITIES_PATH, filename + ".csv"), "r") as f:
        entities_df = pd.read_csv(f)
    theo_rel += len(entities_df) * (len(entities_df) + 1) / 2

    with open(os.path.join(RELATIONS_PATH, filename + "_RE.csv"), "r") as f:
        relations_df = pd.read_csv(f)
    total_rel += len(relations_df)

print(len(os.listdir(ENTITIES_PATH)))
print(theo_rel)
print(theo_rel / len(ENTITIES_PATH))

print(len(os.listdir(RELATIONS_PATH)))
print(total_rel)
print(total_rel / len(os.listdir(RELATIONS_PATH)))
