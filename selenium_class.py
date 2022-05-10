from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import time
import os
import glob


class SeleniumContainer():

    def __init__(self):

        self.download_dir = "/home/romainc/code/Anastomosis/data/"

        # Options and Service
        op = Options()
        ser = Service(ChromeDriverManager().install())

        op.add_experimental_option('prefs', {"download.default_directory": self.download_dir,
                                             "plugins.always_open_pdf_externally": True})

        # send browser option to webdriver object
        self.driver = webdriver.Chrome(service=ser, options=op)

    def get_pdf(self, url, name):

        self.driver.get(url)
        print(self.driver.title)

        latest_file = max(glob.glob(self.download_dir + "*"), key=os.path.getctime)
        os.rename(latest_file, self.download_dir + name + '.pdf')
