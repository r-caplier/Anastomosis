import os
import argparse

from tqdm.auto import tqdm

from download.download import DownloaderClass
from download.cleaner import CleanerClass

from paths import *

with open("token", "r") as f:
    os.environ['GH_TOKEN'] = f.read().strip()

if not os.path.exists(LOGS_PATH):
    os.mkdir(LOGS_PATH)

if not os.path.exists(LOGS_DOWNLOAD_PATH):
    os.mkdir(LOGS_DOWNLOAD_PATH)

if not os.path.exists(DATA_RAW_PATH):
    os.mkdir(DATA_RAW_PATH)

if not os.path.exists(DATA_CLEAN_PATH):
    os.mkdir(DATA_CLEAN_PATH)

default_search_terms = ["anastomotic", "leak"]

parser = argparse.ArgumentParser(description="Downloading script for PubMed")
parser.add_argument("--search_terms",
                    nargs='+',
                    default=default_search_terms,
                    help="Search terms to use in the PubMed query")
parser.add_argument("--overwrite",
                    type=bool,
                    default=False,
                    help="Whether or not to force the script to rebuild the list of articles to download")
parser.add_argument("--num_pages",
                    type=int,
                    default=-1,
                    help="Number of pages to go through (leave empty to download everything; ignored if overwrite is not set to True and a file is already present)")

args = parser.parse_args()

if args.num_pages < 0:
    max_num_pages = False
else:
    max_num_pages = args.num_pages

downloader = DownloaderClass()
downloader.download(args.search_terms, max_page_num=max_num_pages, overwrite=args.overwrite)

print("Cleaning text...")
cleaner = CleanerClass()
for file_name in tqdm(os.listdir(DATA_RAW_PATH)):
    text = cleaner.clean(file_name)
    with open(os.path.join(DATA_CLEAN_PATH, file_name.split('.')[0] + '.txt'), "w") as f:
        f.write(text)
