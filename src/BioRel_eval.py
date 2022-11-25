from collections import OrderedDict
import os
import re
import json
import math
import numpy as np

from tqdm.auto import tqdm

from constants import *

import torch
from torch import nn
from torch.nn import CrossEntropyLoss, MSELoss
from torch.utils.data import TensorDataset, random_split
from torch.utils.data import DataLoader, RandomSampler, SequentialSampler

from transformers import BertPreTrainedModel, BertModel, BertForSequenceClassification
from transformers import BertTokenizer


################################################################################
# Constants
################################################################################

if not os.path.exists(PREDICTIONS_PATH):
    os.mkdir(PREDICTIONS_PATH)

I = 5

CUDA = 0

# If there's a GPU available...
if torch.cuda.is_available():
    # Tell PyTorch to use the GPU.
    device = torch.device("cuda")
    print('There are %d GPU(s) available.' % torch.cuda.device_count())
    print('We will use the GPU:', torch.cuda.get_device_name(CUDA))
    os.environ['CUDA_VISIBLE_DEVICES'] = str(CUDA)
# If not...
else:
    print('No GPU available, using the CPU instead.')
    device = torch.device("cpu")

################################################################################
# Model classes
################################################################################


class BertForSequenceClassificationUserDefined(BertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels
        self.bert = BertModel(config)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        self.classifier = nn.Linear(2 * config.hidden_size, config.hidden_size)
        self.classifier_2 = nn.Linear(config.hidden_size, self.config.num_labels)
        self.init_weights()
        self.output_emebedding = None

    def forward(self, input_ids=None, attention_mask=None, token_type_ids=None, position_ids=None,
                head_mask=None, inputs_embeds=None, labels=None, e1_pos=None, e2_pos=None, w=None):

        outputs = self.bert(
            input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
        )  # sequence_output, pooled_output, (hidden_states), (attentions)

        e_pos_outputs = []
        sequence_output = outputs[0]
        for i in range(0, len(e1_pos)):
            e1_pos_output_i = sequence_output[i, e1_pos[i].item(), :]
            e2_pos_output_i = sequence_output[i, e2_pos[i].item(), :]
            e_pos_output_i = torch.cat((e1_pos_output_i, e2_pos_output_i), dim=0)
            e_pos_outputs.append(e_pos_output_i)
        e_pos_output = torch.stack(e_pos_outputs)
        self.output_emebedding = e_pos_output  # e1&e2 cancat output

        e_pos_output = self.dropout(e_pos_output)
        hidden = self.classifier(e_pos_output)
        logits = self.classifier_2(hidden)

        outputs = (logits,) + outputs[2:]  # add hidden states and attention if they are here

        if labels is not None:
            if self.num_labels == 1:
                #  We are doing regression
                loss_fct = MSELoss()
                loss = loss_fct(logits.view(-1), labels.view(-1))
            else:
                loss_fct = CrossEntropyLoss()
                loss = 0
                for i in range(len(w)):
                    loss += math.exp(w[i] - 1) * loss_fct(logits[i].view(-1, self.num_labels), labels[i].view(-1))
                    #loss += w[i] * loss_fct(logits[i].view(-1, self.num_labels), labels[i].view(-1))
                loss = loss / len(w)
            outputs = (loss, ) + outputs + (self.output_emebedding,)

        return outputs  # (loss), logits, (hidden_states), (attentions), (self.output_emebedding)


# f_theta1
class RelationClassification(BertForSequenceClassificationUserDefined):
    def __init__(self, config):
        super().__init__(config)


# g_theta2
class LabelGeneration(BertForSequenceClassificationUserDefined):
    def __init__(self, config):
        super().__init__(config)

################################################################################
# Pre-processing tools
################################################################################


class PreProcessing():

    def __init__(self):
        print('Loading BERT tokenizer...')
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased', do_lower_case=True)

    def pre_process(self, sentence_train, sentence_train_label):

        input_ids = []
        attention_masks = []
        labels = []
        e1_pos = []
        e2_pos = []

        # pre-processing sentenses to BERT pattern
        for i in range(len(sentence_train)):
            encoded_dict = self.tokenizer.encode_plus(
                sentence_train[i],  # Sentence to encode.
                add_special_tokens=False,  # Add '[CLS]' and '[SEP]'
                max_length=MAX_LENGTH,  # Pad & truncate all sentences.
                padding="max_length",
                truncation=True,
                return_attention_mask=True,  # Construct attn. masks.
                return_tensors='pt',  # Return pytorch tensors.
            )
            try:
                # Find e1(id:2487) and e2(id:2475) position
                pos1 = (encoded_dict['input_ids'] == 2487).nonzero()[0][1].item()
                pos2 = (encoded_dict['input_ids'] == 2475).nonzero()[0][1].item()
                e1_pos.append(pos1)
                e2_pos.append(pos2)
                # Add the encoded sentence to the list.
                input_ids.append(encoded_dict['input_ids'])
                # And its attention mask (simply differentiates padding from non-padding).
                attention_masks.append(encoded_dict['attention_mask'])
                labels.append(sentence_train_label[i])
            except:
                pass
            # print(sent)

        # Convert the lists into tensors.
        input_ids = torch.cat(input_ids, dim=0).to(device)
        attention_masks = torch.cat(attention_masks, dim=0).to(device)
        labels = torch.tensor(labels, device='cuda')
        e1_pos = torch.tensor(e1_pos, device='cuda')
        e2_pos = torch.tensor(e2_pos, device='cuda')
        w = torch.ones(len(e1_pos), device='cuda')

        # Combine the training inputs into a TensorDataset.
        train_dataset = TensorDataset(input_ids, attention_masks, labels, e1_pos, e2_pos, w)

        return train_dataset

################################################################################
# Main
################################################################################

# Constants


NUM_LABELS = 125
MAX_LENGTH = 128
BATCH_SIZE = 16

# Building relation to id maps

with open(os.path.join(ROOT_PATH, 'data', 'BioRel', 'train.json')) as f:
    train_json = json.load(f)

diff_relations = {}

for i in train_json:
    t = i["relation"]
    if t not in diff_relations.keys():
        diff_relations[t] = 1
    else:
        diff_relations[t] += 1

relation2id = {}
relation2id["NA"] = 0
cnt = 1

for rel in diff_relations.keys():
    if rel != "NA":
        relation2id[rel] = cnt
        cnt += 1

id2relation = {}
for rel in relation2id.keys():
    id2relation[relation2id[rel]] = rel

# Loading trained model

modelf1 = RelationClassification.from_pretrained(
    "bert-base-uncased",  # Use the 12-layer BERT model, with an uncased vocab.
    num_labels=NUM_LABELS,  # The number of output labels--2 for binary classification.
    # You can increase this for multi-class tasks.
    output_attentions=False,  # Whether the model returns attentions weights.
    output_hidden_states=False,  # Whether the model returns all hidden-states.
)

modelf1.to(device)

# original saved file with DataParallel
state_dict = torch.load(os.path.join(ROOT_PATH, "data", "BioRel_saved_model", "checkpoint.pt"))
# create new OrderedDict that does not contain `module.`
new_state_dict = OrderedDict()
for k, v in state_dict["model_state_dict"].items():
    name = k[7:]  # remove `module.`
    new_state_dict[name] = v

modelf1.load_state_dict(new_state_dict)
modelf1.eval()

# Building the preprocessing

pprocessing = PreProcessing()

# Running the model on our sentence and getting the predictions

for filename in tqdm(os.listdir(RELATIONS_PATH)):

    sentences_marked_list = []
    best_guess1 = []
    best_guess2 = []
    best_guess3 = []
    best_guess4 = []
    best_guess5 = []

    with open(os.path.join(DATA_CLEAN_PATH, filename.split("_")[0] + ".txt"), "r") as f:
        text = f.read()

    with open(os.path.join(ENTITIES_PATH, filename.split("_")[0] + ".csv"), "r") as f:
        entities_df = pd.read_csv(f).drop("Unnamed: 0", axis=1)

    with open(os.path.join(RELATIONS_PATH, filename), "r") as f:
        relations_df = pd.read_csv(f).drop("Unnamed: 0", axis=1)

    sentences = []

    cursor = 0
    last_end = 0

    for word, start_char, end_char in list(entities_df[["Word", "StartChar", "EndChar"]].itertuples(index=False, name=None)):
        dot = re.search("\.", text[cursor:start_char])
        if dot:
            sentences.append({"Text": text[last_end:cursor + dot.span()[0]],
                              "StartChar": last_end,
                              "EndChar": cursor + dot.span()[0]})
            last_end = cursor + dot.span()[1]
        else:
            pass
        cursor = end_char
    sentences_df = pd.DataFrame(sentences)

    for first_id, second_id, first_word, second_word, first_tui, second_tui in list(relations_df[["First", "End", "FirstWord", "EndWord", "FirstCUI", "EndCUI"]].itertuples(index=False, name=None)):
        sent_id = entities_df.iloc[first_id]["Sentence"]
        if sent_id not in sentences_df.index:
            continue
        sent_text = sentences_df.iloc[sent_id]["Text"]
        sent_start = sentences_df.iloc[sent_id]["StartChar"]
        sent_end = sentences_df.iloc[sent_id]["EndChar"]

        first_start_char = entities_df.iloc[first_id]["StartChar"]
        first_end_char = entities_df.iloc[first_id]["EndChar"]
        second_start_char = entities_df.iloc[second_id]["StartChar"]
        second_end_char = entities_df.iloc[second_id]["EndChar"]

        sent = "[CLS] " + sent_text[:first_start_char - sent_start].strip() + \
            " <e1>" + str(first_word) + "</e1>" + \
            sent_text[first_end_char - sent_start:second_start_char - sent_start] + \
            "<e2>" + str(second_word) + "</e2> " + \
            sent_text[second_end_char - sent_start:].strip() + " [SEP]"

        label = [0]

        try:
            AL_dataset = pprocessing.pre_process([sent], label)
        except:
            continue

        AL_dataloader = DataLoader(
            AL_dataset,  # The training samples.
            sampler=RandomSampler(AL_dataset),  # Select batches randomly
            batch_size=BATCH_SIZE  # Trains with this batch size.
        )

        for batch in AL_dataloader:
            # Unpack this training batch from our dataloader.
            b_input_ids = batch[0].to(device)
            b_input_mask = batch[1].to(device)
            b_labels = batch[2].to(device)
            b_e1_pos = batch[3].to(device)
            b_e2_pos = batch[4].to(device)
            b_w = batch[5].to(device)

            with torch.no_grad():
                # Forward pass, calculate logit predictions.
                (loss, logits, _) = modelf1(b_input_ids,
                                            token_type_ids=None,
                                            attention_mask=b_input_mask,
                                            labels=b_labels,
                                            e1_pos=b_e1_pos,
                                            e2_pos=b_e2_pos,
                                            w=b_w)

            logits = logits.detach().cpu().numpy()
            label_ids = b_labels.to('cpu').numpy()
            pred_flat = np.argsort(logits, axis=1).flatten()[-5:]
            labels_flat = label_ids.flatten()

        sentences_marked_list.append(sent)
        best_guess1.append(pred_flat[0])
        best_guess2.append(pred_flat[1])
        best_guess3.append(pred_flat[2])
        best_guess4.append(pred_flat[3])
        best_guess5.append(pred_flat[4])

    pred_df = pd.DataFrame({"Sentence": sentences_marked_list,
                            "Guess 1": best_guess1,
                            "Guess 2": best_guess2,
                            "Guess 3": best_guess3,
                            "Guess 4": best_guess4,
                            "Guess 5": best_guess5})

    with open(os.path.join(PREDICTIONS_PATH, filename), "w") as f:
        pred_df.to_csv(f)
