#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scrapy
import os
import json
from codecs import open
from datetime import datetime
import re

URL = 'https://nytimes.com/'
NAME = 'New York Times'

# Hash table chưa tên chủ đề, để tạo thư mục
CATEGORIES = {
    'world': 'World',
    'us': 'U.S.',
    'politics': 'Politics',
    'business': 'Business',
    'technology': 'Tech',
    'science': 'Science',
    'health': 'Health',
    'sports': 'Sports',
    'books': 'Books',
    'food': 'Food',
    'travel': 'Travel'
}

CATEGORIES_COUNTER = {
    'world': [0, 0],
    'us': [0, 0],
    'politics': [0, 0],
    'business': [0, 0],
    'technology': [0, 0],
    'science': [0, 0],
    'health': [0, 0],
    'sports': [0, 0],
    'books': [0, 0],
    'food': [0, 0],
    'travel': [0, 0]
}

class NyTimes(scrapy.Spider):
    name = "nytimes"
    folder_path = "nytimes"
    page_limit = None
    start_urls = [
    ]

    def __init__(self, category=None, limit=None, *args, **kwargs):
        super(NyTimes, self).__init__(*args, **kwargs)
        if limit != None:
            self.page_limit = int(limit)
        # Tạo thư mục
        # if not os.path.exists(self.folder_path):
        #     os.mkdir(self.folder_path)

        if category in CATEGORIES:
            self.category = category
            # folders_path = self.folder_path + '/' + CATEGORIES[category]
            # if not os.path.exists(folders_path):
            #     os.makedirs(folders_path)
            self.start_urls = [URL + 'section/' + category]
        else:
            for CATEGORY in CATEGORIES:
                folders_path = self.folder_path + '/' + CATEGORIES[CATEGORY]
                if not os.path.exists(folders_path):
                    os.makedirs(folders_path)
                self.start_urls.append(URL + CATEGORY)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse_list_news)

    def parse_list_news(self, response):
        #category = self.get_category_from_url(response.url)
        category = self.category

        if self.page_limit is not None and (CATEGORIES_COUNTER[category][1] >= self.page_limit or self.page_limit <= 0):
            return

        # next_page_url = self.extract_next_page_url(response)
        # if len(next_page_url.split('/')) < 4:
        #     next_page_url = URL + next_page_url[1:]

        # Xử lý
        section = response.css("section.css-15h4p1b")
        for list_news in section.css("section#collection-highlights-container article"):
            relative_url = list_news.css('a::attr(href)').extract_first()
            abs_url = response.urljoin(URL + relative_url)
            yield scrapy.Request(abs_url, callback=self.parse_news)
        for list_news in section.css("section.ep7jkp60 article"):
            relative_url = list_news.css('a::attr(href)').extract_first()
            abs_url = response.urljoin(URL + relative_url)
            yield scrapy.Request(abs_url, callback=self.parse_news)
        for list_news in section.css("section#stream-panel li"):
            relative_url = list_news.css('a::attr(href)').extract_first()
            abs_url = response.urljoin(URL + relative_url)
            yield scrapy.Request(abs_url, callback=self.parse_news)
        
        # if category in CATEGORIES and next_page_url is not None:
        #     CATEGORIES_COUNTER[category][1] = CATEGORIES_COUNTER[category][1] + 1
        #     # Đệ qui để crawl trang kế tiếp
        #     yield scrapy.Request(response.urljoin(next_page_url), callback=self.parse_list_news)
        # else:
        #     return
        return


    def extract_next_page_url(self, response):
        section = response.css("div.container")
        # Lấy link trang kế tiếp
        # url = response.url
        next_page_url = section.css("div#pagination a.next-page::attr(href)").extract_first()

        return next_page_url

    def parse_news(self, response):

        jsonData = self.extract_news(response)

        yield jsonData

        # items = response.url.split('/')

        # # Write to file
        # if len(items) >=4  and items[3] in CATEGORIES:
        #     CATEGORIES_COUNTER[items[3]][0] = CATEGORIES_COUNTER[items[3]][0] + 1
        #     filename = '%s/%s-%s.json' % (CATEGORIES[items[3]], CATEGORIES[items[3]], CATEGORIES_COUNTER[items[3]][0])
        #     with open(self.folder_path + "/" + filename, 'wb', encoding = 'utf-8') as fp:
        #         json.dump(jsonData, fp, ensure_ascii= False, indent=4)
        #         self.log('Saved file %s' % filename)
    

    def get_category_from_url(self, url):
        items = url.split('/')
        category = None
        if len(items) >= 4:
            category = re.sub(r'-p[0-9]+', '', items[3])
        return category

    def extract_news(self, response):

        date = self.extract_date(response)
        title = self.extract_title(response)
        content = self.extract_content(response)
        # author = self.extract_author(response)
        description = self.extract_description(response)
        image = self.extract_image(response)

        jsonData = {
            'source': 'nytimes',
            'sourceName': NAME,
            'category': self.category,
            'date': date,
            'title': title,
            'link': response.url,
            'content': content,
            # 'author': author,
            'description': description,
            'image': image
        }

        return jsonData

    def extract_title(self, response):
        news = response.css("article#story")
        title = news.css("h1.css-rsa88z::text").extract_first()
        if title is None:
            title = news.css("h1::text").extract_first()
        return title

    def extract_description(self, response):
        news = response.css("article#story")
        description = news.css("p#article-summary::text").extract_first()
        return description

    def extract_content(self, response):
        news = response.css("article#story")
        content = news.css("section.meteredContent p.css-158dogj *::text").getall()
        
        return content

    def extract_date(self, response):
        news = response.css("article#story")
        date = news.css("time::text").extract_first()
        if date is None: 
            date = response.url[24:34]
            if date[:2] == 'es': date = response.url[27:37]
            try:
                _ = int(date[:4])
            except ValueError:
                date = None
        else:
            month = {
                'Jan.': '01',
                'Feb.': '02',
                'Mar.': '03',
                'Apr.': '04',
                'May.': '05',
                'Jun.': '06',
                'Jul.': '07',
                'Aug.': '08',
                'Sep.': '09',
                'Oct.': '10',
                'Nov.': '11',
                'Dec.': '12'
            }
            dd = date.split(' ')[1].replace(',','')
            if len(dd) == 1: dd = '0'+ dd
            mm = month[date.split(' ')[0]]
            yyyy = date.split(' ')[2].replace(',','')
            date = yyyy + '/' + mm + '/' + dd
        return date
    
    def extract_author(self, response):
        news = response.css("article#story")
        author = news.css("article p.Normal strong::text").extract_first()
        
        return author
    
    def extract_image(self, response):
        news = response.css("article#story")
        image = news.css("picture img::attr(src)").extract_first()
        
        return image