import subprocess
import os

from tqdm.auto import tqdm

START_WORDS = ["abstract", "purpose"]
END_WORDS = ["acknowledgments", "references"]
DATA_CLEAN_PATH = "data_clean"


class PdfTextExtractor():

    def __init__(self):
        pass

    def get_text(self, file_name):

        file_path = os.path.join("data", file_name)

        raw_text = subprocess.run(["pdf2txt.py", file_path], stdout=subprocess.PIPE).stdout.decode("utf-8")
        start_id = raw_text.lower().find("abstract") + 8
        try:
            end_id = min([raw_text.lower().find(end_word)
                         for end_word in END_WORDS if raw_text.lower().find(end_word) > 0])
        except:
            end_id = len(raw_text)
        paragraphs = raw_text[start_id:end_id].split(".\n")
        clean_paragraphs = []

        for raw_paragraph in paragraphs:
            paragraph = ""
            lines = raw_paragraph.split("\n")
            for line_id in range(len(lines)):
                space = True
                line = lines[line_id]
                if len(line) != 0 and line[-1] == "-":
                    line = line[:-1]
                    space = False
                paragraph += line
                if space and len(line) != 0 and line_id != len(lines) - 1:
                    paragraph += " "
            paragraph += "."
            clean_paragraphs.append(paragraph)

        self.clean_paragraphs = clean_paragraphs

    def save_text(self, file_name):

        with open(os.path.join(DATA_CLEAN_PATH, file_name.split('.')[0] + ".txt"), "w") as f:
            f.write('\n\n'.join(self.clean_paragraphs))


if not os.path.exists(DATA_CLEAN_PATH):
    os.mkdir(DATA_CLEAN_PATH)

extractor = PdfTextExtractor()

for file_name in tqdm(os.listdir("data")):
    extractor.get_text(file_name)
    extractor.save_text(file_name)
