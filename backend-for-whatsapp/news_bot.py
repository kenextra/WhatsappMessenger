import random
import requests
from bs4 import BeautifulSoup


def getData(url):
    r = requests.get(url)
    return r.text


def get_news():
    msgs = []
    myHtmlData = getData("https://www.aljazeera.com/tag/agriculture/")
    # https://www.mohfw.gov.in/
    soup = BeautifulSoup(myHtmlData, 'html.parser')
    for divs in soup.findAll('div', {'class': 'gc__content'}):
        for div in divs.findAll('div', {'class': 'gc__header-wrap'}):
            for anchor in div.findAll('h3'):
                title = anchor.findAll(text=True)[0]
                end_link = str(anchor.findAll('a')[0].get('href'))
                first = "Title: " + title + "\n"
                second = "Link: " + "https://www.aljazeera.com" + end_link + "\n"
                data = first + second
                msgs.append(data)

    selected = random.sample(msgs, 4)
    msg = '\n'.join(selected)
    return msg


if __name__ == '__main__':
    msg = get_news()
    print(msg)
