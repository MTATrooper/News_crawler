import os
import time
import threading
import requests
from utils import load_json
from news_crawler.spiders.dantri import CATEGORIES as dantri_categories, URL as dantri_url, NAME as dantri_name
from news_crawler.spiders.vnexpress import CATEGORIES as vnexpress_categories, URL as vnexpress_url, NAME as vnexpress_name

pages = {'dantri': dantri_categories,
        'vnexpress': vnexpress_categories}
urls = {'dantri': dantri_url,
        'vnexpress': vnexpress_url}
fullnames = {'dantri': dantri_name,
        'vnexpress': vnexpress_name}

DATA_DIR = './data'

def insertDB(page):
    PAGE_DIR = os.path.join(DATA_DIR, page)
    for filename in os.listdir(PAGE_DIR):
        data = load_json(os.path.join(PAGE_DIR, filename))
        for news in data:
            dic = {'news': news}
            requests.post('http://localhost:5555/insertnews', json=dic)

def crawl_data(pages):
    start = time.time()

    while True:
        for page in pages:
            os.makedirs('%s/%s' % (DATA_DIR, page))
            for category in pages[page]:
                os.system('scrapy crawl %s -a category=%s -a limit=1 -o %s/%s/%s.json' % (page, category, DATA_DIR, page, category))
            insertDB(page)
        # with open('log%s.txt' % list(pages.keys())[0], 'w') as f:
        #     f.writelines('page %s: %d' % (list(pages.keys())[0], int(time.time() - start)))
        while True:
            if int(time.time() - start) % 300 == 0:
                for page in pages:
                    os.system('rm -r %s/%s'% (DATA_DIR, page))
                break
if __name__ == '__main__':
    try:
        dic = {'pages': pages,
                'urls': urls,
                'fullnames': fullnames}
        requests.post('http://localhost:5555/insertsource', json=dic)
        pages_1 = dict(list(pages.items())[:len(pages)//2])
        pages_2 = dict(list(pages.items())[len(pages)//2:])
        crawl_1 = threading.Thread(target=crawl_data, args=(pages_1,), daemon= True)
        crawl_2 = threading.Thread(target=crawl_data, args=(pages_2,), daemon= True)
        crawl_1.start()
        crawl_2.start()
        crawl_1.join()
        crawl_2.join()
    except:
        print('Exit!')