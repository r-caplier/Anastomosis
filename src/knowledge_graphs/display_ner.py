import os
import argparse

import pandas as pd

from termcolor import colored


def get_color_map(entities_df):

    color_list = ['red', 'blue', 'green', 'yellow', 'magenta', 'cyan', 'gray']
    unique_types = entities_df["entity_type"].unique()

    types_to_color = {}
    cnt = 0
    for type_ent in unique_types:
        types_to_color[type_ent.lower()] = color_list[cnt]
        cnt += 1

    return types_to_color


def print_colored_text(text, entities_df):

    paragraphs = text.split("\n")
    color_map = get_color_map(entities_df)
    colored_text = ""

    for i in range(len(paragraphs)):
        last_end = 0
        colored_paragraph = ""
        if len(entities_df.loc[entities_df["paragraph_id"] == i]) == 0:
            colored_paragraph = paragraphs[i]
        else:
            for index, entity in entities_df.loc[entities_df["paragraph_id"] == i].iterrows():
                start = entity['start']
                end = entity['end']
                if last_end <= start:
                    colored_paragraph += paragraphs[i][last_end:start] + \
                        colored(entity["word"], color_map[entity["entity_type"].lower()])
                    last_end = end
                elif last_end > start and last_end < end:
                    colored_paragraph += colored(entity["word"][last_end:end], color_map[entity["entity_type"].lower()])
                    last_end = end
            if last_end != len(text):
                colored_paragraph += paragraphs[i][last_end:]

        print(colored_paragraph)


ROOT_PATH = os.path.dirname(os.path.dirname(os.getcwd()))

DATA_CLEAN_PATH = os.path.join(ROOT_PATH, "data", "data_clean")
ENTITIES_PATH = os.path.join(ROOT_PATH, "data", "entities")

parser = argparse.ArgumentParser(description="Gimme thy name!")
parser.add_argument("--filename", help="Name of the file to display")

args = parser.parse_args()
filename = args.filename


with open(os.path.join(DATA_CLEAN_PATH, filename), "r") as f:
    text = f.read()

with open(os.path.join(ENTITIES_PATH, filename.split(".")[0] + ".csv"), "r") as f:
    entities_df = pd.read_csv(f)

print_colored_text(text, entities_df)
