"""
Takes as input a trained model, finetuned using the colab notebook
Allows to visualize the detected words in a given piece of text
"""
import os
import argparse

from transformers import AutoConfig
from transformers import AutoTokenizer
from transformers import AutoModelForTokenClassification
from transformers import pipeline

from termcolor import colored


def corrected_ends(start, end, text):
    """
    Given a position of characters, gobbles up all characters left and right that are still in the same word
    """
    while start >= 0 and text[start].isalpha():
        start -= 1
    while end < len(text) and text[end].isalpha():
        end += 1
    return start + 1, end


def print_entities(text, pipe):
    """
    Given a pipe output, prints out all the detected entities in the text
    """

    entities = pipe(text)

    grouped_entities = []
    group = []
    found_start = False

    for entity in entities:
        if entity['entity'][0] == 'B' and not found_start:
            found_start = True
            group.append(entity)
        elif entity['entity'][0] == 'B' and found_start:
            grouped_entities.append(group)
            group = [entity]
        else:
            group.append(entity)

    if len(group) != 0:
        grouped_entities.append(group)

    last_end = 0
    colored_text = ""
    color = 'red'
    for group_e in grouped_entities:
        start = group_e[0]['start']
        end = group_e[-1]['end']
        start, end = corrected_ends(start, end, text)
        if start < last_end:
            colored_text
        colored_text += text[last_end:start] + colored(text[start:end], color)
        last_end = end
        # if color == 'red':
        #     color = 'blue'
        # elif color == 'blue':
        #     color = 'red'
    if last_end != len(text):
        colored_text += text[last_end:]

    print(colored_text)


parser = argparse.ArgumentParser(description="Gimme thy name!")
parser.add_argument("--filename", help="Name of the file to display")

args = parser.parse_args()

DATA_DIR = "data_clean"
MODELS_DIR = "finetuned_models"

model_name = "biobert_v1.1_2000"
tokenizer_name = "bert-base-cased"
cache_dir = "cache"

filename = args.filename

config = AutoConfig.from_pretrained(os.path.join(MODELS_DIR, model_name))
tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
model = AutoModelForTokenClassification.from_pretrained(os.path.join(MODELS_DIR, model_name),
                                                        from_tf=bool(".ckpt" in os.path.join(MODELS_DIR, model_name)),
                                                        config=config,
                                                        cache_dir=cache_dir)

with open(os.path.join(DATA_DIR, filename), "r") as f:
    text = f.read()

pipe = pipeline("ner", model=model, tokenizer=tokenizer)

paragraphs = text.split("\n")
for p in paragraphs:
    print_entities(p, pipe)
