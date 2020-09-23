#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scrapy
import os
import json
from codecs import open
from datetime import datetime
import re

URL = 'https://vnexpress.net/'
NAME = 'VnExpress'

# Hash table chưa tên chủ đề, để tạo thư mục
CATEGORIES = {
    'giao-duc': 'Giáo dục',
    'suc-khoe': 'Sức khoẻ',
    'khoa-hoc': 'Khoa học',
    'so-hoa': ' Công nghệ',
    'giai-tri': 'Giải trí',
    'the-thao': 'Thể thao',
    'doi-song': 'Đời sống',
    'du-lich': 'Du lịch',
    'phap-luat': 'Pháp luật',
    'thoi-su': 'Thời sự',
    'kinh-doanh': 'Kinh doanh'
}

CATEGORIES_COUNTER = {
    'giao-duc': [0, 0],
    'suc-khoe': [0, 0],
    'khoa-hoc': [0, 0],
    'so-hoa': [0, 0],
    'giai-tri': [0, 0],
    'the-thao': [0, 0],
    'doi-song': [0, 0],
    'du-lich': [0, 0],
    'phap-luat': [0, 0],
    'thoi-su': [0, 0],
    'kinh-doanh': [0, 0]
}

class VnExpress(scrapy.Spider):
    '''Crawl tin tức từ https://vnexpress.net website
    ### Các tham số:
        category: Chủ đề để crawl, có thể bỏ trống. Các chủ đề
                 * giao-duc
                 * suc-khoe
                 * khoa-hoc
                 * so-hoa
                 * giai-tri
                 * the-thao
                 * doi-song
                 * du-lich
                 * phap-luat
                 * thoi-su
                 * kinh-doanh
        limit: Giới hạn số trang để crawl, có thể bỏ trống.
    '''
    name = "vnexpress"
    folder_path = "vnexpress"
    page_limit = None
    start_urls = [
    ]

    def __init__(self, category=None, limit=None, *args, **kwargs):
        super(VnExpress, self).__init__(*args, **kwargs)
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
            self.start_urls = [URL + category]
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

        next_page_url = self.extract_next_page_url(response)
        if len(next_page_url.split('/')) < 4:
            next_page_url = URL + next_page_url[1:]

        # Xử lý
        section = response.css("section.section")
        for list_news in section.css("article.item-news"):
            relative_url = list_news.css('h3 a::attr(href)').extract_first()
            if relative_url is None:
                relative_url = list_news.css('h1 a::attr(href)').extract_first()
            if relative_url is None:
                relative_url = list_news.css('h2 a::attr(href)').extract_first()
            abs_url = response.urljoin(relative_url)
            yield scrapy.Request(abs_url, callback=self.parse_news)
        for list_news in section.css("ul.list-sub-feature li"):
            relative_url = list_news.css('h3 a::attr(href)').extract_first()
            abs_url = response.urljoin(relative_url)
            yield scrapy.Request(abs_url, callback=self.parse_news)
        
        if category in CATEGORIES and next_page_url is not None:
            CATEGORIES_COUNTER[category][1] = CATEGORIES_COUNTER[category][1] + 1
            # Đệ qui để crawl trang kế tiếp
            yield scrapy.Request(response.urljoin(next_page_url), callback=self.parse_list_news)
        else:
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
            'source': 'vnexpress',
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
        news = response.css("section.section")
        title = news.css("h1.title-detail::text").extract_first()
        if title is None:
            title = news.css("h1::text").extract_first()
        return title

    def extract_description(self, response):
        news = response.css("section.section")
        description = news.css("p.description::text").extract_first()
        return description

    def extract_content(self, response):
        news = response.css("section.section")
        content = news.css("article p.Normal *::text").getall()
        
        return content

    def extract_date(self, response):
        news = response.css("section.section")
        date = news.css("div.header-content span::text").extract_first()
        if date is None:
            date = news.css("span::text").extract_first()
        if date is not None:
            date_split = date.split(',')
            date_split2 = date_split[1].strip().split('/')
            if len(date_split2[1]) == 1:
                date_split2[1] = '0'+date_split2[1]
            date = date_split2[2] + '/' + date_split2[1] + '/'+ date_split2[0] + ' ' + date_split[2].strip()[:5]
        return date
    
    def extract_author(self, response):
        news = response.css("section.section")
        author = news.css("article p.Normal strong::text").extract_first()
        
        return author
    
    def extract_image(self, response):
        news = response.css("section.section")
        image = news.css("article.fck_detail picture img::attr(data-src)").extract_first()
        
        return image