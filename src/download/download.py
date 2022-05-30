import os
import time
import requests
import re
import pickle

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from tqdm.auto import tqdm

ROOT_PATH = os.path.dirname(os.getcwd())
DEV_NULL_PATH = "/dev/null"

DATA_PATH = os.path.join(ROOT_PATH, "data", "data_raw")
LOGS_PATH = os.path.join(ROOT_PATH, "logs", "download")

os.environ['GH_TOKEN'] = "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"


def get_wiley(soup):

    try:
        paragraphs = []
        abstract = soup.find("section", {"class": "article-section article-section__abstract"})
        if abstract != None:
            paragraphs += abstract.find_all("p")
        sections = soup.find("section", {"class": "article-section article-section__full"})
        if sections != None:
            good_sections = sections.find_all("section", {"class": "article-section__content"})
            if good_sections != None:
                for section in good_sections:
                    paragraphs += section.find_all("p")

        return True, '\n'.join([re.sub("<.{1,2}>", "", paragraph.text) for paragraph in paragraphs])

    except:
        return False, "Error Fetching"


def get_springer(soup):

    try:
        article = soup.find("div", {"class": "c-article-body"})
        paragraphs = article.find_all(re.compile("[section|div]"), recursive=False)

        good_paragraphs = []
        i = 0
        found = False
        while i < len(paragraphs) and not found:
            if paragraphs[i].find("section", {"data-title": "References"}) != None:
                found = True
            else:
                for p in paragraphs[i].find_all("p"):
                    good_paragraphs.append(p)
                i += 1

        article_text = '\n'.join([re.sub("<.{1,2}>", "", paragraph.text) for paragraph in good_paragraphs])

        return True, re.sub("Access provided by ETH Zürich Elektronische Ressourcen\n", "", article_text)

    except:
        return False, "Error Fetching"


def get_elsevier(soup):

    try:
        abstract = soup.find("div", {"id": "abstracts"})
        if abstract != None:
            abstract_text = '\n'.join([re.sub("<.{1,2}>", "", paragraph.text) for paragraph in abstract.find_all("p")])
        else:
            abstract_text = ""

        body = soup.find("div", {"id": "body"}).find("div", {"class": ""})
        body_text = '\n'.join([re.sub("<.{1,2}>", "", paragraph.text) for paragraph in body.find_all("p")])

        return True, abstract_text + '\n' + body_text

    except:
        return False, "Error Fetching"


IMPLEMENTED_WEBSITES = {
    "Wiley": get_wiley,
    "Springer": get_springer,
    "Elsevier Science": get_elsevier,
}


class DownloaderClass():

    def __init__(self):

        self.ser = Service(GeckoDriverManager().install())

    def _pget(self, url, stream=False):
        """
        Acounts for network errors in   getting a request (Pubmed often appears offline, but not for long periods of time)
        Retries every 2 seconds for 60 seconds and then gives up
        """
        downloaded = False
        count = 0

        while not downloaded and count < 60:
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

    def _get_page(self, url):

        options = webdriver.FirefoxOptions()
        options.headless = True
        browser = webdriver.Firefox(options=options, service=self.ser)

        browser.get(url)
        time.sleep(2)
        html = browser.page_source
        soup = BeautifulSoup(html, features='lxml')

        browser.close()

        return soup

    def _get_search_matches(self, search_terms, max_page_num=False):
        """
        From a collection of search terms, get all of the ids of articles matching those search criterias
        Optionnaly, set a max number of pages to search through (10 articles per page)
        """
        # Filtering out every non English match
        search_url = "https://pubmed.ncbi.nlm.nih.gov/?term=" + '+'.join(search_terms) + '&filter=lang.english'
        full_search_ids = []

        # Grabs every page
        page_num = 0
        while (max_page_num and page_num < max_page_num) or not max_page_num:
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
        self.search_results_ids = full_search_ids

    def _get_article_text(self, article_id):
        """
        Given a Pubmed article id, finds the url of the corresponding article, if freely available
        Needs manual implementation for each publishing site, feeel free to add some
        """
        # Tracks whether or not the url was found
        found = True

        # Getting the inital page
        pubmed_url = "https://pubmed.ncbi.nlm.nih.gov/" + article_id + "/"
        pubmed_page = self._pget(pubmed_url)
        pubmed_soup = BeautifulSoup(pubmed_page.text, features="lxml")

        # Grabbing download links if available
        try:
            dl_features = pubmed_soup.find("div", {"class": "full-text-links"}).find("a", {"class": "link-item"})
            dl_url = dl_features.get('href')
            dl_page_type = dl_features.get('data-ga-action')
        except:
            return False, str(article_id) + " - No article links found"

        if dl_page_type in IMPLEMENTED_WEBSITES.keys():
            soup = self._get_page(dl_url)
            response, text = IMPLEMENTED_WEBSITES[dl_page_type](soup)
            if response:
                return response, text
            else:
                return response, str(article_id) + f" - {dl_page_type}: Error in HTML"
        else:
            return False, str(article_id) + f" - {dl_page_type}: Not implemented"

    def download(self, search_terms, max_page_num=False, overwrite=False):
        """
        Downloads the pdfs of matching search results
        """
        save_search_id_name = "full_search_ids_" + "_".join(search_terms) + ".pkl"

        if not os.path.exists(os.path.join(LOGS_PATH, save_search_id_name)) or overwrite:
            print("\n\nGrabbing all search results...")
            self._get_search_matches(search_terms, max_page_num=max_page_num)
            with open(os.path.join(LOGS_PATH, save_search_id_name), "wb") as f:
                pickle.dump(self.search_results_ids, f)
        else:
            print("\n\nFound already pre-downloaded search results!")
            with open(os.path.join(LOGS_PATH, save_search_id_name), "rb") as f:
                self.search_results_ids = pickle.load(f)
        print(f"Found {len(self.search_results_ids)} matching documents.")

        print("Downloading...")
        doc_num = 0
        found_num = 0
        found_dict = {"Name": [], "PubMedID": [], "Path": []}
        log = "Logged actions -------------------\n"

        for article_id in tqdm(self.search_results_ids):
            doc_num += 1
            found, text = self._get_article_text(article_id)

            if found:
                found_num += 1
                article_path = os.path.join(DATA_PATH, article_id + ".txt")
                with open(article_path, "w") as f:
                    f.write(text)
                log += article_id + " - Downloaded\n"
            else:
                log += text + "\n"

        time.sleep(1)

        log = f"Downloaded {found_num}/{len(self.search_results_ids)} documents\n" + log
        with open(os.path.join(LOGS_PATH, "download_log.txt"), "w") as f:
            f.write(log)

        os.remove("geckodriver.log")


if __name__ == "__main__":

    if not os.path.exists(LOGS_PATH):
        os.mkdir(LOGS_PATH)

    if not os.path.exists(DATA_PATH):
        os.mkdir(DATA_PATH)

    dl = Downloader()
    dl.download(['anastomotic', 'leak'], max_page_num=False)
