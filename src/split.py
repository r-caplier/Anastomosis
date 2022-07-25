import os
import json
import pandas as pd

from sklearn.model_selection import train_test_split
from tqdm.auto import tqdm

from constants import *

with open(os.path.join(ROOT_PATH, "data", "train_sentences_full.json"), "r") as f:
    list_sentences = json.load(f)

with open(os.path.join(ROOT_PATH, "data", "train_label_id_full.json"), "r") as f:
    list_labels = json.load(f)

data_dict = {"Sentence": list_sentences, "Label": list_labels}
data_df = pd.DataFrame(data_dict)

NUM_TRAIN_PER_CLASS = 40
NUM_TRAIN_NO_RELATION = 2000
NUM_TRAIN_NO_LABEL = 4000

NUM_TEST_PER_CLASS = 20
NUM_TEST_NO_RELATION = 100

NO_RELATION_LABEL = 0
RELATION_LABEL = 1
FULL_LABEL = True

train_sentences_full = []
train_labels_full = []
test_sentences_full = []
test_labels_full = []
dict_idx = {}

cnt = 0
for i in sorted(data_df["Label"].unique()):
    dict_idx[i] = cnt
    cnt += 1

for i in data_df["Label"].unique():

    potential_df = data_df.loc[data_df["Label"] == i]["Sentence"]

    if i == 0:
        train_sent, test_sent = train_test_split(
            potential_df.values, train_size=NUM_TRAIN_NO_RELATION, test_size=NUM_TEST_NO_RELATION)
        if FULL_LABEL:
            train_labels = [int(dict_idx[i])] * NUM_TRAIN_NO_RELATION
            test_labels = [int(dict_idx[i])] * NUM_TEST_NO_RELATION
        else:
            train_labels = [NO_RELATION_LABEL] * NUM_TRAIN_NO_RELATION
            test_labels = [NO_RELATION_LABEL] * NUM_TEST_NO_RELATION
    else:
        train_sent, test_sent = train_test_split(
            potential_df.values, train_size=NUM_TRAIN_PER_CLASS, test_size=NUM_TEST_PER_CLASS)
        if FULL_LABEL:
            train_labels = [int(dict_idx[i])] * NUM_TRAIN_PER_CLASS
            test_labels = [int(dict_idx[i])] * NUM_TEST_PER_CLASS
        else:
            train_labels = [RELATION_LABEL] * NUM_TRAIN_PER_CLASS
            test_labels = [RELATION_LABEL] * NUM_TEST_PER_CLASS

    train_sentences_full += list(train_sent)
    test_sentences_full += list(test_sent)
    train_labels_full += train_labels
    test_labels_full += test_labels

# train_sentences_full += random.sample(list(data_df["Sentence"].values), NUM_TRAIN_NO_LABEL)
# train_labels_full += [NO_LABEL_LABEL] * NUM_TRAIN_NO_LABEL

json_o_train_sentences = json.dumps(train_sentences_full)
json_o_test_sentences = json.dumps(test_sentences_full)
json_o_train_labels = json.dumps(train_labels_full)
json_o_test_labels = json.dumps(test_labels_full)

with open("train_sentence.json", "w") as f:
    f.write(json_o_train_sentences)

with open("train_label_id.json", "w") as f:
    f.write(json_o_train_labels)

with open("test_sentence.json", "w") as f:
    f.write(json_o_test_sentences)

with open("test_label_id.json", "w") as f:
    f.write(json_o_test_labels)
