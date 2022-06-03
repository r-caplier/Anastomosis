import os
import argparse

import spacy
import pandas as pd

from termcolor import colored


def show_entities(docs):

    if entities:
        for ent in entities:
            print(ent.text + ' - ' + str(ent.start_char) + ' - ' + str(ent.end_char) +
                  ' - ' + ent.label_ + ' - ' + str(spacy.explain(ent.label_)))
    else:
        print('No named entities found.')


def get_color_map(entities_df):

    colors = ["red", "blue", "green", "yellow", "magenta", "cyan", "grey", "white"]

    types_to_color = {}
    cnt = 0
    for type_ent in list(entities_df["Type"].value_counts().index):
        try:
            types_to_color[type_ent] = colors[cnt]
        except:
            types_to_color[type_ent] = None
        cnt += 1

    return types_to_color


def print_colored_text(text, entities_df):

    color_map = get_color_map(entities_df)
    colored_text = ""
    last_end = 0

    for i in range(len(entities_df)):
        start = entities_df.iloc[i]["StartChar"]
        end = entities_df.iloc[i]["EndChar"]
        e_type = entities_df.iloc[i]["Type"]
        if last_end <= start:
            colored_text += text[last_end:start] + colored(text[start:end], color_map[e_type])
            last_end = end
        elif last_end > start and last_end < end:
            colored_text += colored(text[last_end:end], color_map[e_type])
            last_end = end
    if last_end != len(text):
        colored_text += text[last_end:]

    print(colored_text)

    for k, v in color_map.items():
        print(colored(k, v))
