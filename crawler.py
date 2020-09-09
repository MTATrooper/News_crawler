import os
from news_crawler.spiders.dantri import CATEGORIES as dantri_categories
from news_crawler.spiders.vnexpress import CATEGORIES as vnexpress_categories
from utils import load_json
import time
import threading
from pymongo import MongoClient
import requests

pages_1 = {'dantri': dantri_categories}
pages_2 = {'vnexpress': vnexpress_categories}

DATA_DIR = './data'
client = MongoClient(port=27017)
db=client.newspaper

def insertDB(page):
    PAGE_DIR = os.path.join(DATA_DIR, page)
    for filename in os.listdir(PAGE_DIR):
        data = load_json(os.path.join(PAGE_DIR, filename))
        for news in data:
            find = db.news.find_one({'link': news['link']})
            if len(news['content']) >= 5 and news['title'] is not None and news['date'] is not None and find is None:
                content = ' '.join(news['content'] if len(news['content'][-1]) > 30 else news['content'][:-1])
                dic = {'text': content}
                respond = requests.post('http://localhost:5555/summary', json=dic)
                news['summary'] = respond.json()['key']
                db.news.insert_one(news)

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
            if int(time.time() - start) % 180 == 0:
                for page in pages:
                    os.system('rm -r %s/%s'% (DATA_DIR, page))
                break
if __name__ == '__main__':
    try:
        for page in pages_1:
            find = db.source.find_one({'name': page})
            if find is None:
                db.source.insert_one({'name': page})
        for page in pages_2:
            find = db.source.find_one({'name': page})
            if find is None:
                db.source.insert_one({'name': page})
        crawl_1 = threading.Thread(target=crawl_data, args=(pages_1,), daemon= True)
        crawl_2 = threading.Thread(target=crawl_data, args=(pages_2,), daemon= True)
        crawl_1.start()
        crawl_2.start()
        crawl_1.join()
        crawl_2.join()
    except:
        print('Exit!')