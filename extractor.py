import subprocess
import os
import re
import pandas as pd
from io import StringIO

from PyPDF2 import PdfFileReader

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from tqdm.auto import tqdm

from bad_patterns import BAD_PATTERNS

START_WORDS = ["abstract", "purpose"]
END_WORDS = ["acknowledgments", "references", "conflict of interest", "conflicts of interest"]
DATA_CLEAN_PATH = "data_clean"
ABSTRACTS_PATH = "abstracts"


class PdfTextExtractor():

    def __init__(self):
        pass

    def _extract_text_pdf(self, file_path):
        """
        Given a pdf file path, returns the text content of the pdf
        """
        output_string = StringIO()
        with open(file_path, 'rb') as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)

        return output_string.getvalue()

    def _pattern_remover(self, text):
        """
        Given raw text, removes all non viable patterns left in it.
        List of bad patterns can be updated freely, see bad_patterns.py
        """
        lines = text.split("\n")
        clean_lines = []
        for line in lines:
            for pattern in BAD_PATTERNS:
                if pattern["type"] == "pattern":
                    line = re.sub(pattern["pattern"], "", line)
                elif pattern["type"] == "block" and re.search(pattern["pattern"], line):
                    line = ""
            clean_lines.append(line)

        return clean_lines

    def _text_maker(self, lines):
        """
        Given a list of lines, recombines them into one string of characters
        """
        text = ""
        for line_id in range(len(lines)):
            space = True
            line = lines[line_id]
            if len(line) != 0 and line[-1] == "-":
                line = line[:-1]
                space = False
            text += line
            if space and len(line) != 0 and line_id != len(lines) - 1:
                text += " "
        text += "."

        return text

    def _remove_punct(self, text):
        """
        Takes in a cleaned up string of texte, removes all punctuation and cleans up the multiple spaces left
        Might add lowercasing all, could be a good idea
        Making sure to keep the % sign
        """
        return re.sub(r"[^\w\s^.]", "", text)

    def get_text(self, file_name):
        """
        Given a file name, returns the cleaned up text inside of it.
        Cuts everything so that only the text between the abstract and the end sections stays.
        Does a pass of pattern removal.
        """
        file_path = os.path.join("data", file_name)

        if os.path.exists(file_path):
            raw_text = self._extract_text_pdf(file_path)

            start_id = raw_text.lower().find("abstract")
            if start_id == -1:
                start_id = 0
            else:
                start_id += 8

            try:
                end_id = min([raw_text.lower().find(end_word)
                              for end_word in END_WORDS if raw_text.lower().find(end_word) > 0])
            except:
                end_id = len(raw_text)

            clean_lines = self._pattern_remover(raw_text[start_id:end_id])
            text = self._text_maker(clean_lines)
            return self._remove_punct(text)

        else:
            return "File not found: " + file_path

    def get_abstract(self, file_name):

        file_path = os.path.join("data", file_name)

        if os.path.exists(file_path):

            raw_text = self._extract_text_pdf(file_path)
            start_id = raw_text.lower().find("abstract") + 8
            if start_id == -1:
                print("Abstract not found")
            else:
                clean_abstract = self._pattern_remover(raw_text[start_id:].split(".\n\n")[0])
                abstract_text = self._text_maker(clean_abstract)
                return self._remove_punct(abstract_text)

        else:
            return "File not found: " + file_path

    def save_text(self, file_name, clean_paragraphs):

        with open(os.path.join(DATA_CLEAN_PATH, file_name.split('.')[0] + ".txt"), "w") as f:
            f.write('\n\n'.join(clean_paragraphs))


if not os.path.exists(DATA_CLEAN_PATH):
    os.mkdir(DATA_CLEAN_PATH)

if not os.path.exists(ABSTRACTS_PATH):
    os.mkdir(ABSTRACTS_PATH)

extractor = PdfTextExtractor()

for file_name in tqdm(os.listdir("data")):
    text = extractor.get_text(file_name)
    with open(os.path.join(DATA_CLEAN_PATH, file_name.split('.')[0] + '.txt'), "w") as f:
        f.write(text)
