import subprocess
import os
import argparse
import re
import pandas as pd

from tqdm.auto import tqdm

ROOT_PATH = os.path.dirname(os.path.dirname(os.getcwd()))

DATA_RAW_PATH = os.path.join(ROOT_PATH, "data", "data_raw")
DATA_CLEAN_PATH = os.path.join(ROOT_PATH, "data", "data_clean")
LOGS_PATH = os.path.join(ROOT_PATH, "logs", "download")

BAD_PATTERNS = [
    {"pattern": r"\[([0-9][,-–]? ?)+\],?", "type": "pattern"}, # References mentions [3] or [4-9]
    {"pattern": r"\D[0-9]{1,2},", "type": "pattern"}, # References mentions 3, 4, 7
    {"pattern": r"([a-zA-Z%])([,\.]*)[0-9]+", "type": "pattern", "replace": r"\1\2"}, # References mention Text.2 or 35%.4 or Text,3
    {"pattern": r"\(.*?\)", "type": "pattern"}, # Anything in parentheses, not greedy matching
    {"pattern": r"i[iv]*\)", "type": "pattern"}, # Roman bullet points in paragraphs
]


class CleanerClass():

    def __init__(self):
        pass

    def _pattern_remover(self, text):
        """
        Given raw text, removes all non viable patterns left in it.
        List of bad patterns can be updated freely, see bad_patterns.py
        """
        for pattern in BAD_PATTERNS:
            if pattern["type"] == "pattern":
                if "replace" in pattern.keys():
                    text = re.sub(pattern["pattern"], pattern["replace"], text)
                else:
                    text = re.sub(pattern["pattern"], "", text)
            elif pattern["type"] == "full" and re.search(pattern["pattern"], text):
                text = ""

        return text.strip()

    def _finishing_steps(self, text):
        """
        Takes in a cleaned up string of text (unwanted patterns already removed)
        Removes doubles spaces
        Removes spaces before periods
        Removes spaces before comma
        Removes double line skips
        Removes all punctuation
        """
        text = re.sub(" +", " ", text)
        text = re.sub(" \.", ".", text)
        text = re.sub(" ,", ",", text)
        text = re.sub("\n+", "\n", text)
        # text = re.sub(r"[^\w\s]", "", text)
        return text

    def clean(self, file_name):

        with open(os.path.join(DATA_RAW_PATH, file_name), 'r') as f:
            text = f.read()

        paragraphs = text.split('\n')
        clean_paragraphs = []

        for p in paragraphs:
            clean_p = self._pattern_remover(p)
            clean_paragraphs.append(clean_p)

        return self._finishing_steps('\n'.join(clean_paragraphs))

if __name__ == '__main__':
    print("Cleaning text...")
    cleaner = CleanerClass()
    for file_name in tqdm(os.listdir(DATA_RAW_PATH)):
        text = cleaner.clean(file_name)
        with open(os.path.join(DATA_CLEAN_PATH, file_name.split('.')[0] + '.txt'), "w") as f:
            f.write(text)
