from bs4 import BeautifulSoup
import requests
import os

if not os.path.exists("data"):
    os.makedirs("data")

def get_pdf_pubmed(url):
    """
    Given a pubmed url, search the page to find the pdf of the article (through external sites as the actual pdf is not hosted on pubmed)
    """

    name = url.split('/')[-1]
    if name == "":
        name = url.split('/')[-2]

    page = requests.get(url)

    soup = BeautifulSoup(page.text, features="lxml")
    dl_link = soup.find("div", {"class": "full-text-links"}).find("a", {"class": "link-item"})
    dl_url = dl_link.get('href')
    dl_page_type = dl_link.get('data-ga-action')

    dl_page = requests.get(dl_url)
    dl_soup = BeautifulSoup(dl_page.text, features="lxml")

    if dl_page_type == "Springer":
        pdf_link = dl_soup.find("div", {"class": "c-pdf-download"}).find("a", {"class": "u-button"})
        pdf_url = pdf_link.get("href")

        pdf = requests.get(pdf_url)
        with open(os.path.join("data", name + '.pdf'), "wb") as f:
            f.write(pdf.content)

    else:
        print("Type not set up: ", dl_page_type)

get_pdf_pubmed("https://pubmed.ncbi.nlm.nih.gov/34100248/")
