from bs4 import BeautifulSoup
import requests
import os

from tqdm.auto import tqdm

from utilities import protected_get
from selenium_class import SeleniumContainer


def get_pdf_pubmed(url, selenium_cont):
    """
    Given a pubmed url, search the page to find the pdf of the article (through external sites as the actual pdf is not hosted on pubmed)
    """

    # Setting up the name of the pdf
    name = url.split('/')[-1]
    if name == "":
        name = url.split('/')[-2]

    if name in [a.split('.')[0] for a in os.listdir('data')]:
        return

    # Getting the inital page
    page = protected_get(url)

    # Making the soup, and finding links to the mirrors
    soup = BeautifulSoup(page.text, features="lxml")
    try:
        dl_link = soup.find("div", {"class": "full-text-links"}).find("a", {"class": "link-item"})
        dl_url = dl_link.get('href')
        dl_page_type = dl_link.get('data-ga-action')
    except:
        print(str(name) + " - No pdf download links")
        return

    # Making the request of the actual download page
    with protected_get(dl_url) as dl_page:

        sele_state = False

        # Making the soup
        dl_soup = BeautifulSoup(dl_page.text, features="lxml")

        # Getting the pdf link from all the different sources
        if dl_page_type == "Springer":
            pdf_link = dl_soup.find("div", {"class": "c-pdf-download"}).find("a", {"class": "u-button"})
            pdf_url = pdf_link.get("href")
        elif dl_page_type == "Wiley":
            pdf_url = "https://onlinelibrary.wiley.com/doi/pdfdirect/" + \
                '/'.join(dl_url.split("/")[-2::]) + "?download=true"
            selenium_cont.get_pdf(pdf_url, name)
            sele_state = True
            print(str(name) + " - Downloaded")
        else:
            print(str(name) + " - Type not set up: ", dl_page_type)
            return dl_page_type

        # Downloading the pdf
        if not sele_state:
            try:
                pdf = protected_get(pdf_url, stream=True)
                with tqdm.wrapattr(open(os.path.join("data", name + '.pdf'), "wb"), "write", miniters=1, total=int(pdf.headers.get('content-length', 0)), desc=name) as f_out:
                    for chunk in pdf.iter_content(chunk_size=4096):
                        f_out.write(chunk)
                print(str(name) + " - Downloaded")
            except:
                print(str(name) + " - Not downloaded")


def get_results_pubmed(search_terms):

    sele = SeleniumContainer()

    url_search = "https://pubmed.ncbi.nlm.nih.gov/?term=" + '+'.join(search_terms) + '&filter=lang.english'
    search_results_ids = []

    print("Grabbing all search results...")
    downloaded = False

    page = protected_get(url_search)
    soup = BeautifulSoup(page.text, features="lxml")
    page_ids = soup.find("div", {"class": "search-results-chunk results-chunk"}).get("data-chunk-ids").split(",")

    search_results_ids += page_ids

    page_num = 1

    while page_num < 50:
        page_num += 1
        url_page = url_search + "&page=" + str(page_num)
        try:
            page = protected_get(url_page)
            soup = BeautifulSoup(page.text, features="lxml")
            page_ids = soup.find("div", {"class": "search-results-chunk results-chunk"}
                                 ).get("data-chunk-ids").split(",")
            search_results_ids += page_ids
        except AttributeError:
            break

    print("Documents to download: ", len(search_results_ids))
    undefined_page_types = {}
    print("Downloading...")

    for name in search_results_ids:
        url = "https://pubmed.ncbi.nlm.nih.gov/" + name + "/"
        page_type = get_pdf_pubmed(url, sele)
        if isinstance(page_type, str):
            if page_type in undefined_page_types.keys():
                undefined_page_types[page_type] += 1
            else:
                undefined_page_types[page_type] = 1

    unknown_types = ""
    for key in undefined_page_types:
        unknown_types += key + ": " + str(undefined_page_types[key]) + "\n"
    with open(os.path.join("data", "types_missing.txt"), "w") as f:
        f.write(unknown_types)


if not os.path.exists("data"):
    os.makedirs("data")

search = ["anastomotic", "leakage"]
get_results_pubmed(search)
