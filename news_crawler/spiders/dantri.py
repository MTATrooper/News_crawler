#!/usr/bin/env python
# -*- coding: utf-8 -*-

import scrapy
import os
import json
from codecs import open
from datetime import datetime
import re

URL = 'https://dantri.com.vn'

# Hash table chưa tên chủ đề, để tạo thư mục
CATEGORIES = {
    'giao-duc-khuyen-hoc': 'Giáo dục',
    'suc-khoe': 'Sức khoẻ',
    'khoa-hoc-cong-nghe': 'Khoa học',
    'giai-tri': 'Giải trí',
    'the-thao': 'Thể thao',
    'the-gioi': 'Thế giới',
    'du-lich': 'Du lịch',
    'phap-luat': 'Pháp luật',
    'su-kien': 'Thời sự',
    'kinh-doanh': 'Kinh doanh',
    'xa-hoi': 'Xã hội'
}

CATEGORIES_COUNTER = {
    'giao-duc-khuyen-hoc': [0, 0],
    'suc-khoe': [0, 0],
    'khoa-hoc-cong-nghe': [0, 0],
    'giai-tri': [0, 0],
    'the-thao': [0, 0],
    'the-gioi': [0, 0],
    'du-lich': [0, 0],
    'phap-luat': [0, 0],
    'su-kien': [0, 0],
    'kinh-doanh': [0, 0],
    'xa-hoi': [0, 0]
}

class Dantri(scrapy.Spider):
    '''Crawl tin tức từ https://dantri.com.vn website
    ### Các tham số:
        category: Chủ đề để crawl, có thể bỏ trống. Các chủ đề
                 * giao-duc-khuyen-hoc
                 * suc-khoe
                 * khoa-hoc-cong-nghe
                 * giai-tri
                 * the-thao
                 * the-gioi
                 * du-lich
                 * phap-luat
                 * su-kien
                 * kinh-doanh
                 * xa-hoi
        limit: Giới hạn số trang để crawl, có thể bỏ trống.
    '''
    name = "dantri"
    folder_path = "dantri"
    page_limit = None
    start_urls = [
    ]

    def __init__(self, category=None, limit=None, *args, **kwargs):
        super(Dantri, self).__init__(*args, **kwargs)
        if limit != None:
            self.page_limit = int(limit)

        if category in CATEGORIES:
            self.category = category
            self.start_urls = ['%s/%s.htm' % (URL, category)]
        else:
            for CATEGORY in CATEGORIES:
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
            next_page_url = URL + next_page_url

        # Xử lý
        # section = response.css("section.section")
        for list_news in response.css("div.news-item"):
            relative_url = list_news.css('h3 a::attr(href)').extract_first()
            abs_url = response.urljoin('%s%s' % (URL, relative_url))
            yield scrapy.Request(abs_url, callback=self.parse_news)
        for list_news in response.css("li.news-item"):
            relative_url = list_news.css('h3 a::attr(href)').extract_first()
            abs_url = response.urljoin('%s%s' % (URL, relative_url))
            yield scrapy.Request(abs_url, callback=self.parse_news)
        
        if category in CATEGORIES and next_page_url is not None:
            CATEGORIES_COUNTER[category][1] = CATEGORIES_COUNTER[category][1] + 1
            # Đệ qui để crawl trang kế tiếp
            yield scrapy.Request(response.urljoin(next_page_url), callback=self.parse_list_news)
        else:
            return


    def extract_next_page_url(self, response):
        section = response.css("ul.list-unstyled.dt-category-actions")
        # Lấy link trang kế tiếp
        # url = response.url
        next_page_url = section.css("li a.text-primary::attr(href)").extract()[-1]

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
            'source': self.name,
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
        news = response.css("article.dt-news__detail")
        title = news.css("h1.dt-news__title::text").extract_first()
        if title is None:
            title = response.css("div.dt-news__content span strong::text").extract_first()
        return title.strip() if title is not None else title

    def extract_description(self, response):
        news = response.css("article.dt-news__detail")
        description = news.css("div.dt-news__body div.dt-news__sapo h2::text").extract_first()
        if description is None:
            description = response.css("div.dt-news__content p strong em::text").extract_first()
        return description

    def extract_content(self, response):
        news = response.css("article.dt-news__detail")
        content = news.css("div.dt-news__body div.dt-news__content p *::text").extract()
        if content is None:
            content = response.css("div.dt-news__body div.dt-news__content p *::text").extract()
        return content

    def extract_date(self, response):
        news = response.css("article.dt-news__detail")
        date = news.css("div.dt-news__header div.dt-news__meta span::text").extract_first()
        if date is None:
            date = news.css("span::text").extract_first()
        if date is not None:
            date = date.split(',')[1].strip().replace(' ','')
        return date
    
    def extract_author(self, response):
        news = response.css("section.section")
        author = news.css("article p.Normal strong::text").extract_first()
        
        return author
    
    def extract_image(self, response):
        news = response.css("article.dt-news__detail")
        image = news.css("div.dt-news__body div.dt-news__content figure img::attr(src)").extract_first()
        if image is None:
            image = response.css("div.dt-news__content figure img::attr(src)").extract_first()
        return image