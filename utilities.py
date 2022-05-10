import requests
import time

def protected_get(url, stream=False):
    """
    Acounts for network errors in getting a request
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
