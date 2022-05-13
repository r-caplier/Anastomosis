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
END_WORDS = ["acknowledgments", "references"]
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
        Given raw text, removes all non viable patterns left in
        List of bad patterns can be updated freely
        """
        blocks = raw_text.split("\n")
        clean_blocks = []
        for block in blocks:
            for pattern in BAD_PATTERNS:
                if pattern["type"] == "pattern":
                    clean_block = re.sub(pattern["pattern"], "", block)
                elif pattern["type"] == "block" and re.search(pattern["pattern"], block):
                    clean_block = ""
            clean_blocks.append(clean_block)

        return clean_blocks

    def _text_cleaner(self, raw_text):
        """
        Given raw text output from a pdf, reorganises it by removing formatting
        """
        text = ""
        lines = raw_text.split("\n")
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

    def get_raw_text(self, file_name):
        """
        Given a file name, returns the raw text inside of it
        Cuts everything so that only the text between the abstract and the end sections stays.
        """
        file_path = os.path.join("data", file_name)

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

        return raw_text[start_id:end_id]

    def get_abstract_title(self, file_name):

        file_path = os.path.join("data", file_name)

        if os.path.exists(file_path):

            raw_text = self._extract_text_pdf(file_path)
            start_id = raw_text.lower().find("abstract") + 8
            if start_id == -1:
                print("Abstract not found")
                abstract = ""
            else:
                abstract = self._text_cleaner(raw_text[start_id:].split(".\n")[0])

            with open(file_path, 'rb') as f:
                pdf = PdfFileReader(f, strict=False)
                title = pdf.getDocumentInfo().title
            if title == None:
                title = ""
        else:
            raise FileNotFoundError()

        return title, abstract

    def save_text(self, file_name, clean_paragraphs):

        with open(os.path.join(DATA_CLEAN_PATH, file_name.split('.')[0] + ".txt"), "w") as f:
            f.write('\n\n'.join(clean_paragraphs))


if not os.path.exists(DATA_CLEAN_PATH):
    os.mkdir(DATA_CLEAN_PATH)

if not os.path.exists(ABSTRACTS_PATH):
    os.mkdir(ABSTRACTS_PATH)

extractor = PdfTextExtractor()

file_name = "21107847.pdf"
raw_text = extractor._extract_text_pdf(os.path.join("data", file_name))
raw_text_clean = extractor._text_cleaner(raw_text)
print(extractor._text_cleaner(raw_text))
print("\n")
print(extractor._text_cleaner(raw_text_clean))

# abstract_dict = {"Title": [], "Abstract": []}
#
# for file_name in tqdm(os.listdir("data")):
#     title, abstract = extractor.get_abstract_title(file_name)
#     abstract_dict["Title"].append(title)
#     abstract_dict["Abstract"].append(abstract)
#     with open(os.path.join(ABSTRACTS_PATH, file_name.split('.')[0] + '_abstract.txt'), "w") as f:
#         f.write('Title: ' + title)
#         f.write('\nAbstract' + abstract)
# abstract_df = pd.DataFrame(abstract_dict)
# abstract_df.to_csv(os.path.join(ABSTRACTS_PATH, "abstracts.csv"))
