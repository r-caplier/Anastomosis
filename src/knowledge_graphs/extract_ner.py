import os
import argparse

import pandas as pd

from transformers import AutoConfig
from transformers import AutoTokenizer
from transformers import AutoModelForTokenClassification
from transformers import pipeline


def get_entities(text, pipes):

    entities_df = pd.DataFrame(columns=["pipe", "entity", "score", "index", "word", "start", "end"])

    paragraphs = text.split("\n")
    for i in range(len(paragraphs)):
        for pipe_name, pipe in pipes.items():
            entities = pipe["pipe"](paragraphs[i])
            pipe_df = pd.DataFrame(entities)
            pipe_df["pipe"] = [pipe_name] * len(entities)
            pipe_df["paragraph_id"] = [int(i)] * len(entities)
            entities_df = pd.concat([entities_df, pipe_df])

    return entities_df


def largest_jump(l):

    max_j = 0
    for i in range(len(l) - 1):
        j = l[i + 1] - l[i]
        if j > max_j:
            max_j = j
    return max_j


def corrected_word(start, end, text):
    while start >= 0 and text[start].isalpha():
        start -= 1
    while end < len(text) and text[end].isalpha():
        end += 1
    return text[start + 1: end]


def remove_duplicates(df):

    list_keep = [True] * len(df)

    def get_higher_words_index(df, i):
        pipe_row = df.iloc[i]["pipe"]
        higher_words_df = df.loc[(df["paragraph_id"] == df.iloc[i]["paragraph_id"]) & (
            df["pipe"] != df.iloc[i]["pipe"]) & (df["prio"] <= df.iloc[i]["prio"])]
        full_index_list = []
        for index_g in higher_words_df["index"]:
            full_index_list += index_g
        return full_index_list

    for i in range(len(df)):
        higher_words_index = get_higher_words_index(df, i)
        if len(higher_words_index) != 0:
            for index in df.iloc[i]["index"]:
                if index in higher_words_index:
                    list_keep[i] = False
                    continue

    return df.loc[list_keep].reset_index(drop=True)


ROOT_PATH = os.path.dirname(os.path.dirname(os.getcwd()))

DATA_RAW_PATH = os.path.join(ROOT_PATH, "data", "data_raw")
DATA_CLEAN_PATH = os.path.join(ROOT_PATH, "data", "data_clean")
ENTITIES_PATH = os.path.join(ROOT_PATH, "data", "entities")
LOGS_PATH = os.path.join(ROOT_PATH, "logs", "download")

if not os.path.exists(ENTITIES_PATH):
    os.mkdir(ENTITIES_PATH)

MODELS_DIR = os.path.join(ROOT_PATH, "data", "finetuned_models")

model_name = "biobert_v1.1_2000"
tokenizer_name = "bert-base-cased"
cache_dir = "cache"

parser = argparse.ArgumentParser(description="Gimme thy name!")
parser.add_argument("--filename", help="Name of the file to display")

args = parser.parse_args()
filename = args.filename

config_bio = AutoConfig.from_pretrained(os.path.join(MODELS_DIR, model_name))
tokenizer_bio = AutoTokenizer.from_pretrained(tokenizer_name)
model_bio = AutoModelForTokenClassification.from_pretrained(os.path.join(MODELS_DIR, model_name),
                                                            from_tf=bool(".ckpt" in os.path.join(
                                                                MODELS_DIR, model_name)),
                                                            config=config_bio,
                                                            cache_dir=cache_dir)

tokenizer_base = AutoTokenizer.from_pretrained(tokenizer_name)
model_base = AutoModelForTokenClassification.from_pretrained("butchland/bert-finetuned-ner")


with open(os.path.join(DATA_CLEAN_PATH, filename), "r") as f:
    text = f.read()

pipes = {"Bio": {"pipe": pipeline("ner", model=model_bio, tokenizer=tokenizer_bio), "prio": 0},
         "Base": {"pipe": pipeline("ner", model=model_base, tokenizer=tokenizer_base), "prio": 1}}

paragraphs = text.split("\n")
entities_df = get_entities(text, pipes).reset_index(drop=True)

entities_df["entity_id"] = (entities_df["entity"].apply(lambda x: x.split("-")[0]) == "B").cumsum() - 1
full_entities_df = entities_df.groupby("entity_id").agg(list)

thresh = 3
full_entities_df = full_entities_df.loc[full_entities_df["index"].apply(largest_jump) <= thresh]

full_entities_df["start"] = full_entities_df["start"].apply(lambda x: min(x))
full_entities_df["end"] = full_entities_df["end"].apply(lambda x: max(x))
full_entities_df["pipe"] = full_entities_df["pipe"].apply(lambda x: x[0])
full_entities_df["prio"] = [pipes[full_entities_df.iloc[i]["pipe"]]["prio"] for i in range(len(full_entities_df))]
full_entities_df["paragraph_id"] = full_entities_df["paragraph_id"].apply(lambda x: int(x[0]))
full_entities_df["entity_type"] = full_entities_df["entity"].apply(lambda x: x[0].split("-")[1])
full_entities_df.rename(columns={'word': 'tokens'}, inplace=True)

full_entities_df = remove_duplicates(full_entities_df)

full_entities_df["word"] = [paragraphs[full_entities_df.iloc[i]["paragraph_id"]]
                            [full_entities_df.iloc[i]["start"]:full_entities_df.iloc[i]["end"]] for i in range(len(full_entities_df))]

full_entities_df["corrected_word"] = [corrected_word(full_entities_df.iloc[i]["start"], full_entities_df.iloc[i]
                                                     ["end"], paragraphs[full_entities_df.iloc[i]["paragraph_id"]]) for i in range(len(full_entities_df))]

with open(os.path.join(ENTITIES_PATH, args.filename.split(".")[0] + ".csv"), "wb") as f:
    full_entities_df.to_csv(f)
