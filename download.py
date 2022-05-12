import os
import shutil
import glob
import time
import pickle
import pandas as pd

import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfFileReader

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from tqdm.auto import tqdm

LOGS_PATH = "logs"

# Todo : Add a tool to find out how many citations per article


class Downloader():

    def __init__(self):

        self.download_dir = "/home/romainc/code/Anastomosis/data_temp/"

        # Options and Service
        op = Options()
        ser = Service(ChromeDriverManager().install())

        op.add_experimental_option('prefs', {"download.default_directory": self.download_dir,
                                             "plugins.always_open_pdf_externally": True})

        # send browser option to webdriver object
        self.driver = webdriver.Chrome(service=ser, options=op)

    def _pget(self, url, stream=False):
        """
        Acounts for network errors in getting a request (Pubmed often appears offline, but not for long periods of time)
        Retries every 2 seconds for 60 seconds and then gives up
        """
        downloaded = False
        count = 0

        while not downloaded and count < 30:
            try:
                page = requests.get(url, stream=stream)
                downloaded = True
            except:
                print(url + f" - Network error, retrying... ({count + 1})")
                time.sleep(2)
                count += 1

        if page != None:
            return page
        else:
            raise ValueError

    def _get_title(self, pdf_path):
        if os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as f:
                pdf = PdfFileReader(f, strict=False)
                return pdf.getDocumentInfo().title
        else:
            return "Title not found"

    def _get_search_matches(self, search_terms):
        """
        From a collection of search terms, get all of the ids of articles matching those search criterias
        """
        # Filtering out every non English match
        search_url = "https://pubmed.ncbi.nlm.nih.gov/?term=" + '+'.join(search_terms) + '&filter=lang.english'
        full_search_ids = []

        # Grabs every page
        page_num = 0
        while page_num < 2:
            page_num += 1
            if page_num != 1:
                page_url = search_url + "&page=" + str(page_num)
            else:
                page_url = search_url
            try:
                page = self._pget(page_url)
                page_soup = BeautifulSoup(page.text, features="lxml")
                page_ids = page_soup.find("div", {"class": "search-results-chunk results-chunk"}
                                          ).get("data-chunk-ids").split(",")
                full_search_ids += page_ids
            except AttributeError:
                break

        # Saving the results
        self.full_search_ids = full_search_ids

    def _get_pdf_url(self, pdf_id):
        """
        Given a Pubmed article id, finds the url of the corresponding pdf, if freely available
        Needs manual implementation for each publishing site, feeel free to add some
        """
        # Tracks whether or not the url was found
        found = True

        # Getting the inital page
        pubmed_url = "https://pubmed.ncbi.nlm.nih.gov/" + pdf_id + "/"
        pubmed_page = self._pget(pubmed_url)
        pubmed_soup = BeautifulSoup(pubmed_page.text, features="lxml")

        # Grabbing download links if available
        try:
            dl_features = pubmed_soup.find("div", {"class": "full-text-links"}).find("a", {"class": "link-item"})
            dl_url = dl_features.get('href')
            dl_page_type = dl_features.get('data-ga-action')
        except:
            return False, str(pdf_id) + " - No pdf download links"

        # Types of download source - Please add more
        if dl_page_type == "Springer":
            with self._pget(dl_url) as page_dl:
                soup_dl = BeautifulSoup(page_dl.text, features="lxml")
                pdf_url = soup_dl.find("div", {"class": "c-pdf-download"}).find("a", {"class": "u-button"}).get('href')

        # elif dl_page_type == "Wiley":
        #     pdf_url = "https://onlinelibrary.wiley.com/doi/pdfdirect/" + \
        #         '/'.join(dl_url.split("/")[-2::]) + "?download=true"

        else:
            found = False
            pdf_url = str(pdf_id) + " - Type not set up: " + dl_page_type

        return found, pdf_url

    def _download_pdf(self, pdf_id, pdf_url):
        """
        Given the url of a pdf, downloads it (should bypass DDOS protection mecanisms)
        """
        self.driver.get(pdf_url)
        while len(os.listdir("data_temp")) == 0:
            time.sleep(0.1)
        latest_file = max(glob.glob(os.path.join("data_temp", "*")), key=os.path.getctime)
        while latest_file.split(".")[-1] == 'crdownload':
            time.sleep(0.1)
            latest_file = max(glob.glob(os.path.join("data_temp", "*")), key=os.path.getctime)
        os.rename(latest_file, os.path.join("data", pdf_id + ".pdf"))

    def download(self, search_terms):
        """
        Downloads the pdfs of matching search results
        """
        save_search_id_name = "full_search_ids_" + "_".join(search_terms) + ".pkl"

        if not os.path.exists(os.path.join(LOGS_PATH, save_search_id_name)):
            print("\n\nGrabbing all search results...")
            self._get_search_matches(search_terms)
            with open(os.path.join(LOGS_PATH, save_search_id_name), "wb") as f:
                pickle.dump(self.full_search_ids, f)
        else:
            print("\n\nFound already pre-downloaded search results!")
            with open(os.path.join(LOGS_PATH, save_search_id_name), "rb") as f:
                self.full_search_ids = pickle.load(f)
        print(f"Found {len(self.full_search_ids)} matching documents.")

        print("Downloading...")
        doc_num = 0
        found_num = 0
        found_dict = {"Name": [], "PubMedID": [], "Path": []}
        log = "Logged actions -------------------\n"

        for pdf_id in tqdm(self.full_search_ids):
            doc_num += 1
            found, pdf_url = self._get_pdf_url(pdf_id)

            if found:
                found_num += 1
                self._download_pdf(pdf_id, pdf_url)
                pdf_path = os.path.join("data", pdf_id + ".pdf")
                found_dict["Name"].append("Undefined")
                found_dict["PubMedID"].append(pdf_id)
                found_dict["Path"].append(pdf_path)
                log += pdf_id + " - Downloaded\n"
            else:
                log += pdf_url + "\n"

            if doc_num % 10 == 0:
                found_df = pd.DataFrame(found_dict)
                found_df.to_csv(os.path.join(LOGS_PATH, "search_results.csv"))

        time.sleep(1)
        found_dict["Name"] = [self._get_title(title) for title in found_dict["Path"]]
        found_df = pd.DataFrame(found_dict)
        found_df.to_csv(os.path.join(LOGS_PATH, "search_results.csv"))

        log = f"Downloaded {found_num}/{len(self.full_search_ids)} documents\n" + log
        with open(os.path.join(LOGS_PATH, "download_log.txt"), "w") as f:
            f.write(log)

        if os.path.exists("data_temp"):
            shutil.rmtree("data_temp")

        self.driver.close()


if __name__ == "__main__":

    if not os.path.exists(LOGS_PATH):
        os.mkdir(LOGS_PATH)

    if not os.path.exists("data"):
        os.mkdir("data")

    if os.path.exists("data_temp") and len(os.listdir("data_temp")) > 0:
        shutil.rmtree("data_temp")

    if not os.path.exists("data_temp"):
        os.mkdir("data_temp")

    dl = Downloader()
    dl.download(['anastomotic', 'leak'])
