import os
import time
import threading
import requests
from utils import load_json
from pymongo import MongoClient
from nltk import sent_tokenize
from news_crawler.spiders.dantri import CATEGORIES as dantri_categories, URL as dantri_url
from news_crawler.spiders.vnexpress import CATEGORIES as vnexpress_categories, URL as vnexpress_url

pages = {'dantri': dantri_categories,
        'vnexpress': vnexpress_categories}
urls = {'dantri': dantri_url,
        'vnexpress': vnexpress_url}

DATA_DIR = './data'
client = MongoClient(port=27017)
db=client.newspaper

def insertDB(page):
    PAGE_DIR = os.path.join(DATA_DIR, page)
    for filename in os.listdir(PAGE_DIR):
        data = load_json(os.path.join(PAGE_DIR, filename))
        for news in data:
            find = db.news.find_one({'link': news['link']})     #tìm xem link đã xuất hiện trong CSDL chưa
            for row in news['content']:                         #Xóa tiêu đề ảnh lẫn trong bài viết
                if row[-1] != '.':
                    news['content'].remove(row)
            content = ' '.join(news['content'])
            sents = sent_tokenize(content)
            if len(sents) != 0 and len(sents[-1].strip()) <= 30:    #Bỏ tên tác giả khỏi nội dung bài viết
                sents.remove(sents[-1])
            if len(sents) >= 5 and news['title'] is not None and news['date'] is not None and find is None:
                news['content'] = sents
                content = ' '.join(sents)
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
                os.system('rm -r %s'% DATA_DIR)
                break
if __name__ == '__main__':
    try:
        for page in pages:
            sources = { 'name': page, 
                        'url': urls[page],
                        'category': pages[page]
                    }
            find = db.source.find_one({'name': page})
            if find is None:
                db.source.insert_one(sources)
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