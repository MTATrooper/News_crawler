import os
from news_crawler.spiders.dantri import CATEGORIES as dantri_categories
from news_crawler.spiders.vnexpress import CATEGORIES as vnexpress_categories
import time
import threading

pages_1 = {'dantri': dantri_categories}
pages_2 = {'vnexpress': vnexpress_categories}

def crawl_data(pages):
    start = time.time()

    while True:
        for page in pages:
            os.makedirs('data/%s' % page)
            for category in pages[page]:
                os.system('scrapy crawl %s -a category=%s -a limit=1 -o data/%s/%s.json' % (page, category, page, category))
        
        while True:
            if int(time.time() - start) % 180 == 0:
                for page in pages:
                    os.system('rm -r data/%s'% page)
                break
if __name__ == '__main__':
    try:
        crawl_1 = threading.Thread(target=crawl_data, args=(pages_1,), daemon= True)
        crawl_2 = threading.Thread(target=crawl_data, args=(pages_2,), daemon= True)
        crawl_1.start()
        crawl_2.start()
        crawl_1.join()
        crawl_2.join()
    except:
        print('Exit!')